"""Orlen Paczka Courier Integration — migrated from meriship codebase.

Handles all Orlen Paczka SOAP API interactions including:
- Shipment creation (GenerateBusinessPack)
- Shipment cancellation (PutCustomerPackCanceled)
- Status tracking (GiveMePackStatus)
- Label retrieval (LabelPrintDuplicateList)
- Pickup point lookup (GiveMeAllRUCHWithFilled)
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from enum import Enum
from http import HTTPStatus

from zeep import Client, Transport
from zeep.exceptions import Fault, TransportError
from zeep.helpers import serialize_object

from src.config import settings
from src.schemas import (
    CreateOrderCommand,
    CreateOrderResponse,
    OrlenPaczkaCredentials,
    ShipmentParty,
    Tracking,
)

logger = logging.getLogger("courier-orlenpaczka")


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def wsdl_to_json(data: object) -> dict:
    """Convert a zeep SOAP response object to a JSON-serializable dict."""
    return json.loads(json.dumps(serialize_object(data)))


# ---------------------------------------------------------------------------
# Orlen Paczka Return Codes
# ---------------------------------------------------------------------------

class OrlenPaczkaReturnCodes(Enum):
    """Enum representing possible return codes that Orlen Paczka API returns."""

    NO_PARTNER_ID = (100, "brak PartnerID")
    NO_PARTNER_KEY = (101, "brak PartnerKey")
    NO_PHONE = (103, "brak PhoneNumber")
    NO_DESTINATION_CODE = (104, "brak DestinationCode")
    NO_NAMES = (105, "brak FirstName i LastName lub CompanyName")
    NO_PACK_CODE = (106, "brak PackCode")
    NO_PRINT_ADDRESS = (107, "brak PrintAdress")
    NO_SENDER_EMAIL = (111, "brak SenderEMail")
    NO_SENDER_PHONE = (112, "brak SenderPhoneNumber")
    NO_SENDER_CITY = (113, "brak SenderCity")
    NO_SENDER_STREET = (114, "brak SenderStreetName")
    NO_SENDER_BUILDING = (115, "brak SenderBuildingNumber")
    NO_SENDER_POST_CODE = (116, "brak SenderPostCode")
    NO_SENDER_NAMES = (117, "brak SenderFirstName i SenderLastName lub SenderCompanyName")
    NO_COD_VALUE = (120, "brak AmountCashOnDelivery")
    NO_COD_TRANSFER_DESC = (121, "brak TransferDescription")
    NO_RETURN_CITY = (123, "brak ReturnCity")
    NO_RETURN_STREET = (124, "brak ReturnStreetName")
    NO_RETURN_BUILDING = (125, "brak ReturnBuildingNumber")
    NO_RETURN_POST_CODE = (126, "brak ReturnPostCode")
    NO_RETURN_COMPANY = (127, "brak ReturnCompanyName")
    NO_RETURN_RETURN_FLAG = (128, "brak ReturnAvailable")
    NO_RETURN_RETURN_QUANTITY = (129, "brak ReturnQuantity")
    INVALID_SYMBOLS_COD_VALUE = (130, "niedozwolone znaki w AmountCashOnDelivery")
    INVALID_SYMBOLS_COD_TRANSFER_DESC = (131, "niedozwolone znaki w TransferDescription")
    INVALID_PHONE = (133, "niepoprawny PhoneNumber")
    INVALID_PACK_VALUE = (134, "niepoprawny PackValue")
    PACK_VALUE_BIGGER_THAN_INSURANCE = (135, "PackValue przekracza maksymalną wartość ubezpieczenia")
    INVALID_COD_TRANSFER_DESC = (136, "niepoprawny TransferDescription")
    INVALID_RETURN_QUANTITY = (137, "niepoprawny ReturnQuantity")
    INVALID_POST_CODE = (138, "niepoprawny PostCode")
    NO_ZERO_IN_COD_VALUE = (140, "nie może być zero w AmountCashOnDelivery")
    INVALID_BOX_SIZE = (141, "niepoprawny BoxSize")
    INVALID_PARCEL_COUNT = (150, "przekroczona maksymalna liczba paczek")
    INVALID_PACK_CODE_AND_PHONE = (163, "brak PackCode i PhoneNumber")

    INVALID_PARTNER_ID_OR_KEY = (200, "niepoprawny PartnerID i/lub PartnerKey")
    ALREADY_CANCELLED = (201, "już była anulowana")
    CANNOT_BE_CANCELLED = (202, "już nie może być anulowana")
    UNKNOWN_PACK_CODE = (205, "nieznany PackCode")
    UNKNOWN_DESTINATION_CODE = (206, "nieznany DestinationCode")
    UNKNOWN_RETURN_DESTINATION_CODE = (207, "nieznany ReturnDestinationCode")
    CLIENT_ALREADY_EXISTS = (208, "klient już istnieje")
    INVALID_PACK_CODE = (209, "niepoprawny PackCode")
    MISSING_ROUTING_DATA_FOR_LABEL = (211, "lack of routing data for this label")
    UNAUTHORIZED_FOR_LABEL_NUMBER = (212, "no permission to this label number")
    PARCEL_ALREADY_SENT_WITH_NUMBER = (213, "parcel with this number already sent via Ruch")
    PARCEL_NOT_FOUND = (222, "Pack not found in Ruch system")
    UNAUTHORIZED_PACK_ACCESS = (223, "Pack does not belong to partner")

    UNAUTHORIZED_COD_ACCESS = (310, "no permission to COD")
    UNAUTHORIZED_INSURANCE_ACCESS = (311, "no permission to Insurance")
    UNAUTHORIZED_RETURN_ACCESS = (312, "no permission to Return")
    COD_NOT_AVAILABLE_FOR_DEST_CODE = (318, "no service COD in DestinationCode")

    SAVED_BUT_DEST_CODE_CHANGED = (6, "zapisano ale zmieniono DestinationCode")
    SAVED_BUT_RETURN_DEST_CODE_CHANGED = (7, "zapisano ale zmieniono ReturnDestinationCode")
    SAVED_BUT_DEST_AND_RETURN_DEST_CODE_CHANGED = (
        8,
        "zapisano ale zmieniono DestinationCode i ReturnDestinationCode",
    )
    SAVED = (0, "Zapisano")

    @classmethod
    def success_codes(cls) -> list[int]:
        return [code.value[0] for code in cls if code.value[0] in set(range(100))]

    @classmethod
    def unauthorized_codes(cls) -> list[int]:
        return [code.value[0] for code in cls if code.value[0] in {200, 212, 223, 310, 311, 312, 318}]


# ---------------------------------------------------------------------------
# Orlen Paczka Integration
# ---------------------------------------------------------------------------

class OrlenPaczkaIntegration:
    """Orlen Paczka SOAP integration.

    Uses zeep to communicate with the Orlen Paczka WSDL service.
    All methods return (result, status_code) tuples.
    """

    TRACKING_URL = "https://www.orlenpaczka.pl/sledz-paczke/?numer={tracking_number}"

    def __init__(self) -> None:
        transport = Transport(timeout=settings.soap_timeout)
        transport.session.verify = False
        self.client: Client | None = None

        try:
            self.client = Client(settings.orlen_paczka_wsdl_path, transport=transport)
            logger.info("SOAP client connected — %s", settings.orlen_paczka_wsdl_path)
        except ConnectionError:
            logger.error("SOAP client timeout — %s", settings.orlen_paczka_wsdl_path)
        except Exception:
            logger.exception("SOAP client init failed — %s", settings.orlen_paczka_wsdl_path)

    # ------------------------------------------------------------------
    # Order status
    # ------------------------------------------------------------------

    def get_order_status(
        self,
        credentials: OrlenPaczkaCredentials,
        order_id: str,
    ) -> tuple[str, int]:
        """Get order status via GiveMePackStatus.

        Orlen Paczka might not return data for several seconds after order creation.
        """
        payload = {
            "PartnerID": credentials.partner_id,
            "PartnerKey": credentials.partner_key,
            "PackCode": order_id,
            "PhoneNumber": None,
        }
        extract: Callable = lambda r: r._value_1._value_1[0].get("PackStatus")
        response, err = self._call_service("GiveMePackStatus", extract, **payload)
        if err:
            return err

        if "Trans" in response:
            order_status_code = int(response["Trans"])
        else:
            logger.error("Error fetching orlenpaczka status: %s", response["ErrDes"])
            return (
                f'Error code: {response["Err"]}, Details: {response["ErrDes"]}',
                HTTPStatus.BAD_REQUEST,
            )

        return str(order_status_code), HTTPStatus.OK

    # ------------------------------------------------------------------
    # Tracking info
    # ------------------------------------------------------------------

    def get_tracking_info(
        self,
        order_id: str,
    ) -> tuple[Tracking, int]:
        """Return tracking URL — no API call needed."""
        resp = Tracking(
            tracking_number=order_id,
            tracking_url=self.TRACKING_URL.format(tracking_number=order_id),
        )
        return resp, HTTPStatus.OK

    # ------------------------------------------------------------------
    # Create shipment
    # ------------------------------------------------------------------

    def create_order(
        self,
        credentials: OrlenPaczkaCredentials,
        command: CreateOrderCommand,
    ) -> tuple[CreateOrderResponse | str, int]:
        """Create order via GenerateBusinessPack."""
        create_order_dictionary = self._get_create_order_dict(credentials, command)
        response, err = self._call_service("GenerateBusinessPack", **create_order_dictionary)
        if err:
            return err

        return (
            self._normalize_order_item(command, waybill_number=response["PackCode_RUCH"]),
            HTTPStatus.CREATED,
        )

    # ------------------------------------------------------------------
    # Delete shipment
    # ------------------------------------------------------------------

    def delete_order(
        self,
        credentials: OrlenPaczkaCredentials,
        order_id: str,
    ) -> tuple[dict | str, int]:
        """Cancel order via PutCustomerPackCanceled."""
        payload = {
            "PartnerID": credentials.partner_id,
            "PartnerKey": credentials.partner_key,
            "PackCode": order_id,
        }
        delete_extraction_func: Callable = (
            lambda r: r._value_1._value_1[0].get("CustomerPackCanceled")
        )

        _, err = self._call_service(
            method="PutCustomerPackCanceled",
            extract=delete_extraction_func,
            **payload,
        )
        if err:
            return err
        return {}, HTTPStatus.NO_CONTENT

    # ------------------------------------------------------------------
    # Labels
    # ------------------------------------------------------------------

    def get_waybill_label_bytes(
        self,
        credentials: OrlenPaczkaCredentials,
        waybill_numbers: list[str],
        _args: dict | None = None,
    ) -> tuple[bytes | str, int]:
        """Retrieve label PDF via LabelPrintDuplicateList.

        Only supports single waybill per request.
        """
        if len(waybill_numbers) != 1:
            raise NotImplementedError(
                f"Batch label retrieval not supported — fetch labels individually: {waybill_numbers}"
            )

        array_of_string_type = self.client.get_type("ns0:ArrayOfString")
        payload = {
            "PartnerID": credentials.partner_id,
            "PartnerKey": credentials.partner_key,
            "PackCodeList": array_of_string_type(waybill_numbers),
            "Format": "PDF",
        }
        status_extraction_func: Callable = (
            lambda r: r.LabelPrintDuplicateListResult._value_1._value_1[0].get(
                "LabelPrintDuplicateList"
            )
        )

        try:
            response = self.client.service.LabelPrintDuplicateList(**payload)
        except TransportError as e:
            logger.exception("LabelPrintDuplicateList transport error: %s", e.message)
            return e.content, e.status_code
        except Fault as e:
            logger.exception("LabelPrintDuplicateList fault: %s", e.message)
            return e.code, HTTPStatus.BAD_REQUEST

        status = status_extraction_func(response)
        error_code = int(status.Err)

        if error_code not in OrlenPaczkaReturnCodes.success_codes():
            if error_code == OrlenPaczkaReturnCodes.MISSING_ROUTING_DATA_FOR_LABEL.value[0]:
                msg = (
                    "No routing data from OrlenPaczka: possibly too early or non-existent parcel. "
                    "Data is usually available after a few dozen seconds."
                )
                logger.warning(msg)
                return msg, HTTPStatus.NOT_FOUND
            return status.ErrDes, HTTPStatus.BAD_REQUEST

        return response.LabelData, HTTPStatus.OK

    # ------------------------------------------------------------------
    # Pickup points
    # ------------------------------------------------------------------

    def get_points(
        self,
        credentials: OrlenPaczkaCredentials,
    ) -> tuple[object, int]:
        """Get all RUCH pickup points via GiveMeAllRUCHWithFilled."""
        response, err = self._call_service(
            "GiveMeAllRUCHWithFilled",
            extract=lambda r: r,
            PartnerID=credentials.partner_id,
            PartnerKey=credentials.partner_key,
        )
        if err:
            return err

        return wsdl_to_json(response.Data)["PointPwR"], HTTPStatus.OK

    # ------------------------------------------------------------------
    # Private — build create order dict
    # ------------------------------------------------------------------

    def _get_create_order_dict(
        self,
        credentials: OrlenPaczkaCredentials,
        command: CreateOrderCommand,
    ) -> dict:
        orlenpaczka_extras: dict = command.extras.get("orlenpaczka", {})
        shipper = command.shipper
        receiver = command.receiver
        is_return = orlenpaczka_extras.get("return_pack")

        cod_transfer_description: str = orlenpaczka_extras.get(
            "cod_description",
            settings.orlen_paczka_cod_transfer_message.format(content=command.content),
        )
        cod_transfer_description = "".join(ch for ch in cod_transfer_description if ch.isalnum())

        destination_code = orlenpaczka_extras.get("custom_attributes", {}).get("target_point")
        box_size = command.parcels[0].parcel_type if command.parcels else "A"

        order_number = ""
        if command.content:
            order_number = command.content[:30] if len(command.content) > 30 else command.content

        create_order_dict: dict = {
            "PartnerID": credentials.partner_id,
            "PartnerKey": credentials.partner_key,
            "DestinationCode": destination_code,
            "BoxSize": box_size,
            "SenderFirstName": shipper.first_name,
            "SenderLastName": shipper.last_name,
            "SenderEMail": shipper.email,
            "SenderStreetName": shipper.street,
            "SenderBuildingNumber": shipper.building_number,
            "SenderCity": shipper.city,
            "SenderPostCode": shipper.postal_code,
            "SenderPhoneNumber": shipper.phone,
            "FirstName": receiver.first_name,
            "LastName": receiver.last_name,
            "EMail": receiver.email,
            "StreetName": receiver.street,
            "BuildingNumber": receiver.building_number,
            "City": receiver.city,
            "PostCode": receiver.postal_code,
            "PhoneNumber": receiver.phone,
            "PrintAdress": "1",
            "CashOnDelivery": command.cod,
            "AmountCashOnDelivery": int(command.cod_value * 100),
            "TransferDescription": cod_transfer_description,
            "Insurance": orlenpaczka_extras.get("insurance"),
            "SenderOrders": order_number,
        }

        if is_return:
            create_order_dict["ReturnPack"] = "T"
            create_order_dict["ReturnAvailable"] = "T"
            create_order_dict["ReturnQuantity"] = sum(p.quantity for p in command.parcels)
            create_order_dict["ReturnFirstName"] = shipper.first_name
            create_order_dict["ReturnLastName"] = shipper.last_name
            create_order_dict["ReturnEMail"] = shipper.email
            create_order_dict["ReturnStreetName"] = shipper.street
            create_order_dict["ReturnBuildingNumber"] = shipper.building_number
            create_order_dict["ReturnCity"] = shipper.city
            create_order_dict["ReturnPostCode"] = shipper.postal_code
            create_order_dict["ReturnPhoneNumber"] = shipper.phone
            create_order_dict["ReturnCompanyName"] = shipper.company_name
            create_order_dict["PrintAdress"] = "2"

        return create_order_dict

    # ------------------------------------------------------------------
    # Private — normalisation helpers
    # ------------------------------------------------------------------

    def _normalize_order_item(
        self,
        command: CreateOrderCommand,
        waybill_number: str,
    ) -> CreateOrderResponse:
        return CreateOrderResponse(
            id=waybill_number,
            waybill_number=waybill_number,
            receiver=self._normalize_shipment_party(command.receiver),
            shipper=self._normalize_shipment_party(command.shipper),
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
        extract: Callable[[object], object] | None = None,
        *args: object,
        **kwargs: object,
    ) -> tuple[object | None, None | tuple[str, int]]:
        """Wrapper for Orlen Paczka SOAP calls with error classification.

        Uses custom extraction functions because Orlen Paczka returns
        irregular nested response structures.
        """
        if extract is None:
            extract = lambda r: r._value_1._value_1[0].get(method)

        try:
            response = getattr(self.client.service, method)(*args, **kwargs)
        except TransportError as e:
            logger.exception("SOAP transport error on %s: %s", method, e.message)
            return None, (e.content, e.status_code)
        except Fault as e:
            logger.exception("SOAP fault on %s: %s", method, e.message)
            return None, (e.code, HTTPStatus.BAD_REQUEST)

        result = extract(response)
        if "Err" not in result:
            return result, None

        error_code = int(result.Err)

        if error_code in OrlenPaczkaReturnCodes.success_codes():
            return result, None
        if error_code in OrlenPaczkaReturnCodes.unauthorized_codes():
            logger.error("Unauthorized on %s: %s", method, result.ErrDes)
            return None, (result.ErrDes, HTTPStatus.UNAUTHORIZED)

        logger.error("Error on %s: %s", method, result.ErrDes)
        return None, (result.ErrDes, HTTPStatus.BAD_REQUEST)
