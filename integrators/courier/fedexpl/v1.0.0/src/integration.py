"""FedEx PL Courier Integration — migrated from meriship codebase.

Handles all FedEx PL SOAP API interactions including:
- Shipment creation (zapiszListV2)
- Label retrieval (wydrukujEtykiete)
- COD and insurance handling
- Full _prepare_fedex_command logic
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from http import HTTPStatus

from zeep import Client, Transport
from zeep.exceptions import Fault, TransportError
from zeep.helpers import serialize_object

from src.config import settings
from src.schemas import CreateOrderCommand, FedexPlCredentials

logger = logging.getLogger("courier-fedexpl")


def wsdl_to_json(data: object) -> dict:
    """Convert a zeep SOAP response object to a JSON-serializable dict."""
    return json.loads(json.dumps(serialize_object(data)))


class FedexPlIntegration:
    """FedEx PL SOAP integration."""

    def __init__(self) -> None:
        transport = Transport(
            timeout=settings.soap_timeout,
            operation_timeout=settings.soap_operation_timeout,
        )
        self.client: Client | None = None

        try:
            self.client = Client(settings.fedex_pl_wsdl, transport=transport)
            logger.info("SOAP client connected — %s", settings.fedex_pl_wsdl)
        except ConnectionError:
            logger.error("SOAP client timeout — %s", settings.fedex_pl_wsdl)
        except Exception:
            logger.exception("SOAP client init failed — %s", settings.fedex_pl_wsdl)

    # ------------------------------------------------------------------
    # Create order
    # ------------------------------------------------------------------

    def create_order(
        self,
        credentials: FedexPlCredentials,
        command: CreateOrderCommand,
    ) -> tuple[dict | str, int]:
        """Create a shipment via zapiszListV2."""
        create_fedexpl_command = self._prepare_fedex_command(command, credentials)

        try:
            response = self.client.service.zapiszListV2(
                **create_fedexpl_command,
            )
        except TransportError as exc:
            return exc.content, exc.status_code
        except Fault as exc:
            error_message = exc.message
            try:
                logger.info("Błędy w walidacji FedexPl:")
                for f in (
                    self.client.wsdl.types.deserialize(exc.detail[0])
                    .__getattribute__("attributes")
                    .__getattribute__("fault")
                ):
                    error_message = error_message + f["fault"]
                    logger.info(f)
            except Exception:
                logger.info("Problem podczas walidacji atrybutow dla FedexPl")
            return error_message, HTTPStatus.BAD_REQUEST

        if response is None:
            return "Brak danych", HTTPStatus.OK

        response_formatted = wsdl_to_json(response)

        status_code = HTTPStatus.BAD_REQUEST
        if response_formatted.get("waybill"):
            status_code = HTTPStatus.OK

        if status_code != HTTPStatus.OK:
            return response_formatted, status_code

        return self._normalize_order(response_formatted, command), HTTPStatus.CREATED

    # ------------------------------------------------------------------
    # Order status (stub)
    # ------------------------------------------------------------------

    def get_order_status(
        self,
        credentials: FedexPlCredentials,
        waybill_number: str,
    ) -> tuple[str, int]:
        return "Brak statusu", HTTPStatus.OK

    # ------------------------------------------------------------------
    # Labels
    # ------------------------------------------------------------------

    def get_waybill_label_bytes(
        self,
        credentials: FedexPlCredentials,
        waybill_numbers: list[str],
        args: dict,
    ) -> tuple[bytes | str, int]:
        """Retrieve label PDF via wydrukujEtykiete."""
        package_id = waybill_numbers[0]

        get_label_command = {
            "kodDostepu": credentials.api_key,
            "numerPrzesylki": package_id,
            "format": "PDF",
        }

        try:
            response = self.client.service.wydrukujEtykiete(
                **get_label_command,
            )
        except TransportError as exc:
            return exc.content, exc.status_code
        except Fault as exc:
            return exc.message, HTTPStatus.BAD_REQUEST

        if not response:
            return "Generate sped label call returned error", HTTPStatus.BAD_REQUEST

        return response, HTTPStatus.OK

    # ------------------------------------------------------------------
    # Status mapping
    # ------------------------------------------------------------------

    @staticmethod
    def map_status(status: str) -> str:
        return status

    # ------------------------------------------------------------------
    # Private — build SOAP command
    # ------------------------------------------------------------------

    @staticmethod
    def _prepare_fedex_command(
        command: CreateOrderCommand,
        credentials: FedexPlCredentials,
    ) -> dict:
        """Build the full zapiszListV2 SOAP payload."""
        api_key = credentials.api_key
        client_id = credentials.client_id
        courier_number = credentials.courier_number
        account_number = credentials.account_number

        fedex_extras: dict = command.extras.get("fedex", {})

        cod_value: float = 0
        if command.cod:
            cod_value = command.cod_value

        shipper = command.shipper
        receiver = command.receiver

        pickup_date = datetime.strptime(
            command.shipment_date.split(" ")[0],
            "%Y-%m-%d",
        ).date()

        cod_field: dict | None = None
        insurance_field: dict | None = None
        description = False

        if command.cod and cod_value > 0:
            cod_field = {
                "codType": "B",
                "codValue": cod_value,
                "bankAccountNumber": account_number,
            }
            insurance_field = {
                "insuranceValue": cod_value,
                "contentDescription": command.content,
            }
            description = True
        else:
            cod_field = {
                "codType": "",
                "codValue": "",
                "bankAccountNumber": "",
            }

        if (
            fedex_extras.get("insurance")
            and fedex_extras.get("insurance_value")
            and fedex_extras.get("insurance_value") > 0
        ):
            insurance_field = {
                "insuranceValue": fedex_extras["insurance_value"],
                "contentDescription": command.content,
            }
            description = True

        parcels = []
        for parcel in command.parcels:
            single_parcel = {
                "type": parcel.parcel_type,
                "weight": parcel.weight,
                "dim1": round(parcel.length),
                "dim2": round(parcel.width),
                "dim3": round(parcel.height),
                "shape": "0",
            }
            parcels.append(single_parcel)

        parcels_formatted = {"parcel": parcels}

        return {
            "accessCode": api_key,
            "shipmentV2": {
                "paymentForm": "P",
                "shipmentType": "K",
                "payerType": "1",
                "sender": {
                    "senderId": client_id,
                    "contactDetails": {
                        "name": shipper.first_name,
                        "surname": shipper.last_name,
                        "phoneNo": shipper.phone,
                        "email": shipper.email,
                    },
                },
                "receiver": {
                    "addressDetails": {
                        "isCompany": 0,
                        "name": receiver.first_name,
                        "surname": receiver.last_name,
                        "city": receiver.city,
                        "postalCode": receiver.postal_code,
                        "countryCode": "PL",
                        "street": receiver.street,
                        "homeNo": receiver.building_number,
                    },
                    "contactDetails": {
                        "name": receiver.first_name,
                        "surname": receiver.last_name,
                        "phoneNo": receiver.phone,
                        "email": receiver.email,
                    },
                },
                "payer": {
                    "payerId": client_id,
                    "contactDetails": {
                        "name": shipper.first_name,
                        "surname": shipper.last_name,
                        "phoneNo": shipper.phone,
                        "email": shipper.email,
                    },
                },
                "proofOfDispatch": {
                    "senderSignature": shipper.company_name,
                    "courierId": courier_number,
                    "sendDate": pickup_date.strftime("%Y-%m-%d") + " 13:00",
                },
                "cod": cod_field,
                "insurance": insurance_field,
                "parcels": parcels_formatted,
                "remarks": "" if description else command.content,
            },
        }

    # ------------------------------------------------------------------
    # Private — normalise response
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_order(
        response: dict,
        command: CreateOrderCommand,
    ) -> dict:
        waybill = response["waybill"]
        return {
            "id": waybill,
            "waybill_number": waybill,
            "shipper": FedexPlIntegration._normalize_shipment_party_from_address(command.shipper),
            "receiver": FedexPlIntegration._normalize_shipment_party_from_address(command.receiver),
            "orderStatus": "CREATED",
        }

    @staticmethod
    def _normalize_shipment_party_from_address(party) -> dict:
        street = party.street
        building = party.building_number
        postal = party.postal_code
        city = party.city
        country = party.country_code
        return {
            "first_name": party.first_name,
            "last_name": party.last_name,
            "phone": party.phone,
            "email": party.email,
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
