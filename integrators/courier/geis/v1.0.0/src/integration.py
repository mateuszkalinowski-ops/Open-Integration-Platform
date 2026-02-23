"""Geis Courier Integration — migrated from meriship codebase.

Handles all Geis SOAP API interactions including:
- Order creation (InsertOrder / InsertExport)
- Order deletion (DeleteShipment)
- Order details (ShipmentDetail)
- Status tracking (ShipmentStatus)
- Label retrieval (GetLabel)
- Health check (IsHealthy)
- Range assignment (AssignRange)
- Pickup creation (CreatePickUp)
"""

from __future__ import annotations

import logging
from datetime import datetime
from http import HTTPStatus

from zeep import Client, Transport
from zeep.exceptions import Fault, TransportError

from src.config import settings
from src.schemas import (
    CreateOrderCommand,
    CreateOrderResponse,
    GeisCredentials,
    ShipmentParty,
)

logger = logging.getLogger("courier-geis")


class GeisIntegration:
    """Geis SOAP integration.

    Supports both domestic (InsertOrder) and export (InsertExport) shipment types.
    Uses distribution channel 2 (Cargo).
    """

    CARGO_DISTRIBUTION_CHANNEL = 2
    ERROR_CODE_SUCCESS = "0000"

    def __init__(self) -> None:
        transport = Transport(timeout=settings.soap_timeout)
        self.client: Client | None = None

        try:
            self.client = Client(settings.geis_api_url, transport=transport)
            logger.info("SOAP client connected — %s", settings.geis_api_url)
        except ConnectionError:
            logger.error("SOAP client timeout — %s", settings.geis_api_url)
        except Exception:
            logger.exception("SOAP client init failed — %s", settings.geis_api_url)

        if self.client and not self._check_healthy():
            logger.error("Geis service health check failed")

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    def check_healthy(self) -> bool:
        """Public health check wrapper."""
        return self._check_healthy()

    # ------------------------------------------------------------------
    # Order status
    # ------------------------------------------------------------------

    def get_order_status(
        self,
        credentials: GeisCredentials,
        waybill_number: str,
    ) -> tuple[str | dict, int]:
        """Retrieve shipment status via ShipmentStatus."""
        resp, err = self._call_service(
            "ShipmentStatus",
            Request={
                "Header": self._get_header(credentials),
                "RequestObject": {"ShipmentNumber": waybill_number},
            },
        )
        if err:
            return err[0], HTTPStatus.BAD_REQUEST
        return resp["StatusName"], HTTPStatus.OK

    # ------------------------------------------------------------------
    # Create shipment
    # ------------------------------------------------------------------

    def create_order(
        self,
        credentials: GeisCredentials,
        command: CreateOrderCommand,
    ) -> tuple[CreateOrderResponse | str, int]:
        """Create order — uses InsertExport or InsertOrder based on extras.

        If InsertOrder/InsertExport returns error code 3040, creates a pickup
        first and retries InsertOrder.
        """
        geis_extras: dict = command.extras.get("geis", {})

        if geis_extras.get("geis_export", True):
            resp, err = self._insert_export(credentials, command)
        else:
            resp, err = self._insert_order(credentials, command)

        if err:
            return err[0], HTTPStatus.BAD_REQUEST

        if resp["ErrorCode"] == "3040":
            pickup_resp, pickup_err = self._create_pick_up(credentials, command)
            if pickup_err:
                return pickup_err[0], HTTPStatus.BAD_REQUEST
            if pickup_resp["ErrorCode"] != self.ERROR_CODE_SUCCESS:
                logger.warning("Pickup processing error: %s", pickup_resp["ErrorMessage"])

            resp, err = self._insert_order(credentials, command)
            if err:
                return err[0], HTTPStatus.BAD_REQUEST
            if resp["ErrorCode"] != self.ERROR_CODE_SUCCESS:
                logger.error("Order processing error: %s", resp["ErrorMessage"])
                return resp["ErrorMessage"], HTTPStatus.BAD_REQUEST

        if resp["ErrorCode"] != self.ERROR_CODE_SUCCESS:
            logger.error("Order processing error: %s", resp["ErrorMessage"])
            return resp["ErrorMessage"], HTTPStatus.BAD_REQUEST

        if geis_extras.get("book_courier"):
            pickup_resp, pickup_err = self._create_pick_up(credentials, command)
            if pickup_err:
                return pickup_err[0], HTTPStatus.BAD_REQUEST
            if pickup_resp["ErrorCode"] != self.ERROR_CODE_SUCCESS:
                logger.warning("Pickup processing error: %s", pickup_resp["ErrorMessage"])

        return self._normalize_order_item(command, resp), HTTPStatus.CREATED

    # ------------------------------------------------------------------
    # Labels
    # ------------------------------------------------------------------

    def get_waybill_label_bytes(
        self,
        credentials: GeisCredentials,
        waybill_numbers: list[str],
        _args: dict | None = None,
    ) -> tuple[bytes | str, int]:
        """Retrieve label via GetLabel. Returns PDF bytes for thermal printers (format 5)."""
        resp, err = self._call_service(
            "GetLabel",
            Request={
                "Header": self._get_header(credentials),
                "RequestObject": {
                    "ShipmentNumbers": [
                        {"LabelItem": {"ShipmentNumber": waybill_numbers[0]}}
                    ],
                    "DistributionChannel": self.CARGO_DISTRIBUTION_CHANNEL,
                    "Format": 5,
                    "Position": 1,
                },
            },
        )
        if err:
            return err[0], HTTPStatus.BAD_REQUEST
        if resp["ErrorCode"] != self.ERROR_CODE_SUCCESS:
            return resp["ErrorMessage"], HTTPStatus.BAD_REQUEST

        byte_data = resp["ResponseObject"]["LabelData"]["LabelItemData"][0]["Data"]
        return byte_data, HTTPStatus.OK

    # ------------------------------------------------------------------
    # Order details
    # ------------------------------------------------------------------

    def get_order(
        self,
        credentials: GeisCredentials,
        waybill_number: str,
    ) -> tuple[object, int]:
        """Retrieve order details via ShipmentDetail."""
        resp, err = self._call_service(
            "ShipmentDetail",
            Request={
                "Header": self._get_header(credentials),
                "RequestObject": {
                    "DistributionChannel": self.CARGO_DISTRIBUTION_CHANNEL,
                    "ShipmentNumber": waybill_number,
                },
            },
        )
        if err:
            return err[0], HTTPStatus.BAD_REQUEST
        return resp, HTTPStatus.OK

    # ------------------------------------------------------------------
    # Delete shipment
    # ------------------------------------------------------------------

    def delete_order(
        self,
        credentials: GeisCredentials,
        waybill_number: str,
    ) -> tuple[str | None, int]:
        """Delete shipment via DeleteShipment."""
        resp, err = self._call_service(
            "DeleteShipment",
            Request={
                "Header": self._get_header(credentials),
                "RequestObject": {
                    "ShipmentsNumbers": [
                        {
                            "DeleteShipmentItem": {
                                "DistributionChannel": self.CARGO_DISTRIBUTION_CHANNEL,
                                "ShipmentNumber": waybill_number,
                            },
                        },
                    ],
                },
            },
        )
        if err:
            return err[0], HTTPStatus.BAD_REQUEST
        if resp["ErrorCode"] != self.ERROR_CODE_SUCCESS:
            return resp["ErrorMessage"], HTTPStatus.BAD_REQUEST

        deleted_items_response: list = resp["ResponseObject"]["ShipmentsNumbers"][
            "DeleteShipmentItemResponse"
        ]
        for del_response in deleted_items_response:
            if not del_response["IsStorno"]:
                return del_response["ErrorMessage"], HTTPStatus.BAD_REQUEST

        return None, HTTPStatus.OK

    # ------------------------------------------------------------------
    # Range assignment
    # ------------------------------------------------------------------

    def assign_range(
        self,
        credentials: GeisCredentials,
    ) -> tuple[tuple[str, str] | str, int]:
        """Assign a shipment number range via AssignRange."""
        resp, err = self._call_service(
            "AssignRange",
            Request={
                "Header": self._get_header(credentials),
                "RequestObject": {
                    "DistributionChannel": self.CARGO_DISTRIBUTION_CHANNEL,
                },
            },
        )
        if err:
            return err[0], HTTPStatus.BAD_REQUEST
        if resp["ErrorCode"] != self.ERROR_CODE_SUCCESS:
            return resp["ErrorMessage"], HTTPStatus.BAD_REQUEST

        return (
            resp["ResponseObject"]["RangeLow"],
            resp["ResponseObject"]["RangeHigh"],
        ), HTTPStatus.OK

    # ------------------------------------------------------------------
    # Private — health check
    # ------------------------------------------------------------------

    def _check_healthy(self) -> bool:
        resp, err = self._call_service("IsHealthy")
        if err:
            return False
        return resp["Status"] == "HEALTHY"

    # ------------------------------------------------------------------
    # Private — InsertOrder (domestic)
    # ------------------------------------------------------------------

    def _insert_order(
        self,
        credentials: GeisCredentials,
        command: CreateOrderCommand,
    ) -> tuple[object | None, tuple[str, int] | None]:
        return self._call_service(
            "InsertOrder",
            Request={
                "Header": self._get_header(credentials),
                "RequestObject": self._get_insert_order_payload(command),
            },
        )

    def _get_insert_order_payload(self, command: CreateOrderCommand) -> dict:
        return {
            "DistributionChannel": self.CARGO_DISTRIBUTION_CHANNEL,
            "PickUpDate": command.shipment_date,
            "Reference": command.content,
            "Note": command.content,
            "ExportItems": [
                {
                    "ExportItem": {
                        "CountItems": p.quantity,
                        "Description": command.content,
                        "Type": p.parcel_type,
                        "Weight": p.weight,
                        "Height": p.height / 100,
                        "Width": p.width / 100,
                        "Length": p.length / 100,
                    },
                }
                for p in command.parcels
            ],
            "SenderAddress": self._get_address_payload(command.shipper),
            "SenderContact": self._get_contact_payload(command.shipper),
            "DeliveryAddress": self._get_address_payload(command.receiver),
            "DeliveryContact": self._get_contact_payload(command.receiver),
            "ExportServices": self._get_export_services_payload(command),
        }

    # ------------------------------------------------------------------
    # Private — InsertExport
    # ------------------------------------------------------------------

    def _insert_export(
        self,
        credentials: GeisCredentials,
        command: CreateOrderCommand,
    ) -> tuple[object | None, tuple[str, int] | None]:
        return self._call_service(
            "InsertExport",
            Request={
                "Header": self._get_header(credentials),
                "RequestObject": self._get_insert_export_payload(command),
            },
        )

    def _get_insert_export_payload(self, command: CreateOrderCommand) -> dict:
        payload = self._get_insert_order_payload(command)
        del payload["SenderAddress"]
        return payload

    # ------------------------------------------------------------------
    # Private — CreatePickUp
    # ------------------------------------------------------------------

    def _create_pick_up(
        self,
        credentials: GeisCredentials,
        command: CreateOrderCommand,
    ) -> tuple[object | None, tuple[str, int] | None]:
        return self._call_service(
            "CreatePickUp",
            Request={
                "Header": self._get_header(credentials),
                "RequestObject": self._get_pick_up_payload(command),
            },
        )

    def _get_pick_up_payload(self, command: CreateOrderCommand) -> dict:
        extras = command.extras.get("geis", {})
        date_from = datetime.strptime(
            f"{extras['pickup_date']}T{extras['pickup_time_from']}", "%Y-%m-%dT%H:%M"
        ).isoformat()
        date_to = datetime.strptime(
            f"{extras['pickup_date']}T{extras['pickup_time_to']}", "%Y-%m-%dT%H:%M"
        ).isoformat()

        return {
            "DistributionChannel": self.CARGO_DISTRIBUTION_CHANNEL,
            "DateFrom": date_from,
            "DateTo": date_to,
            "CountItems": sum(p.quantity for p in command.parcels),
            "TotalWeight": sum(p.weight * p.quantity for p in command.parcels),
            "Contact": self._get_contact_payload(command.receiver),
            "Note": command.content,
        }

    # ------------------------------------------------------------------
    # Private — address/contact payloads
    # ------------------------------------------------------------------

    @staticmethod
    def _get_address_payload(party: ShipmentParty) -> dict:
        return {
            "Name": f"{party.first_name} {party.last_name}",
            "Street": party.street,
            "City": party.city,
            "ZipCode": party.postal_code,
            "Country": party.country_code,
        }

    @staticmethod
    def _get_contact_payload(party: ShipmentParty) -> dict:
        return {
            "FullName": f"{party.first_name} {party.last_name}",
            "Email": party.email,
            "Phone": party.phone,
        }

    # ------------------------------------------------------------------
    # Private — export services (COD, insurance)
    # ------------------------------------------------------------------

    @staticmethod
    def _get_export_services_payload(command: CreateOrderCommand) -> list[dict]:
        extras: dict = command.extras.get("geis", {})
        services: list[dict] = []

        if command.cod:
            services.append({
                "Code": "COD",
                "Parameter_1": command.cod_value,
                "Parameter_2": command.cod_curr,
                "Parameter_4": command.payment.account_id,
            })

        if extras.get("insurance"):
            services.append({
                "Code": "POJ",
                "Parameter_1": extras.get("insurance_value"),
                "Parameter_2": extras.get("insurance_curr"),
            })

        return services

    # ------------------------------------------------------------------
    # Private — header
    # ------------------------------------------------------------------

    @staticmethod
    def _get_header(credentials: GeisCredentials) -> dict:
        return {
            "CustomerCode": credentials.customer_code,
            "Password": credentials.password,
            "Language": credentials.default_language,
        }

    # ------------------------------------------------------------------
    # Private — normalisation
    # ------------------------------------------------------------------

    def _normalize_order_item(
        self,
        command: CreateOrderCommand,
        order_data: dict,
    ) -> CreateOrderResponse:
        waybill_number = order_data["ResponseObject"]["PackNumber"]
        return CreateOrderResponse(
            id=waybill_number,
            waybill_number=waybill_number,
            shipper=self._normalize_shipment_party(command.shipper),
            receiver=self._normalize_shipment_party(command.receiver),
            order_status="CREATED",
        )

    @staticmethod
    def _normalize_shipment_party(party: ShipmentParty) -> dict:
        return {
            "first_name": party.first_name,
            "last_name": party.last_name,
            "phone": party.phone,
            "email": party.email,
            "address": {
                "street": party.street,
                "building_number": party.building_number,
                "city": party.city,
                "postal_code": party.postal_code,
                "country_code": party.country_code,
            },
        }

    # ------------------------------------------------------------------
    # Private — generic SOAP call wrapper
    # ------------------------------------------------------------------

    def _call_service(
        self,
        method: str,
        *args: object,
        **kwargs: object,
    ) -> tuple[object | None, tuple[str, int] | None]:
        """Wrapper for Geis SOAP calls with transport/fault error handling."""
        try:
            return getattr(self.client.service, method)(*args, **kwargs), None
        except TransportError as e:
            logger.exception("SOAP transport error on %s", method)
            return None, (e.content, e.status_code)
        except Fault as e:
            logger.exception("SOAP fault on %s", method)
            return None, (e.code, HTTPStatus.BAD_REQUEST)
