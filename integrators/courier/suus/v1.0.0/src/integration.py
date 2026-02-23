"""Suus Courier Integration — migrated from meriship codebase.

Handles all Suus SOAP API interactions including:
- Order creation via addOrder (with auth structure)
- Error code extraction from raw XML elements
- Status tracking via getEvents
- Label retrieval via getDocument (labelA6, base64 decoded)
- COD (RohligCOD) and insurance (RohligUbezpieczenie3) services
- String truncation via return_shorten_value

https://cms.suus.com/uploads/documents-english/documentation-ws-wb-1-17-eng.pdf
"""

from __future__ import annotations

import base64
import json
import logging
from http import HTTPStatus

from zeep import Client, Settings as ZeepSettings, Transport
from zeep.exceptions import Fault, TransportError
from zeep.helpers import serialize_object

from src.config import settings
from src.schemas import CreateOrderCommand, SuusCredentials

logger = logging.getLogger("courier-suus")


def wsdl_to_json(data: object) -> dict:
    """Convert a zeep SOAP response object to a JSON-serializable dict."""
    return json.loads(json.dumps(serialize_object(data)))


def return_shorten_value(value: str, max_char_count: int) -> str:
    """Truncate string to max_char_count characters."""
    if not value:
        return ""
    return value if len(value) < max_char_count else value[:max_char_count]


class SuusIntegration:
    """Suus SOAP integration for freight/parcel shipments."""

    def __init__(self) -> None:
        transport = Transport(timeout=settings.soap_timeout)
        zeep_settings = ZeepSettings(strict=False, xml_huge_tree=True)
        self.client: Client | None = None

        try:
            self.client = Client(
                settings.suus_api_wsdl,
                settings=zeep_settings,
                transport=transport,
            )
            logger.info("SOAP client connected — %s", settings.suus_api_wsdl)
        except ConnectionError:
            logger.error("SOAP client timeout — %s", settings.suus_api_wsdl)
        except Exception:
            logger.exception("SOAP client init failed — %s", settings.suus_api_wsdl)

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

    @staticmethod
    def _get_auth(login: str, password: str) -> dict:
        return {
            "session": "",
            "login": login,
            "password": password,
        }

    # ------------------------------------------------------------------
    # Order status
    # ------------------------------------------------------------------

    def get_order_status(
        self,
        credentials: SuusCredentials,
        waybill_number: str,
    ) -> tuple[str, int]:
        """Get shipment status via getEvents SOAP call."""
        command = {
            "auth": self._get_auth(credentials.login, credentials.password),
            "shipments": [
                {
                    "shipmentNo": waybill_number,
                    "reference": "",
                },
            ],
        }

        try:
            response = self.client.service.getEvents(**command)
        except TransportError as exc:
            return exc.content, exc.status_code
        except Exception as exc:
            return str(exc), HTTPStatus.BAD_REQUEST

        shipments = response["shipments"]
        if len(shipments) > 0:
            events = shipments[0]["events"]
            if len(events) > 0:
                last_event = events[-1]
                return last_event["description"], HTTPStatus.OK

        return "UNKNOWN", HTTPStatus.OK

    # ------------------------------------------------------------------
    # Create order
    # ------------------------------------------------------------------

    def create_order(
        self,
        credentials: SuusCredentials,
        command: CreateOrderCommand,
    ) -> tuple[object, int]:
        """Create order via addOrder SOAP call.

        Extracts error codes from raw XML elements in the response when present.
        """
        create_command = self._prepare_suus_command(
            command, credentials.login, credentials.password,
        )

        response = None
        try:
            response = self.client.service.addOrder(**create_command)
        except Fault as exc:
            logger.error("SOAP Fault: %s", exc)
            return str(exc), HTTPStatus.BAD_REQUEST
        except TransportError as exc:
            return exc.content, exc.status_code
        except Exception as exc:
            logger.info("Errors during Suus order creation:")
            try:
                error_message = str(exc)
                logger.info(error_message)
                return error_message, HTTPStatus.BAD_REQUEST
            except Exception:
                logger.info("Problem during attribute validation for Suus")
            return "Error while creating shipment in Suus", HTTPStatus.BAD_REQUEST

        # Extract error codes from raw XML elements
        error_message = None
        if response and "_raw_elements" in response:
            raw_elements = response["_raw_elements"]
            for elem in raw_elements:
                if elem.tag.endswith("errorCodes"):
                    error_codes = elem.xpath(".//text()")
                    for er in error_codes:
                        if not error_message:
                            error_message = ""
                        error_message = error_message + er + " "

        try:
            if response and response["shipmentNo"]:
                return self._normalize_order(response, command), HTTPStatus.CREATED
            else:
                return error_message or "Unknown error", HTTPStatus.BAD_REQUEST
        except Exception as exc:
            error_msg = str(exc)
            logger.info(error_msg)
            return error_msg, HTTPStatus.BAD_REQUEST

    # ------------------------------------------------------------------
    # Labels
    # ------------------------------------------------------------------

    def get_waybill_label_bytes(
        self,
        credentials: SuusCredentials,
        waybill_numbers: list[str],
        _data: dict | None = None,
    ) -> tuple[bytes | str, int]:
        """Retrieve label via getDocument SOAP call (labelA6).

        Returns decoded base64 PDF bytes.
        """
        package_id = waybill_numbers[0]
        label_data, status_code = self._generate_labels(
            credentials.login, credentials.password, package_id,
        )

        if status_code == HTTPStatus.OK:
            return base64.b64decode(label_data), status_code

        return label_data, status_code

    # ------------------------------------------------------------------
    # Private — prepare command
    # ------------------------------------------------------------------

    def _prepare_suus_command(
        self,
        command: CreateOrderCommand,
        login: str,
        password: str,
    ) -> dict:
        """Build the SOAP addOrder payload.

        Includes auth structure, COD (RohligCOD) and insurance (RohligUbezpieczenie3)
        as additional services, and truncated string fields.
        """
        suus_extras: dict = command.extras.get("suus", {})
        order_type = "B2B"

        if suus_extras.get("order_type"):
            order_type = suus_extras["order_type"]

        cod = command.cod

        currency = "PLN"
        if cod and command.cod_curr:
            currency = command.cod_curr
        elif (
            suus_extras.get("insurance")
            and suus_extras.get("insurance_value")
            and suus_extras["insurance_value"] > 0
        ):
            currency = suus_extras.get("insurance_curr", "PLN")

        services: list[dict] = []

        if cod:
            cod_value = command.cod_value
            services.append({
                "symbol": "RohligCOD",
                "decimal1": cod_value,
            })

        shipper = command.shipper
        receiver = command.receiver

        if (
            suus_extras.get("insurance")
            and suus_extras.get("insurance_value")
            and suus_extras["insurance_value"] > 0
        ):
            value = suus_extras["insurance_value"]
            services.append({
                "symbol": "RohligUbezpieczenie3",
                "decimal1": value,
                "decimal2": 0,
                "varchar1": "PLN",
                "int01": 1,
            })

        packages: list[dict] = []
        for parcel in command.parcels:
            packages.append({
                "symbol": parcel.parcel_type,
                "quantity": parcel.quantity,
                "weightKg": parcel.weight,
                "lenghtCm": parcel.length,
                "widthCm": parcel.width,
                "heightCm": parcel.height,
            })

        receiver_name = return_shorten_value(
            (receiver.company_name or "") + " "
            + (receiver.first_name or "") + " "
            + (receiver.last_name or ""),
            100,
        )

        return {
            "auth": self._get_auth(login, password),
            "order": {
                "header": {
                    "reference": return_shorten_value(command.content, 50),
                    "loadingDate": command.shipment_date,
                    "currency": currency,
                    "orderType": order_type,
                    "descriptionOfGoods": return_shorten_value(command.content, 50),
                    "remarks": "",
                },
                "loadingAddress": {
                    "name": return_shorten_value(shipper.company_name or "", 100),
                    "street": return_shorten_value(shipper.street or "", 50),
                    "streetNo": return_shorten_value(shipper.building_number or "", 10),
                    "postCode": shipper.postal_code,
                    "city": return_shorten_value(shipper.city or "", 50),
                    "country": shipper.country_code,
                    "e-mail": shipper.email,
                    "mobilePhone": shipper.phone,
                    "person": shipper.contact_person,
                },
                "unloadingAddress": {
                    "name": receiver_name,
                    "street": return_shorten_value(receiver.street or "", 50),
                    "streetNo": return_shorten_value(receiver.building_number or "", 10),
                    "postCode": receiver.postal_code,
                    "city": return_shorten_value(receiver.city or "", 50),
                    "country": receiver.country_code,
                    "e-mail": receiver.email,
                    "mobilePhone": receiver.phone,
                    "person": receiver.contact_person,
                },
                "packages": packages,
                "additionalServices": services if len(services) > 0 else None,
            },
        }

    # ------------------------------------------------------------------
    # Private — label generation
    # ------------------------------------------------------------------

    def _generate_labels(
        self,
        login: str,
        password: str,
        package_id: str,
    ) -> tuple[str | bytes, int]:
        """Retrieve label via getDocument SOAP call with labelA6 format."""
        command = {
            "auth": self._get_auth(login, password),
            "document": "labelA6",
            "shipmentNo": package_id,
            "reference": "",
            "masterNo": "",
            "colliNo": [{"colliNo": ""}],
        }

        try:
            response = self.client.service.getDocument(**command)
        except TransportError as exc:
            return exc.content, exc.status_code
        except Exception as exc:
            return str(exc), HTTPStatus.BAD_REQUEST

        return response["document"], HTTPStatus.OK

    # ------------------------------------------------------------------
    # Private — normalisation
    # ------------------------------------------------------------------

    def _normalize_order(
        self,
        response: dict,
        command: CreateOrderCommand,
    ) -> dict:
        waybill = response["shipmentNo"]
        return {
            "id": response["shipmentNo"],
            "waybill_number": str(waybill),
            "shipper": self._normalize_shipment_party(command.shipper),
            "receiver": self._normalize_shipment_party(command.receiver),
            "orderStatus": "CREATED",
        }
