"""Packeta Courier Integration — migrated from meriship codebase.

Handles all Packeta SOAP API interactions including:
- Packet creation via createPacket (with PP courier mode detection)
- Packet status via packetStatus
- Label generation via packetLabelPdf / packetsCourierLabelsPdf
- Courier number retrieval via packetCourierNumberV2
- Packet cancellation via cancelPacket
"""

from __future__ import annotations

import json
import logging
from http import HTTPStatus

from zeep import Client, Transport
from zeep.exceptions import Fault, TransportError
from zeep.helpers import serialize_object

from src.config import settings
from src.schemas import CreateOrderCommand, PacketaCredentials

logger = logging.getLogger("courier-packeta")

PP_COURIER_IDS: set[str] = {
    "3060",
    "3616",
    "4017",
    "4307",
    "4539",
    "4635",
    "4654",
    "4656",
    "4826",
    "4828",
    "4994",
    "5061",
    "5062",
    "5064",
    "5066",
    "6828",
    "7455",
    "7910",
    "8001",
    "9104",
    "10619",
    "12889",
    "14052",
    "17467",
    "18809",
    "19470",
    "19471",
    "19516",
    "19517",
    "20409",
    "25005",
    "25985",
    "25987",
    "25988",
    "25989",
    "25990",
    "25992",
    "26067",
    "26986",
    "26987",
    "27955",
    "29760",
}


def wsdl_to_json(data: object) -> dict:
    """Convert a zeep SOAP response object to a JSON-serializable dict."""
    return json.loads(json.dumps(serialize_object(data)))


class PacketaIntegration:
    """Packeta SOAP integration.

    https://docs.packetery.com/03-creating-packets/05-api-description.html
    """

    def __init__(self) -> None:
        transport = Transport(timeout=settings.soap_timeout)
        self.client: Client | None = None

        try:
            self.client = Client(settings.packeta_api_wsdl, transport=transport)
            logger.info("SOAP client connected — %s", settings.packeta_api_wsdl)
        except ConnectionError:
            logger.error("SOAP client timeout — %s", settings.packeta_api_wsdl)
        except Exception:
            logger.exception("SOAP client init failed — %s", settings.packeta_api_wsdl)

    @staticmethod
    def _is_pp_courier(courier_id: str) -> bool:
        return courier_id in PP_COURIER_IDS

    @staticmethod
    def _normalize_shipment_party(party) -> dict:
        street = getattr(party, "street", "") or ""
        building = getattr(party, "building_number", "") or ""
        postal = getattr(party, "postal_code", "") or ""
        city = getattr(party, "city", "") or ""
        country = getattr(party, "country_code", "PL") or "PL"
        return {
            "first_name": getattr(party, "first_name", "") or "",
            "last_name": getattr(party, "last_name", "") or "",
            "contact_person": getattr(party, "contact_person", "") or "",
            "phone": getattr(party, "phone", "") or "",
            "email": getattr(party, "email", "") or "",
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
    # Order status
    # ------------------------------------------------------------------

    def get_order_status(
        self,
        credentials: PacketaCredentials,
        waybill_number: str,
    ) -> tuple[str, int]:
        """Get packet status via packetStatus SOAP call."""
        command = {
            "apiPassword": credentials.api_password,
            "packetId": waybill_number,
        }

        try:
            response = self.client.service.packetStatus(**command)
        except TransportError as exc:
            return exc.content, exc.status_code
        except Fault as exc:
            return exc.message, HTTPStatus.BAD_REQUEST

        if response is None:
            return "Brak danych", HTTPStatus.OK

        status = response["codeText"]
        return status, HTTPStatus.OK

    # ------------------------------------------------------------------
    # Create order
    # ------------------------------------------------------------------

    def create_order(
        self,
        credentials: PacketaCredentials,
        command: CreateOrderCommand,
    ) -> tuple[object, int]:
        """Create a packet via createPacket SOAP call.

        Detects PP courier mode based on service_name matching PP_COURIER_IDS.
        Extracts validation errors from Fault attribute details.
        """
        is_pp_courier = self._is_pp_courier(command.service_name)
        create_command = self._prepare_packeta_command(
            command,
            credentials.api_password,
            credentials.eshop,
            is_pp_courier,
        )

        try:
            response = self.client.service.createPacket(**create_command)
        except TransportError as exc:
            return exc.content, exc.status_code
        except Fault as exc:
            error_message = exc.message
            try:
                logger.info("Packeta validation errors:")
                for f in (
                    self.client.wsdl.types.deserialize(exc.detail[0])
                    .__getattribute__("attributes")
                    .__getattribute__("fault")
                ):
                    error_message = error_message + f["fault"]
                    logger.info(f)
            except Exception:
                logger.info("Problem during attribute validation for Packeta")
            return error_message, HTTPStatus.BAD_REQUEST

        if response is None:
            return "Brak danych", HTTPStatus.OK

        response_formatted = wsdl_to_json(response)

        status_code = HTTPStatus.BAD_REQUEST
        if response_formatted.get("id"):
            status_code = HTTPStatus.OK

        if status_code != HTTPStatus.OK:
            return response_formatted, status_code

        if is_pp_courier:
            normalized = self._normalize_order(response_formatted, command)
            normalized["order_id"] = "pp_courier" + str(response_formatted["id"])
            return normalized, HTTPStatus.CREATED

        return self._normalize_order(response_formatted, command), HTTPStatus.CREATED

    # ------------------------------------------------------------------
    # Labels
    # ------------------------------------------------------------------

    def get_waybill_label_bytes(
        self,
        credentials: PacketaCredentials,
        waybill_numbers: list[str],
        external_id: str | None = None,
    ) -> tuple[bytes | str, int]:
        """Retrieve label bytes.

        Uses packetLabelPdf for standard packets.
        Uses packetsCourierLabelsPdf when external_id (courier number) differs from packet ID.
        Retrieves courier number via packetCourierNumberV2 when external_id contains 'pp_courier'.
        """
        password = credentials.api_password
        package_id = waybill_numbers[0]

        resolved_external_id = None
        if external_id and "pp_courier" in external_id:
            resolved_external_id = self._get_response_with_external_id(password, package_id)

        return self._generate_labels(password, package_id, resolved_external_id)

    # ------------------------------------------------------------------
    # Delete order
    # ------------------------------------------------------------------

    def delete_order(
        self,
        credentials: PacketaCredentials,
        waybill_number: str,
        _data: dict | None = None,
    ) -> tuple[object, int]:
        """Cancel a packet via cancelPacket SOAP call."""
        try:
            response = self.client.service.cancelPacket(
                apiPassword=credentials.api_password,
                packetId=waybill_number,
            )
        except TransportError as exc:
            return exc.content, exc.status_code
        except Fault as exc:
            return exc.message, HTTPStatus.NOT_FOUND

        if response is None:
            return "Brak danych", HTTPStatus.NO_CONTENT
        if response["result"]:
            return wsdl_to_json(response), HTTPStatus.OK
        return wsdl_to_json(response), HTTPStatus.BAD_REQUEST

    # ------------------------------------------------------------------
    # Private — prepare command
    # ------------------------------------------------------------------

    def _prepare_packeta_command(
        self,
        command: CreateOrderCommand,
        password: str,
        eshop: str,
        is_pp_courier: bool,
    ) -> dict:
        """Build the SOAP createPacket payload.

        Handles three modes:
        - PP courier: uses addressId = service_name, carrierPickupPoint = target_point
        - Target point: uses addressId = target_point
        - Direct address: includes full street/city/zip
        """
        packeta_extras: dict = command.extras.get("packeta", {})
        cod_value: float = 0
        cod = command.cod

        if cod:
            cod_value = command.cod_value

        currency = "EUR"
        if cod and command.cod_curr:
            currency = command.cod_curr
        elif (
            packeta_extras.get("insurance")
            and packeta_extras.get("insurance_value")
            and packeta_extras["insurance_value"] > 0
        ):
            currency = packeta_extras.get("insurance_curr", "EUR")

        target_point = None
        custom_attrs = packeta_extras.get("custom_attributes", {})
        if custom_attrs and custom_attrs.get("target_point"):
            target_point = custom_attrs["target_point"]

        receiver = command.receiver

        value: float = 0
        if cod and cod_value > 0:
            value = cod_value
        elif (
            packeta_extras.get("insurance")
            and packeta_extras.get("insurance_value")
            and packeta_extras["insurance_value"] > 0
        ):
            value = packeta_extras["insurance_value"]

        receiver_company = receiver.company_name
        if receiver.company_name and len(receiver.company_name) > 100:
            receiver_company = receiver.company_name[:100]

        weight: float = 0
        for parcel in command.parcels:
            if parcel.weight and parcel.weight > 0:
                weight += parcel.weight

        number = command.doc_id
        if command.content and len(command.content) > 0:
            number = command.content

        postal_code = receiver.postal_code
        if postal_code:
            postal_code = postal_code.replace("-", "")

        packet = command.parcels[0] if command.parcels else None
        size = {}
        if packet:
            size = {
                "length": packet.length * 10,
                "width": packet.width * 10,
                "height": packet.height * 10,
            }

        if is_pp_courier:
            return {
                "apiPassword": password,
                "attributes": {
                    "number": number,
                    "name": receiver.first_name,
                    "surname": receiver.last_name,
                    "company": receiver_company,
                    "email": receiver.email,
                    "phone": receiver.phone,
                    "addressId": command.service_name,
                    "cod": cod_value,
                    "currency": currency,
                    "value": value,
                    "weight": weight,
                    "eshop": eshop,
                    "note": command.content,
                    "carrierPickupPoint": target_point,
                    "size": size,
                },
            }
        elif target_point:
            return {
                "apiPassword": password,
                "attributes": {
                    "number": number,
                    "name": receiver.first_name,
                    "surname": receiver.last_name,
                    "company": receiver_company,
                    "email": receiver.email,
                    "phone": receiver.phone,
                    "addressId": target_point,
                    "cod": cod_value,
                    "currency": currency,
                    "value": value,
                    "weight": weight,
                    "eshop": eshop,
                    "note": command.content,
                    "size": size,
                },
            }
        else:
            return {
                "apiPassword": password,
                "attributes": {
                    "number": number,
                    "name": receiver.first_name,
                    "surname": receiver.last_name,
                    "company": receiver_company,
                    "email": receiver.email,
                    "phone": receiver.phone,
                    "addressId": command.service_name,
                    "cod": cod_value,
                    "currency": currency,
                    "value": value,
                    "weight": weight,
                    "eshop": eshop,
                    "note": command.content,
                    "street": receiver.street,
                    "houseNumber": receiver.building_number,
                    "city": receiver.city,
                    "zip": postal_code,
                    "size": size,
                },
            }

    # ------------------------------------------------------------------
    # Private — label generation
    # ------------------------------------------------------------------

    def _generate_labels(
        self,
        password: str,
        package_id: str,
        external_id: str | None,
    ) -> tuple[bytes | str, int]:
        """Generate labels using the appropriate SOAP method.

        packetLabelPdf for standard packets, packetsCourierLabelsPdf when
        an external courier number is available and differs from packet ID.
        """
        if not external_id or package_id == external_id:
            try:
                response = self.client.service.packetLabelPdf(
                    apiPassword=password,
                    packetId=package_id,
                    format="A6 on A6",
                    offset=0,
                )
            except TransportError as exc:
                return exc.content, exc.status_code
            except Fault as exc:
                return exc.message, HTTPStatus.BAD_REQUEST
        else:
            try:
                response = self.client.service.packetsCourierLabelsPdf(
                    apiPassword=password,
                    format="A6 on A6",
                    offset=0,
                    packetIdsWithCourierNumbers={
                        "packetIdWithCourierNumber": {
                            "courierNumber": external_id,
                            "packetId": package_id,
                        },
                    },
                )
            except TransportError as exc:
                return exc.content, exc.status_code
            except Fault as exc:
                return exc.message, HTTPStatus.BAD_REQUEST

        if not response:
            return "Generate label call returned error", HTTPStatus.BAD_REQUEST

        return response, HTTPStatus.OK

    # ------------------------------------------------------------------
    # Private — courier number retrieval
    # ------------------------------------------------------------------

    def _get_response_with_external_id(
        self,
        password: str,
        packeta_id: str,
    ) -> str | None:
        """Retrieve the external courier number via packetCourierNumberV2."""
        try:
            response_info = self.client.service.packetCourierNumberV2(
                apiPassword=password,
                packetId=packeta_id,
            )
        except TransportError:
            return None
        except Fault:
            return None

        response = wsdl_to_json(response_info)

        try:
            if response.get("courierNumber"):
                return response["courierNumber"]
        except Exception as exc:
            logger.info("Error retrieving internal courier number: %s", exc)

        return None

    # ------------------------------------------------------------------
    # Private — normalisation
    # ------------------------------------------------------------------

    def _normalize_order(
        self,
        response: dict,
        command: CreateOrderCommand,
    ) -> dict:
        waybill = response["id"]
        return {
            "id": response["id"],
            "waybill_number": str(waybill),
            "shipper": self._normalize_shipment_party(command.shipper),
            "receiver": self._normalize_shipment_party(command.receiver),
            "orderStatus": "CREATED",
        }
