"""DHL Courier Integration — migrated from meriship codebase.

Handles all DHL SOAP API interactions including:
- Shipment creation (DHL24 and Parcelshop)
- Label retrieval
- Shipment status tracking
- Order management
- Service point lookup
"""

from __future__ import annotations

import base64
import io
import json
import logging
import mimetypes
import zipfile
from datetime import date, timedelta
from http import HTTPStatus

from zeep import Client, Transport
from zeep.exceptions import Fault, TransportError
from zeep.helpers import serialize_object

from src.config import settings
from src.schemas import DhlCredentials

logger = logging.getLogger("courier-dhl")


# ---------------------------------------------------------------------------
# Utility helpers (ported from app.integrations.utils)
# ---------------------------------------------------------------------------


def wsdl_to_json(data: object) -> dict:
    """Convert a zeep SOAP response object to a JSON-serializable dict."""
    return json.loads(json.dumps(serialize_object(data)))


def format_postcode(postcode: str) -> str:
    """Format postcode to AB-CDE pattern if missing separator."""
    if len(postcode) > 5 and "-" not in postcode:
        return f"{postcode[:2]}-{postcode[2:]}"
    return postcode


def get_extras(data: dict, namespace: str | None = None) -> dict:
    """Extract the ``extras`` sub-dict, optionally narrowed to *namespace*."""
    if "extras" not in data:
        return {}
    obj = data["extras"]
    if isinstance(obj, str):
        obj = json.loads(obj)
    if not isinstance(obj, dict):
        raise ValueError('extras must be a JSON object, e.g. {"dhl": {...}}')
    if namespace:
        obj = obj.get(namespace, {})
        if not isinstance(obj, dict):
            raise ValueError(f"extras.{namespace} must be a dict")
    return obj


# ---------------------------------------------------------------------------
# Normalised point schema (ported from app.integrations.schema_templates)
# ---------------------------------------------------------------------------

GET_POINT_SCHEMA: dict = {
    "type": "",
    "name": "",
    "address": {
        "line1": "",
        "line2": "",
        "state_code": "",
        "postal_code": "",
        "country_code": "",
        "city": "",
        "longitude": "",
        "latitude": "",
    },
    "image_url": "",
    "open_hours": "",
    "option_cod": False,
    "option_send": True,
    "option_deliver": False,
    "additional_info": "",
    "distance": 0,
    "foreign_address_id": "",
}


# ---------------------------------------------------------------------------
# DHL Integration
# ---------------------------------------------------------------------------


class DhlIntegration:
    """DHL SOAP integration for both DHL24 and DHL ServicePoint (Parcelshop) APIs."""

    TRACKING_URL = "https://www.dhl.com/pl-en/home/tracking/tracking-parcel.html?submit=1&tracking-id={tracking_number}"
    DEFAULT_COD_FORM = "BANK_TRANSFER"

    def __init__(self) -> None:
        transport = Transport(
            timeout=settings.soap_timeout,
            operation_timeout=settings.soap_operation_timeout,
        )
        self.client: Client | None = None
        self.client_ps: Client | None = None

        try:
            self.client = Client(settings.wsdl_url, transport=transport)
            logger.info("SOAP client connected — %s", settings.wsdl_url)
        except ConnectionError:
            logger.error("SOAP client timeout — %s", settings.wsdl_url)
        except (TransportError, Fault, OSError) as exc:
            logger.exception("SOAP client init failed — %s: %s", settings.wsdl_url, exc)

        try:
            self.client_ps = Client(settings.parcelshop_url, transport=transport)
            logger.info("SOAP ServicePoint client connected — %s", settings.parcelshop_url)
        except ConnectionError:
            logger.error("SOAP ServicePoint client timeout — %s", settings.parcelshop_url)
        except (TransportError, Fault, OSError) as exc:
            logger.exception("SOAP ServicePoint client init failed — %s: %s", settings.parcelshop_url, exc)

    # ------------------------------------------------------------------
    # Order status
    # ------------------------------------------------------------------

    def get_order_status(
        self,
        credentials: DhlCredentials,
        waybill_number: str,
    ) -> tuple[str | None, int]:
        """Retrieve the latest shipment status via ``getTrackAndTraceInfo``."""
        try:
            response = self.client.service.getTrackAndTraceInfo(
                authData=self._get_auth_data(credentials),
                shipmentId=waybill_number,
            )
        except TransportError as exc:
            logger.error("DHL SOAP transport error: %s", str(exc.content)[:200])
            return {"error": "DHL API communication error"}, exc.status_code
        except Fault as exc:
            logger.error("DHL SOAP fault: %s", str(exc.message)[:200])
            return {"error": "DHL API request failed"}, HTTPStatus.NOT_FOUND

        if response is None:
            return None, HTTPStatus.NO_CONTENT

        try:
            if response.events:
                latest = sorted(
                    response.events.item,
                    key=lambda e: e.timestamp,
                    reverse=True,
                )[0]
                return latest.status, HTTPStatus.OK

            order, status_code = self.get_order(credentials, waybill_number, {})
            if status_code == HTTPStatus.OK:
                return order["orderStatus"], HTTPStatus.OK
            return order, status_code
        except (AttributeError, TypeError, IndexError, KeyError):
            return None, HTTPStatus.NO_CONTENT

    # ------------------------------------------------------------------
    # Tracking info
    # ------------------------------------------------------------------

    def get_tracking_info(
        self,
        waybill_number: str,
    ) -> tuple[dict, int]:
        """Return tracking URL for a given waybill — no API call required."""
        return {
            "tracking_number": waybill_number,
            "tracking_url": self.TRACKING_URL.format(tracking_number=waybill_number),
        }, HTTPStatus.OK

    # ------------------------------------------------------------------
    # Create shipment
    # ------------------------------------------------------------------

    def create_order(
        self,
        credentials: DhlCredentials,
        command: dict,
    ) -> tuple[dict | str, int]:
        """Create a DHL shipment.

        For parcelshop shipments (when ``extras.dhlps.custom_attributes.target_point``
        is present), uses the ServicePoint API. Otherwise uses the standard DHL24 API,
        optionally followed by a ``bookCourier`` call.
        """
        resp, status_code = self._create_order(credentials, command)
        if status_code != HTTPStatus.OK:
            return resp, status_code

        target_point = self._get_target_point_from_extras(
            command.get("extras", {}).get("dhlps", {}),
        )
        if target_point:
            return (
                self._normalize_order_item_parcelshop(credentials, command, resp),
                HTTPStatus.CREATED,
            )

        extras_dhl: dict = get_extras(command, "dhl")
        extras_dhl["shipment_id"] = resp["shipmentId"]

        if not extras_dhl.get("book_courier", True):
            get_order_response, sc = self.get_order(
                credentials,
                extras_dhl["shipment_id"],
                {},
            )
            if sc == HTTPStatus.OK:
                get_order_response.setdefault("extras", {}).setdefault("dhl", {})
                get_order_response["extras"]["dhl"]["shipment_id"] = extras_dhl["shipment_id"]
                return self._normalize_order_item(command, get_order_response), HTTPStatus.CREATED
            return get_order_response, sc

        return self._buy_offer(credentials, command)

    # ------------------------------------------------------------------
    # Delete shipment
    # ------------------------------------------------------------------

    def delete_order(
        self,
        credentials: DhlCredentials,
        waybill_number: str,
        data: dict,
    ) -> tuple[object, int]:
        """Cancel / delete a DHL shipment via ``deleteShipments``."""
        try:
            offer_id = get_extras(data, "dhl").get("offer_id", "")
            response = self.client.service.deleteShipments(
                authData=self._get_auth_data(credentials),
                shipment={
                    "shipmentIdentificationNumber": waybill_number,
                    "dispatchIdentificationNumber": offer_id,
                },
            )
        except TransportError as exc:
            logger.error("DHL SOAP transport error: %s", str(exc.content)[:200])
            return {"error": "DHL API communication error"}, exc.status_code
        except Fault as exc:
            logger.error("DHL SOAP fault: %s", str(exc.message)[:200])
            return {"error": "DHL API request failed"}, HTTPStatus.NOT_FOUND

        if response is None:
            return "Brak danych", HTTPStatus.NO_CONTENT
        if response["result"]:
            return wsdl_to_json(response), HTTPStatus.OK
        return wsdl_to_json(response), HTTPStatus.BAD_REQUEST

    # ------------------------------------------------------------------
    # Labels
    # ------------------------------------------------------------------

    def get_waybill_label(
        self,
        credentials: DhlCredentials,
        waybill_numbers: list[str],
        data: dict,
    ) -> tuple[bytes, int]:
        """Return label bytes — PDF for single waybill, ZIP for multiple."""
        if len(waybill_numbers) > 1:
            labels, status_code = self.get_labels(credentials, waybill_numbers, data)
            if status_code == HTTPStatus.OK:
                return self._zip_labels(labels), status_code
            return labels, status_code

        label_bytes, status_code = self.get_waybill_label_bytes(
            credentials,
            waybill_numbers,
            data,
        )
        return label_bytes, status_code

    def get_waybill_label_bytes(
        self,
        credentials: DhlCredentials,
        waybill_numbers: list[str],
        data: dict,
    ) -> tuple[bytes, int]:
        """Return raw PDF bytes for the first label in the list."""
        labels, status_code = self.get_labels(credentials, waybill_numbers, data)
        if status_code == HTTPStatus.OK:
            return base64.b64decode(labels[0]["labelData"]), status_code
        return labels, status_code

    def get_labels(
        self,
        credentials: DhlCredentials,
        waybill_numbers: list[str],
        _data: dict,
    ) -> tuple[list | str, int]:
        """Retrieve label data for one or more waybills via ``getLabels``."""
        try:
            response = self.client.service.getLabels(
                authData=self._get_auth_data(credentials),
                itemsToPrint={
                    "item": [{"labelType": "BLP", "shipmentId": wbn} for wbn in waybill_numbers],
                },
            )
        except TransportError as exc:
            logger.error("DHL SOAP transport error: %s", str(exc.content)[:200])
            return {"error": "DHL API communication error"}, exc.status_code
        except Fault as exc:
            logger.error("DHL SOAP fault: %s", str(exc.message)[:200])
            return {"error": "DHL API request failed"}, HTTPStatus.NOT_FOUND

        if response is None:
            return "Brak danych", HTTPStatus.OK

        status_code = (
            HTTPStatus.OK
            if not hasattr(response, "code")
            else (HTTPStatus.UNAUTHORIZED if response.code == "100" else HTTPStatus.BAD_REQUEST)
        )
        if status_code == HTTPStatus.OK:
            return wsdl_to_json(response), status_code
        return [response.message], status_code

    # ------------------------------------------------------------------
    # Get order details
    # ------------------------------------------------------------------

    def get_order(
        self,
        credentials: DhlCredentials,
        waybill_number: str,
        data: dict,
    ) -> tuple[dict | str, int]:
        """Retrieve order details by scanning ``getMyShipments`` results.

        The DHL API has no direct lookup by waybill — we must paginate through
        recent shipments within a date window (max 90 days).
        """
        created_from, created_to = self._retrieve_time_range(data)
        orders: list = []

        try:
            count = self.client.service.getMyShipmentsCount(
                authData=self._get_auth_data(credentials),
                createdFrom=date.today() - timedelta(days=2),
                createdTo=date.today(),
            )
            count = count if count else 100
            offset = 0
            while count > offset:
                response = self.client.service.getMyShipments(
                    authData=self._get_auth_data(credentials),
                    createdFrom=created_from,
                    createdTo=created_to,
                    offset=offset,
                )
                if response is None:
                    return "Brak danych", HTTPStatus.OK
                orders.extend(response)
                offset += 100
        except TransportError as exc:
            logger.error("DHL SOAP transport error: %s", str(exc.content)[:200])
            return {"error": "DHL API communication error"}, exc.status_code
        except Fault as exc:
            logger.error("DHL SOAP fault: %s", str(exc.message)[:200])
            return {"error": "DHL API request failed"}, HTTPStatus.NOT_FOUND

        if not orders:
            return (
                f"Zamówienie nie istnieje w podanym okresie czasowym {created_from} - {created_to}",
                HTTPStatus.NOT_FOUND,
            )

        found = [o for o in orders if o.shipmentId == waybill_number]
        if not found:
            return (
                f"Nie znaleziono zamówienia o identyfikatorze {waybill_number}",
                HTTPStatus.NOT_FOUND,
            )

        json_order = wsdl_to_json(found[0])
        json_order["tracking_number"] = waybill_number
        json_order["extras"] = {"dhl": {}}
        json_order["tracking"] = {
            "tracking_number": waybill_number,
            "tracking_url": self.TRACKING_URL.format(tracking_number=waybill_number),
        }
        return json_order, HTTPStatus.OK

    # ------------------------------------------------------------------
    # Service points
    # ------------------------------------------------------------------

    def get_points(
        self,
        credentials: DhlCredentials,
        data: dict,
    ) -> tuple[object, int]:
        """Find nearest DHL service-points via SOAP ``getNearestServicepoints``."""
        extras = get_extras(data, "dhl")
        parcelshop_api = bool(extras.get("parcelshop"))
        cod = extras.get("cod", False)

        try:
            if parcelshop_api:
                structure = {
                    "authData": self._get_auth_data(credentials),
                    "postcode": data.get("postcode", "00001").replace("-", ""),
                    "radius": extras.get("radius", 500),
                }
            else:
                structure = {
                    "country": extras.get("country", "PL"),
                    "postcode": data.get("postcode", "00001").replace("-", ""),
                    "radius": extras.get("radius", 500),
                }

            if "city" in data:
                structure["city"] = data["city"]

            if parcelshop_api:
                if cod:
                    response = self.client_ps.service.getNearestServicepointsCOD(
                        structure=structure,
                    )
                else:
                    response = self.client_ps.service.getNearestServicepoints(
                        structure=structure,
                    )
            else:
                    response = self.client.service.getNearestServicepoints(
                    authData=self._get_auth_data(credentials),
                    structure=structure,
                )
        except TransportError as exc:
            logger.error("DHL SOAP transport error: %s", str(exc.content)[:200])
            return {"error": "DHL API communication error"}, exc.status_code
        except Fault as exc:
            logger.error("DHL SOAP fault: %s", str(exc.message)[:200])
            return {"error": "DHL API request failed"}, HTTPStatus.NOT_FOUND

        if response is None:
            return "Brak danych", HTTPStatus.OK

        status_code = (
            HTTPStatus.OK
            if not hasattr(response, "code")
            else (HTTPStatus.UNAUTHORIZED if response.code == "100" else HTTPStatus.BAD_REQUEST)
        )

        if status_code != HTTPStatus.OK:
            logger.error("DHL SOAP error in get_points: %s", str(response.message)[:200])
            return {"error": "DHL API request failed"}, status_code

        points: dict = {}
        resp_json = wsdl_to_json(response)
        items = resp_json.get("points", {})
        items = items.get("item", []) if items else []

        for dhl_point in items:
            point = _deep_copy_schema(GET_POINT_SCHEMA)
            if parcelshop_api:
                point["address"]["city"] = dhl_point["address"]["city"]
            else:
                point["type"] = dhl_point["type"]
                point["address"]["country_code"] = dhl_point["address"]["country"]

            point["name"] = dhl_point["name"]
            point["address"]["line1"] = dhl_point["address"]["street"]
            point["address"]["line2"] = dhl_point["address"]["houseNumber"]
            point["address"]["postal_code"] = format_postcode(
                dhl_point["address"]["postcode"],
            )
            point["address"]["longitude"] = float(dhl_point["longitude"])
            point["address"]["latitude"] = float(dhl_point["latitude"])
            point["additional_info"] = dhl_point["description"]

            points[dhl_point["sap"]] = point

        return points, status_code

    # ------------------------------------------------------------------
    # Private — authentication
    # ------------------------------------------------------------------

    @staticmethod
    def _get_auth_data(credentials: DhlCredentials) -> dict:
        return {
            "username": credentials.username,
            "password": credentials.password,
        }

    # ------------------------------------------------------------------
    # Private — buy offer (book courier)
    # ------------------------------------------------------------------

    def _buy_offer(
        self,
        credentials: DhlCredentials,
        command: dict,
    ) -> tuple[object, int]:
        """Book a courier pickup after shipment creation."""
        extras_dhl = get_extras(command, "dhl")

        try:
            response = self.client.service.bookCourier(
                authData=self._get_auth_data(credentials),
                pickupDate=extras_dhl["pickup_date"],
                pickupTimeFrom=extras_dhl["pickup_time_from"],
                pickupTimeTo=extras_dhl["pickup_time_to"],
                additionalInfo=extras_dhl.get("additional_info", ""),
                shipmentIdList=[extras_dhl["shipment_id"]],
                courierWithLabel=extras_dhl.get("courier_with_label", False),
            )
        except TransportError as exc:
            logger.error("DHL SOAP transport error: %s", str(exc.content)[:200])
            return {"error": "DHL API communication error"}, exc.status_code
        except Fault as exc:
            logger.error("DHL SOAP fault: %s", str(exc.message)[:200])
            return {"error": "DHL API request failed"}, HTTPStatus.BAD_REQUEST

        if response is None:
            return "Brak danych", HTTPStatus.CREATED

        status_code = (
            HTTPStatus.CREATED
            if isinstance(response, list)
            else (HTTPStatus.UNAUTHORIZED if response.code == "100" else HTTPStatus.BAD_REQUEST)
        )
        if status_code == HTTPStatus.CREATED:
            offer_id = wsdl_to_json(response[0])

            resp_json, get_order_sc = self.get_order(
                credentials,
                extras_dhl["shipment_id"],
                extras_dhl,
            )
            if get_order_sc != HTTPStatus.OK:
                return resp_json, get_order_sc
            resp_json.setdefault("extras", {}).setdefault("dhl", {})
            resp_json["extras"]["dhl"]["offer_id"] = offer_id
            resp_json["extras"]["dhl"]["shipment_id"] = extras_dhl["shipment_id"]
            return resp_json, status_code

        logger.error("DHL SOAP error in _buy_offer: %s", str(response.message)[:200])
        return {"error": "DHL API request failed"}, status_code

    # ------------------------------------------------------------------
    # Private — create shipment (SOAP call)
    # ------------------------------------------------------------------

    def _create_order(
        self,
        credentials: DhlCredentials,
        command: dict,
    ) -> tuple[object, int]:
        """Execute the raw SOAP ``createShipments`` / ``createShipment`` call."""
        target_point = self._get_target_point_from_extras(
            command.get("extras", {}).get("dhlps", {}),
        )

        try:
            if target_point:
                response = self.client_ps.service.createShipment(
                    shipment={
                        "authData": self._get_auth_data(credentials),
                        "shipmentData": self._get_create_order_structure(
                            command,
                            target_point,
                        ),
                    },
                )
            else:
                response = self.client.service.createShipments(
                    authData=self._get_auth_data(credentials),
                    shipments=self._get_create_order_structure(command),
                )
        except TransportError as exc:
            logger.error("DHL SOAP transport error: %s", str(exc.content)[:200])
            return {"error": "DHL API communication error"}, exc.status_code
        except Fault as exc:
            logger.error("DHL SOAP fault: %s", str(exc.message)[:200])
            return {"error": "DHL API request failed"}, HTTPStatus.BAD_REQUEST

        if response is None:
            return "Brak danych", HTTPStatus.NOT_FOUND

        if target_point:
            return (
                wsdl_to_json(response),
                HTTPStatus.OK if "shipmentNumber" in response else HTTPStatus.BAD_REQUEST,
            )

        status_code = (
            HTTPStatus.OK
            if isinstance(response, list)
            else (HTTPStatus.UNAUTHORIZED if response.code == "100" else HTTPStatus.BAD_REQUEST)
        )
        if status_code == HTTPStatus.OK:
            return wsdl_to_json(response[0]), status_code
        logger.error("DHL SOAP error in _create_order: %s", str(response.message)[:200])
        return {"error": "DHL API request failed"}, status_code

    # ------------------------------------------------------------------
    # Private — build the SOAP shipment structure
    # ------------------------------------------------------------------

    def _get_create_order_structure(
        self,
        command: dict,
        target_point: str | None = None,
    ) -> dict:
        """Assemble the shipment dict expected by the DHL SOAP API."""
        shipper = command.get("shipper", {})
        receiver = command.get("receiver", {})
        parcels = command.get("parcels", [])
        payment = command.get("payment", {})
        cod = command.get("cod", False)
        cod_value = command.get("codValue", command.get("cod_value", 0))
        content = command.get("content", "")
        content2 = command.get("content2", "")
        shipment_date = command.get("shipment_date", command.get("shipmentDate", ""))
        service_name = command.get("serviceName", command.get("service_name", "AH"))

        dhlps_extras: dict = command.get("extras", {}).get("dhlps", {})
        dhl_extras: dict = command.get("extras", {}).get("dhl", dhlps_extras)

        if dhl_extras.get("delivery9"):
            service_name = "09"
        if dhl_extras.get("delivery12"):
            service_name = "12"

        dhlps_extra_services = self._add_dhlps_extra_services(command, dhlps_extras)

        # ---- Parcelshop structure ----
        if target_point:
            return {
                "ship": {
                    "shipper": {
                        "address": {
                            "name": f"{shipper.get('first_name', '')} {shipper.get('last_name', '')}",
                            "postcode": self._strip_postcode(
                                shipper.get("postal_code", ""),
                                shipper.get("country_code", "PL"),
                            ),
                            "city": shipper.get("city", ""),
                            "street": shipper.get("street", ""),
                            "houseNumber": shipper.get("building_number", ""),
                        },
                        "contact": {
                            "personName": shipper.get("contact_person", ""),
                            "phoneNumber": shipper.get("phone", ""),
                            "emailAddress": shipper.get("email", ""),
                        },
                        "preaviso": {
                            "personName": receiver.get("contact_person", ""),
                            "phoneNumber": receiver.get("phone", ""),
                            "emailAddress": receiver.get("email", ""),
                        },
                    },
                    "receiver": {
                        "address": {
                            "name": f"{receiver.get('first_name', '')} {receiver.get('last_name', '')}",
                            "postcode": self._strip_postcode(
                                receiver.get("postal_code", ""),
                                receiver.get("country_code", "PL"),
                            ),
                            "city": receiver.get("city", ""),
                            "street": receiver.get("street", ""),
                            "houseNumber": receiver.get("building_number", ""),
                        },
                        "contact": {
                            "personName": receiver.get("contact_person", ""),
                            "phoneNumber": receiver.get("phone", ""),
                            "emailAddress": receiver.get("email", ""),
                        },
                        "preaviso": {
                            "personName": shipper.get("contact_person", ""),
                            "phoneNumber": shipper.get("phone", ""),
                            "emailAddress": shipper.get("email", ""),
                        },
                    },
                    "servicePointAccountNumber": target_point,
                },
                "shipmentInfo": {
                    "dropOffType": "REGULAR_PICKUP",
                    "serviceType": service_name,
                    "billing": {
                        "paymentType": payment.get("payment_method", ""),
                        "shippingPaymentType": payment.get("payer_type", ""),
                        "billingAccountNumber": payment.get("account_id", ""),
                        "costsCenter": content2,
                    },
                    "shipmentDate": shipment_date,
                    "shipmentStartHour": dhl_extras.get("pickup_time_from", ""),
                    "shipmentEndHour": dhl_extras.get("pickup_time_to", ""),
                    "labelType": "BLP",
                    "specialServices": dhlps_extra_services,
                },
                "pieceList": [
                    {
                        "item": {
                            "type": p.get("type", p.get("parcel_type", "PACKAGE")),
                            "width": p.get("width", 0),
                            "height": p.get("height", 0),
                            "lenght": p.get("length", 0),
                            "weight": p.get("weight", 0),
                            "quantity": p.get("quantity", 1),
                        },
                    }
                    for p in parcels
                ],
                "content": content,
            }

        # ---- Standard DHL24 structure ----
        is_packstation = bool(dhl_extras.get("is_packstation"))
        is_postfiliale = bool(dhl_extras.get("is_postfiliale"))
        postnummer = dhl_extras.get("postnummer")

        items = []
        for p in parcels:
            items.append(
                {
                    "type": p.get("type", p.get("parcel_type", "PACKAGE")),
                    "width": p.get("width", 0),
                    "height": p.get("height", 0),
                    "length": p.get("length", 0),
                    "weight": p.get("weight", 0),
                    "quantity": p.get("quantity", 1),
                }
            )

        dhl24_structure = {
            "item": {
                "shipper": {
                    "name": f"{shipper.get('first_name', '')} {shipper.get('last_name', '')}",
                    "postalCode": self._strip_postcode(
                        shipper.get("postal_code", ""),
                        shipper.get("country_code", "PL"),
                    ),
                    "city": shipper.get("city", ""),
                    "street": shipper.get("street", ""),
                    "houseNumber": shipper.get("building_number", ""),
                    "contactPerson": shipper.get("contact_person", ""),
                    "contactPhone": shipper.get("phone", ""),
                    "contactEmail": shipper.get("email", ""),
                },
                "receiver": {
                    "addressType": "B",
                    "country": receiver.get("country_code", "PL"),
                    "postnummer": postnummer,
                    "name": f"{receiver.get('first_name', '')} {receiver.get('last_name', '')}",
                    "postalCode": self._strip_postcode(
                        receiver.get("postal_code", ""),
                        receiver.get("country_code", "PL"),
                    ),
                    "city": receiver.get("city", ""),
                    "street": receiver.get("street", ""),
                    "houseNumber": receiver.get("building_number", ""),
                    "contactPerson": receiver.get("contact_person", ""),
                    "contactPhone": receiver.get("phone", ""),
                    "contactEmail": receiver.get("email", ""),
                    "isPackstation": is_packstation,
                    "isPostfiliale": is_postfiliale,
                },
                "skipRestrictionCheck": True,
                "pieceList": {"item": items},
                "payment": {
                    "paymentMethod": payment.get("payment_method", ""),
                    "payerType": payment.get("payer_type", ""),
                    "accountNumber": payment.get("account_id", ""),
                    "costsCenter": content2,
                },
                "service": {
                    "product": service_name,
                    "collectOnDelivery": bool(cod),
                    "collectOnDeliveryValue": cod_value if cod else None,
                    "collectOnDeliveryForm": self.DEFAULT_COD_FORM if cod else None,
                    "insurance": bool(dhl_extras.get("insurance")),
                    "insuranceValue": (dhl_extras.get("insurance_value") if dhl_extras.get("insurance") else None),
                    "returnOnDelivery": dhl_extras.get("rod", False),
                    "predeliveryInformation": dhl_extras.get(
                        "predelivery_information",
                        False,
                    ),
                    "deliveryOnSaturday": dhl_extras.get("deliveryOnSaturday", False),
                },
                "shipmentDate": shipment_date,
                "content": content,
            },
        }

        if cod:
            svc = dhl24_structure["item"]["service"]
            svc["insurance"] = True
            svc["insuranceValue"] = dhl_extras.get("insurance_value") if dhl_extras.get("insurance") else cod_value

        logger.debug("DHL24 create-order payload assembled")
        return dhl24_structure

    # ------------------------------------------------------------------
    # Private — parcelshop extra services
    # ------------------------------------------------------------------

    def _add_dhlps_extra_services(
        self,
        command: dict,
        dhlps_extras: dict,
    ) -> list[dict]:
        extra_services: list[dict] = []
        cod = command.get("cod", False)
        cod_value = command.get("codValue", command.get("cod_value", 0))
        payment = command.get("payment", {})

        if dhlps_extras.get("insurance"):
            extra_services.append(
                {
                    "item": {
                        "serviceType": "UBEZP",
                        "serviceValue": str(dhlps_extras.get("insurance_value", 0)),
                    },
                }
            )

        if cod:
            if not dhlps_extras.get("insurance"):
                extra_services.append(
                    {
                        "item": {
                            "serviceType": "UBEZP",
                            "serviceValue": str(cod_value * 2),
                        },
                    }
                )
            extra_services.append(
                {
                    "item": {
                        "serviceType": "COD",
                        "serviceValue": str(cod_value),
                        "collectOnDeliveryForm": payment.get("payment_method", "BANK_TRANSFER"),
                    },
                }
            )

        return extra_services

    # ------------------------------------------------------------------
    # Private — normalisation helpers
    # ------------------------------------------------------------------

    def _normalize_order_item(
        self,
        command: dict,
        order: dict,
    ) -> dict:
        """Build a normalised response dict from a raw order."""
        shipper = command.get("shipper", {})
        receiver = command.get("receiver", {})
        return {
            "id": order.get("shipmentId", ""),
            "waybill_number": order.get("tracking_number", ""),
            "shipper": self._normalize_shipment_party(shipper),
            "receiver": self._normalize_shipment_party(receiver),
            "created_at": order.get("created", ""),
            "orderStatus": order.get("orderStatus", ""),
            "tracking": order.get("tracking", {}),
            "extras": order.get("extras", {}),
        }

    def _normalize_order_item_parcelshop(
        self,
        _credentials: DhlCredentials,
        command: dict,
        order: dict,
    ) -> dict:
        """Normalise a ServicePoint ``createShipment`` response."""
        waybill_number = order.get("shipmentNumber", "")
        order.pop("label", None)

        tracking_info, _ = self.get_tracking_info(waybill_number)
        order["tracking"] = tracking_info
        order["tracking_number"] = waybill_number

        shipper = command.get("shipper", {})
        receiver = command.get("receiver", {})

        order["receiver"] = dict(receiver)
        order["receiver"]["name"] = f"{receiver.get('first_name', '')} {receiver.get('last_name', '')}"
        order["receiver"]["contactPhone"] = receiver.get("phone", "")
        order["receiver"]["contactEmail"] = receiver.get("email", "")
        order["receiver"]["postalCode"] = receiver.get("postal_code", "")
        order["receiver"]["houseNumber"] = receiver.get("building_number", "")

        order["shipper"] = dict(shipper)
        order["shipper"]["name"] = f"{shipper.get('first_name', '')} {shipper.get('last_name', '')}"
        order["shipper"]["contactPhone"] = shipper.get("phone", "")
        order["shipper"]["contactEmail"] = shipper.get("email", "")
        order["shipper"]["postalCode"] = shipper.get("postal_code", "")
        order["shipper"]["houseNumber"] = shipper.get("building_number", "")

        order["shipmentId"] = waybill_number
        order["created"] = date.today().isoformat()
        order["orderStatus"] = "Nowa"

        return self._normalize_order_item(command, order)

    @staticmethod
    def _normalize_shipment_party(party: dict) -> dict:
        """Convert a command-side party dict to a response-side structure."""
        street = party.get("street", "")
        building = party.get("building_number", "")
        postal = party.get("postal_code", "")
        city = party.get("city", "")
        country = party.get("country_code", "PL")
        return {
            "first_name": party.get("first_name", ""),
            "last_name": party.get("last_name", ""),
            "contact_person": party.get("contact_person", ""),
            "phone": party.get("phone", ""),
            "email": party.get("email", ""),
            "address": {
                "building_number": building,
                "city": city,
                "country_code": country,
                "line1": f"{street} {building}",
                "line2": f"{postal} {city} {country}",
                "post_code": postal,
                "street": street,
            },
        }

    # ------------------------------------------------------------------
    # Private — misc helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _strip_postcode(postcode: str, country_code: str) -> str:
        """Strip hyphens from postcode (except PT postcodes)."""
        return postcode if country_code == "PT" else postcode.replace("-", "")

    @staticmethod
    def _translate_payer_type(payer_type: str) -> str:
        return "USER" if payer_type == "RECIPIENT" else payer_type

    @staticmethod
    def _retrieve_time_range(data: dict) -> tuple[date, date]:
        try:
            extras = get_extras(data)
            created_from = extras.get("created_from", date.today() - timedelta(days=2))
            created_to = extras.get("created_to", date.today())
        except (ValueError, KeyError, TypeError):
            return date.today() - timedelta(days=89), date.today()
        if created_from is None or created_to is None:
            return date.today() - timedelta(days=89), date.today()
        return created_from, created_to

    @staticmethod
    def _get_target_point_from_extras(extras: dict) -> str | None:
        return extras.get("custom_attributes", {}).get("target_point")

    @staticmethod
    def _guess_extension(mime_type: str) -> str:
        ext = mimetypes.guess_extension(mime_type)
        return ext if ext else ".pdf"

    @staticmethod
    def _zip_labels(labels: list[dict]) -> bytes:
        """Package multiple labels into a ZIP archive and return the bytes."""
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED, False) as zf:
            for label in labels:
                ext = DhlIntegration._guess_extension(label.get("labelMimeType", "application/pdf"))
                zf.writestr(
                    f"{label['shipmentId']}{ext}",
                    base64.b64decode(label["labelData"]),
                )
        return output.getvalue()


# ---------------------------------------------------------------------------
# Module-level helper
# ---------------------------------------------------------------------------


def _deep_copy_schema(schema: dict) -> dict:
    """Return a deep copy of a nested dict template."""
    return json.loads(json.dumps(schema))
