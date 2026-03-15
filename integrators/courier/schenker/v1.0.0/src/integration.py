"""Schenker Courier Integration — migrated from meriship codebase.

Handles all Schenker SOAP API interactions including:
- Order creation (createOrder)
- Order cancellation (cancelOrder)
- Order status (getOrderStatus + getTracking for realization + tracking events)
- Document/label retrieval (getDocuments)
- SSCC support, reference types, COD, extra services

Uses HTTP Basic Auth for SOAP authentication.
"""

from __future__ import annotations

import base64
import contextlib
import io
import json
import logging
import zipfile
from datetime import datetime
from enum import Enum
from http import HTTPStatus

from requests import Session
from requests.auth import HTTPBasicAuth
from zeep import Client, Transport
from zeep.exceptions import Fault, TransportError
from zeep.helpers import serialize_object

from src.config import settings
from src.schemas import (
    CreateShipmentRequest,
    SchenkerCredentials,
    ShipmentParty,
)

logger = logging.getLogger("courier-schenker")

DELETE_ORDER_SCHEMA: dict = {
    "message": "",
    "status": "",
}


def wsdl_to_json(data: object) -> dict:
    """Convert a zeep SOAP response object to a JSON-serializable dict."""
    return json.loads(json.dumps(serialize_object(data)))


class SchenkerIntegration:
    """Schenker SOAP integration with HTTP Basic Auth."""

    TRACKING_URL = "https://www.dbschenker.com/app/tracking-public/?refNumber={tracking_number}"

    class ReferenceType(Enum):
        """Reference types for order identification.

        For getOrderStatus only DWB and COR are valid.
        """

        DOMESTIC_WAYBILL = "DWB"
        CLIENT_ORDER = "COR"
        PACKAGE_ID = "PKG"
        SHIPPER = "SHP"
        CONSIGNEE = "CGN"
        FREIGHT_FORWARDER = "FF"

    class OrderStatus(Enum):
        """Realization statuses — pre-pickup actions."""

        CANCELLED = -2
        REFUSED = -1
        AWAITING_ACCEPTANCE = 0
        ACCEPTED = 1
        IN_REALIZATION = 2
        REALIZED = 3

    class ParcelEvents(Enum):
        """Tracking events — post-pickup / delivery."""

        BOOKED = "ENT"
        COLLECTED = "COL"
        DELIVERED_TO_TERMINAL_BY_SHIPPER = "DET"
        DEPARTED = "MAN"
        ARRIVED = "ENM"
        CUSTOMS_CLEARANCE_INITIATED = "CCL"
        CUSTOMS_CLEARANCE_FINALIZED = "CCF"
        AWAITING_PICKUP = "DIS"
        PICKED_UP = "PUP"
        OUT_FOR_DELIVERY = "DOT"
        DELIVERED = "DLV"
        TERMINAL_INVENTORY = "TIN"
        NOT_DELIVERED = "NDL"
        EPOD_AVAILABLE = "POD"

    def __init__(self) -> None:
        self.client: Client | None = None

    # ------------------------------------------------------------------
    # Order status (combines realization + tracking)
    # ------------------------------------------------------------------

    def get_order_status(
        self,
        credentials: SchenkerCredentials,
        waybill_number: str,
    ) -> tuple[str | int, int]:
        """Get order status: first checks realization, then tracking events if realized."""
        login, password = credentials.login, credentials.password
        if self._are_credentials_different(login, password):
            self._create_soap_client(login, password)

        status, order_status = self._get_order_status(credentials, waybill_number)

        if order_status != HTTPStatus.OK:
            return status, order_status

        if status != self.OrderStatus.REALIZED.value:
            return status, order_status

        return self._get_last_tracking_event(waybill_number)

    # ------------------------------------------------------------------
    # Tracking info
    # ------------------------------------------------------------------

    def get_tracking_info(
        self,
        waybill_number: str,
    ) -> tuple[dict, int]:
        """Return tracking URL — no API call needed."""
        return {
            "tracking_number": waybill_number,
            "tracking_url": self.TRACKING_URL.format(tracking_number=waybill_number),
        }, HTTPStatus.OK

    # ------------------------------------------------------------------
    # Create order
    # ------------------------------------------------------------------

    def create_order(
        self,
        credentials: SchenkerCredentials,
        command: CreateShipmentRequest,
    ) -> tuple[object, int]:
        """Create transport order via SOAP createOrder."""
        login, password = credentials.login, credentials.password
        shipper, receiver, parcels = command.shipper, command.receiver, command.parcels
        schenker_extras = command.extras.get("schenker", {})
        client_id = credentials.credentials_id

        try:
            if self._are_credentials_different(login, password):
                self._create_soap_client(login, password)

            response = self.client.service.createOrder(
                clientId=client_id,
                installId=schenker_extras.get("install_id"),
                dataOrigin=schenker_extras.get("data_origin"),
                waybillNo=schenker_extras.get("waybill_no"),
                product=command.service_name,
                pickupFrom=self._get_date_time(schenker_extras.get("pickup_from")),
                pickupTo=self._get_date_time(schenker_extras.get("pickup_to")),
                deliveryFrom=self._get_date_time(schenker_extras.get("delivery_from")),
                deliveryTo=self._get_date_time(schenker_extras.get("delivery_to")),
                comment=schenker_extras.get("comment"),
                deliveryInstructions=schenker_extras.get("delivery_instructions"),
                sender=self._get_shipment_party_info(shipper, client_id, schenker_extras, credentials.login_ext),
                recipient=self._get_shipment_party_info(receiver, None, schenker_extras, receiver.tax_number),
                payer=self._get_shipment_party_info(shipper, client_id, schenker_extras, credentials.login_ext)
                if command.payment.payer_type == "SHIPPER"
                else self._get_shipment_party_info(receiver, receiver.client_id, schenker_extras, receiver.tax_number),
                packages=[
                    {
                        "colli": {
                            "colliId": schenker_extras.get("colli_id"),
                            "name": command.content,
                            "packCode": parcel.parcel_type,
                            "quantity": parcel.quantity,
                            "protection": schenker_extras.get("protection"),
                            "weight": parcel.weight * 100,
                            "volume": ((parcel.width * parcel.length * parcel.height) / 1_000_000) * 100,
                            "width": parcel.width,
                            "length": parcel.length,
                            "height": parcel.height,
                            "stack": schenker_extras.get("stack"),
                        },
                    }
                    for parcel in parcels
                ],
                ssccMatching=("sscc" in schenker_extras),
                sscc=[
                    {
                        "sscc": {
                            "colliId": sc.get("colli_id"),
                            "ssccNo": sc.get("sscc_no"),
                        },
                    }
                    for sc in schenker_extras.get("sscc")
                ]
                if "sscc" in schenker_extras
                else None,
                adrs=None,
                services=self._get_services(command),
                references=None,
            )

        except TransportError as e:
            return e.content, e.status_code
        except Fault as e:
            return (
                e.detail.find(
                    ".//ns2:transportOrderFaultList/transportOrderFaultRow/errorMessage",
                    namespaces={"ns2": "http://api.schenker.pl/TransportOrders/"},
                ).text,
                HTTPStatus.BAD_REQUEST,
            )

        if response is None:
            return None, HTTPStatus.NO_CONTENT

        status_code = HTTPStatus.OK if response["statusCode"] == "OK" else HTTPStatus.BAD_REQUEST
        json_order = wsdl_to_json(response)

        if status_code == HTTPStatus.BAD_REQUEST:
            return json_order, status_code

        waybill_number = json_order.get("orderId")
        tracking_info, tracking_status_code = self.get_tracking_info(waybill_number)
        if tracking_status_code == HTTPStatus.OK:
            json_order["tracking"] = tracking_info
        json_order["tracking_number"] = waybill_number

        return self._normalize_order_item(command, json_order), status_code

    # ------------------------------------------------------------------
    # Cancel order
    # ------------------------------------------------------------------

    def delete_order(
        self,
        credentials: SchenkerCredentials,
        waybill_number: str,
    ) -> tuple[object, int]:
        """Cancel order via SOAP cancelOrder."""
        login, password = credentials.login, credentials.password
        try:
            if self._are_credentials_different(login, password):
                self._create_soap_client(login, password)

            response = self.client.service.cancelOrder(
                clientId=credentials.credentials_id,
                orderId=waybill_number,
            )

        except TransportError as e:
            return e.content, e.status_code
        except Fault as e:
            return e.message, HTTPStatus.NOT_FOUND

        if response is None:
            return None, HTTPStatus.NO_CONTENT

        endpoint_response = DELETE_ORDER_SCHEMA.copy()
        status_code = HTTPStatus.OK if not response["iError"] else HTTPStatus.BAD_REQUEST

        if status_code == HTTPStatus.OK:
            endpoint_response["message"] = "Zamówienie zostało anulowane."
            return endpoint_response, status_code

        return f"{response['iError']}: {response['cError']}", status_code

    # ------------------------------------------------------------------
    # Labels / documents
    # ------------------------------------------------------------------

    def get_waybill_label_bytes(
        self,
        credentials: SchenkerCredentials,
        waybill_numbers: list[str],
        args: dict,
    ) -> tuple[bytes | str, int]:
        """Get first label as raw bytes."""
        labels, status_code = self.get_labels(credentials, waybill_numbers, args)

        if status_code == HTTPStatus.OK:
            return labels[0], status_code

        return labels, status_code

    def get_waybill_label(
        self,
        credentials: SchenkerCredentials,
        waybill_numbers: list[str],
        args: dict,
    ) -> tuple[bytes | str, int]:
        """Return label bytes — single PDF or ZIP for multiple waybills."""
        if len(waybill_numbers) > 1:
            labels, status_code = self.get_labels(credentials, waybill_numbers, args)
            if status_code == HTTPStatus.OK:
                return self._zip_labels(labels, waybill_numbers), status_code
            return labels, status_code

        return self.get_waybill_label_bytes(credentials, waybill_numbers, args)

    def get_labels(
        self,
        credentials: SchenkerCredentials,
        waybill_numbers: list[str],
        _data: dict,
    ) -> tuple[list | str, int]:
        """Retrieve documents via SOAP getDocuments for each waybill."""
        login, password = credentials.login, credentials.password
        try:
            if self._are_credentials_different(login, password):
                self._create_soap_client(login, password)

            response = [
                self.client.service.getDocuments(
                    clientId=credentials.credentials_id,
                    referenceType="DWB",
                    referenceNumber=waybill_number,
                    type="LP",
                )
                for waybill_number in waybill_numbers
            ]

        except TransportError as e:
            return e.content, e.status_code
        except Fault as e:
            return e.message, HTTPStatus.NOT_FOUND

        status_code = HTTPStatus.OK if response else HTTPStatus.BAD_REQUEST

        if status_code == HTTPStatus.BAD_REQUEST:
            return "Pobieranie dokumentu przewozowego nie powiodło się.", status_code

        return response, status_code

    # ------------------------------------------------------------------
    # Private — SOAP client management
    # ------------------------------------------------------------------

    def _create_soap_client(self, login: str, password: str) -> None:
        """Create HTTP Basic Auth SOAP client."""
        try:
            session = Session()
            session.auth = HTTPBasicAuth(login, password)
            transport = Transport(
                session=session,
                timeout=settings.soap_timeout,
                operation_timeout=settings.soap_operation_timeout,
            )
            self.client = Client(
                wsdl=settings.schenker_transport_api_url,
                transport=transport,
            )
            logger.info("SOAP client connected — %s", settings.schenker_transport_api_url)
        except ConnectionError:
            logger.error("SOAP client timeout — %s", settings.schenker_transport_api_url)
        except Exception:
            logger.exception("SOAP client init failed — %s", settings.schenker_transport_api_url)

    def _are_credentials_different(self, login: str, password: str) -> bool:
        if hasattr(self, "client") and self.client is not None:
            auth = self.client.transport.session.auth
            if auth and auth.username == login and auth.password == password:
                return False
        return True

    # ------------------------------------------------------------------
    # Private — order status helpers
    # ------------------------------------------------------------------

    def _get_order_status(
        self,
        credentials: SchenkerCredentials,
        waybill_number: str,
    ) -> tuple[str | int, int]:
        """Check realization progress via getOrderStatus."""
        try:
            response = self.client.service.getOrderStatus(
                clientId=credentials.credentials_id,
                pcReference_type=self.ReferenceType.DOMESTIC_WAYBILL.value,
                pcReference_number=waybill_number,
            )

        except TransportError as e:
            return e.content, e.status_code
        except Fault as e:
            return e.message, HTTPStatus.BAD_REQUEST

        status_code = HTTPStatus.OK if not response["piError"] else HTTPStatus.BAD_REQUEST
        if status_code == HTTPStatus.OK:
            return response["pcOpis"], status_code
        return response["pcError"], status_code

    def _get_last_tracking_event(
        self,
        waybill_number: str,
    ) -> tuple[str, int]:
        """Get last tracking event via getTracking (post-pickup events)."""
        try:
            response = self.client.service.getTracking(
                referenceType=self.ReferenceType.DOMESTIC_WAYBILL.value,
                referenceNumber=waybill_number,
            )
        except TransportError as e:
            return e.content, e.status_code
        except Fault as e:
            return e.message, HTTPStatus.BAD_REQUEST

        with contextlib.suppress(KeyError):
            events = response["consigment"]["eventList"]
            if events is not None:
                return events[0]["eventCode"], HTTPStatus.OK

        return "Order was not found!", HTTPStatus.NOT_FOUND

    # ------------------------------------------------------------------
    # Private — shipment party builder
    # ------------------------------------------------------------------

    @staticmethod
    def _get_shipment_party_info(
        shipment_party: ShipmentParty,
        client_id: str | None,
        extras: dict,
        tax_number: str | None,
    ) -> dict:
        return {
            "clientId": client_id,
            "clientIln": extras.get("client_iln"),
            "name1": f"{shipment_party.first_name} {shipment_party.last_name}",
            "name2": extras.get("name2"),
            "postCode": shipment_party.postal_code.replace("-", ""),
            "city": shipment_party.city,
            "street": shipment_party.street,
            "phone": shipment_party.phone,
            "nip": tax_number,
            "contactPerson": shipment_party.contact_person,
            "email": shipment_party.email,
            "paletteId": extras.get("palette_id"),
        }

    # ------------------------------------------------------------------
    # Private — services builder (COD, extra services)
    # ------------------------------------------------------------------

    @staticmethod
    def _get_services(command: CreateShipmentRequest) -> list:
        schenker_extras = command.extras.get("schenker", {})
        services: list = []

        if schenker_extras.get("services"):
            for service in schenker_extras["services"]:
                services.append(
                    {
                        "service": {
                            "code": service.get("code"),
                            "parameter1": service.get("parameter1"),
                            "parameter2": service.get("parameter2"),
                            "parameter3": service.get("parameter3"),
                        },
                    },
                )

        if command.cod:
            services.append(
                {
                    "service": {
                        "code": 9,
                        "parameter1": int(command.cod_value * 100),
                    },
                },
            )

        if schenker_extras.get("bringing_pack", False):
            services.append({"service": {"code": 1}})

        return services

    # ------------------------------------------------------------------
    # Private — normalisation
    # ------------------------------------------------------------------

    def _normalize_order_item(
        self,
        command: CreateShipmentRequest,
        order: dict,
    ) -> dict:
        normalized = {
            "id": order["orderId"],
            "waybill_number": order["tracking_number"],
            "shipper": self._normalize_shipment_party(command.shipper),
            "receiver": self._normalize_shipment_party(command.receiver),
            "orderStatus": order["statusCode"],
            "tracking": order["tracking"],
            "extras": {"schenker": order},
        }
        return normalized

    @staticmethod
    def _normalize_shipment_party(party: ShipmentParty) -> dict:
        return {
            "first_name": party.first_name,
            "last_name": party.last_name,
            "contact_person": party.contact_person,
            "phone": party.phone,
            "email": party.email,
            "address": {
                "building_number": party.building_number,
                "city": party.city,
                "country_code": party.country_code,
                "line1": f"{party.street} {party.building_number}",
                "line2": f"{party.postal_code} {party.city} {party.country_code}",
                "post_code": party.postal_code,
                "street": party.street,
            },
        }

    # ------------------------------------------------------------------
    # Private — misc helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_date_time(date_time: str | None) -> str | None:
        if not date_time:
            return None
        dt = datetime.strptime(date_time, "%Y-%m-%d %H:%M:%S")
        return dt.isoformat("T")

    @staticmethod
    def _zip_labels(labels: list, waybill_numbers: list[str]) -> bytes:
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED, False) as z:
            for label, waybill_number in zip(labels, waybill_numbers, strict=True):
                z.writestr(
                    f"{waybill_number}.pdf",
                    base64.b64decode(label),
                )
        return output.getvalue()
