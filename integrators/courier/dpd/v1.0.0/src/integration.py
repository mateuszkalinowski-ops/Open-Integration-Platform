"""DPD Courier Integration — migrated from meriship codebase.

Handles all DPD SOAP API interactions including:
- Shipment creation (generatePackagesNumbersV4)
- Label retrieval (generateSpedLabelsV4)
- Shipment status tracking (getEventsForWaybillV1)
- Pickup booking (packagesPickupCallV4)
- Protocol generation (generateProtocolV2)
"""

from __future__ import annotations

import json
import logging
from http import HTTPStatus

from zeep import Client, Transport
from zeep.exceptions import Fault, TransportError
from zeep.helpers import serialize_object

from src.config import settings
from src.schemas import DpdCredentials, DpdInfoCredentials

logger = logging.getLogger("courier-dpd")


PAYER_TYPES = {
    "SHIPPER": "SENDER",
    "RECIPIENT": "RECEIVER",
    "USER": "THIRD_PARTY",
}

STATUS_MAP: dict[str, str] = {
    "HR_01": "Nadano",
    "HR_02": "W transporcie",
    "HR_03": "W doręczeniu",
    "HR_04": "Doręczono",
    "HR_05": "Awizo",
    "HR_06": "Zwrot",
    "HR_07": "Nieznany",
}


def wsdl_to_json(data: object) -> dict:
    """Convert a zeep SOAP response object to a JSON-serializable dict."""
    return json.loads(json.dumps(serialize_object(data)))


def unravel_parcels(parcels: list[dict]) -> list[dict]:
    """Expand parcels so each entry represents qty=1."""
    result: list[dict] = []
    for p in parcels:
        qty = p.get("quantity", 1)
        result.append(p)
        for _ in range(qty - 1):
            copy = dict(p)
            copy["quantity"] = 1
            result.append(copy)
    return result


class DpdIntegration:
    """DPD SOAP integration for both package services and info services APIs."""

    def __init__(self) -> None:
        transport = Transport(
            timeout=settings.soap_timeout,
            operation_timeout=settings.soap_operation_timeout,
        )
        self.client: Client | None = None
        self.info_client: Client | None = None

        try:
            self.client = Client(settings.dpd_wsdl_path, transport=transport)
            logger.info("SOAP client connected — %s", settings.dpd_wsdl_path)
        except ConnectionError:
            logger.error("SOAP client timeout — %s", settings.dpd_wsdl_path)
        except Exception:
            logger.exception("SOAP client init failed — %s", settings.dpd_wsdl_path)

        try:
            self.info_client = Client(settings.dpd_info_wsdl_path, transport=transport)
            logger.info("SOAP InfoService client connected — %s", settings.dpd_info_wsdl_path)
        except ConnectionError:
            logger.error("SOAP InfoService client timeout — %s", settings.dpd_info_wsdl_path)
        except Exception:
            logger.exception("SOAP InfoService client init failed — %s", settings.dpd_info_wsdl_path)

    # ------------------------------------------------------------------
    # Order status
    # ------------------------------------------------------------------

    def get_order_status(
        self,
        credentials: DpdCredentials,
        waybill_number: str,
        info_credentials: DpdInfoCredentials | None = None,
    ) -> tuple[str | dict, int]:
        """Retrieve the latest shipment status via ``getEventsForWaybillV1``."""
        auth_data = self._get_info_service_auth_data(credentials, info_credentials)

        try:
            response = self.info_client.service.getEventsForWaybillV1(
                waybill_number,
                "ONLY_LAST",
                "PL",
                auth_data,
            )
        except TransportError as exc:
            return exc.content, exc.status_code
        except Fault as exc:
            return exc.message, HTTPStatus.BAD_REQUEST

        if response is None:
            return "Brak danych", HTTPStatus.OK

        confirm_id = response.confirmId
        self._mark_events_as_processed(confirm_id, auth_data)
        status = response["return"]["eventsList"][0]["businessCode"]
        status = self.map_status(status)
        return status, HTTPStatus.OK

    # ------------------------------------------------------------------
    # Create shipment
    # ------------------------------------------------------------------

    def create_order(
        self,
        credentials: DpdCredentials,
        command: dict,
    ) -> tuple[dict | str, int]:
        """Create a DPD shipment.

        Steps:
        1. Generate package numbers via ``generatePackagesNumbersV4``
        2. Optionally book courier pickup via ``packagesPickupCallV4``
        3. Normalize and return the response
        """
        auth_data = self._get_auth_data(credentials)
        fid = auth_data.get("masterFid")

        response, status_code = self._create_order(auth_data, command, fid)

        if status_code != HTTPStatus.OK:
            return response, status_code

        dpd_extras = command.get("extras", {}).get("dpd", {})
        if dpd_extras.get("book_courier", True):
            pickup_response, pickup_code = self._packages_pickup_call(auth_data, command)
            if pickup_code != HTTPStatus.OK:
                return pickup_response, pickup_code

        return self._normalize_order(response, command), HTTPStatus.CREATED

    # ------------------------------------------------------------------
    # Labels
    # ------------------------------------------------------------------

    def get_waybill_label_bytes(
        self,
        credentials: DpdCredentials,
        waybill_numbers: list[str],
        args: dict,
    ) -> tuple[bytes | str, int]:
        """Retrieve label PDF bytes via ``generateSpedLabelsV4``."""
        auth_data = self._get_auth_data(credentials)
        package_id = args.get("external_id")

        dpd_services_params_v1 = self._get_dpd_services_params_v1(waybill_numbers, package_id)
        try:
            response = self.client.service.generateSpedLabelsV4(
                dpdServicesParamsV1=dpd_services_params_v1,
                outputDocFormatV1="PDF",
                outputDocPageFormatV1="LBL_PRINTER",
                outputLabelType="BIC3",
                labelVariant="",
                authDataV1=auth_data,
            )

            if response.session.statusInfo.status == "INCORRECT_PKGS_FOR_SESSION_TYPE":
                dpd_services_params_v1_international = self._get_dpd_services_params_v1(
                    waybill_numbers, package_id, session_type="INTERNATIONAL",
                )
                response = self.client.service.generateSpedLabelsV4(
                    dpdServicesParamsV1=dpd_services_params_v1_international,
                    outputDocFormatV1="PDF",
                    outputDocPageFormatV1="LBL_PRINTER",
                    outputLabelType="BIC3",
                    labelVariant="",
                    authDataV1=auth_data,
                )

        except TransportError as exc:
            return exc.content, exc.status_code
        except Fault as exc:
            return exc.message, HTTPStatus.BAD_REQUEST

        if response is None:
            return "Brak danych", HTTPStatus.OK

        status_code = (
            HTTPStatus.OK
            if response.session.statusInfo.status == "OK"
            else HTTPStatus.BAD_REQUEST
        )
        if status_code != HTTPStatus.OK:
            return (
                f"Generate sped label error: {response.session.statusInfo.status}, "
                f"description: {response.session.statusInfo.description}"
            ), status_code

        return response.documentData, status_code

    # ------------------------------------------------------------------
    # Protocol generation
    # ------------------------------------------------------------------

    def generate_protocol(
        self,
        credentials: DpdCredentials,
        waybill_numbers: list[str],
        session_type: str = "DOMESTIC",
    ) -> tuple[bytes | str, int]:
        """Generate pickup protocol PDF via ``generateProtocolV2``."""
        auth_data = self._get_auth_data(credentials)
        fid = auth_data["masterFid"]

        if session_type:
            service_params = self._get_dpd_services_params_v1(
                waybill_numbers=waybill_numbers, fid=fid, package_id=None,
                session_type=session_type,
            )
        else:
            service_params = self._get_dpd_services_params_v1(
                waybill_numbers=waybill_numbers, fid=fid, package_id=None,
            )

        try:
            response = self.client.service.generateProtocolV2(
                dpdServicesParamsV1=service_params,
                outputDocFormatV1="PDF",
                outputDocPageFormatV1="A4",
                authDataV1=auth_data,
            )
        except TransportError as exc:
            return exc.content, exc.status_code
        except Fault as exc:
            return exc.message, HTTPStatus.BAD_REQUEST

        if response is None:
            return "Brak danych", HTTPStatus.OK

        status_code = (
            HTTPStatus.OK
            if response.session.statusInfo.status == "OK"
            else HTTPStatus.BAD_REQUEST
        )
        if status_code != HTTPStatus.OK:
            return (
                f"Generate protocol error: {response.session.statusInfo.status}, "
                f"description: {response.session.statusInfo.description}"
            ), status_code

        return response.documentData, status_code

    # ------------------------------------------------------------------
    # Status mapping
    # ------------------------------------------------------------------

    @staticmethod
    def map_status(status: str) -> str:
        """Map a DPD business code to a human-readable status."""
        return STATUS_MAP.get(status, status)

    # ------------------------------------------------------------------
    # Private — create order (SOAP call)
    # ------------------------------------------------------------------

    def _create_order(
        self,
        auth_data: dict,
        command: dict,
        fid: int | None,
    ) -> tuple[dict | str, int]:
        """Execute the raw SOAP ``generatePackagesNumbersV4`` call."""
        open_uml = self._get_open_uml_v3(command, fid)
        try:
            response = self.client.service.generatePackagesNumbersV4(
                openUMLFeV3=open_uml,
                pkgNumsGenerationPolicyV1="ALL_OR_NOTHING",
                langCode="PL",
                authDataV1=auth_data,
            )
        except TransportError as exc:
            return exc.content, exc.status_code
        except Fault as exc:
            return exc.message, HTTPStatus.BAD_REQUEST

        if response is None:
            return "Brak danych", HTTPStatus.OK

        if response.Status == "OK":
            status_code = HTTPStatus.OK
        else:
            status_code = HTTPStatus.BAD_REQUEST
            response = self._format_error(response)
        return wsdl_to_json(response), status_code

    # ------------------------------------------------------------------
    # Private — build openUML structure
    # ------------------------------------------------------------------

    def _get_open_uml_v3(self, command: dict, fid: int | None) -> dict:
        """Assemble the openUML dict expected by the DPD SOAP API."""
        shipper = command.get("shipper", {})
        receiver = command.get("receiver", {})
        parcels = command.get("parcels", [])
        content = command.get("content", "")
        cod = command.get("cod", False)
        cod_value = command.get("codValue", command.get("cod_value", 0))
        cod_curr = command.get("cod_curr", "PLN")

        dpd_extras: dict = command.get("extras", {}).get("dpd", {})
        payer_type = self._map_payer_type(command.get("payment", {}).get("payer_type", "SHIPPER"))

        guarantee = None
        if dpd_extras.get("delivery9"):
            guarantee = {"type": "TIME0930"}
        elif dpd_extras.get("delivery12"):
            guarantee = {"type": "TIME1200"}
        elif dpd_extras.get("delivery_saturday"):
            guarantee = {"type": "SATURDAY"}

        receiver_company = receiver.get("company_name", "")
        if receiver_company and len(receiver_company) > 100:
            receiver_company = receiver_company[:100]

        target_point = self._get_target_point_from_extras(dpd_extras)

        unraveled = unravel_parcels(parcels)

        return {
            "packages": [
                {
                    "parcels": [
                        {
                            "reference": None,
                            "weight": p.get("weight", 0),
                            "sizeX": p.get("length", 0),
                            "sizeY": p.get("width", 0),
                            "sizeZ": p.get("height", 0),
                            "content": content,
                            "customerData1": p.get("parcel_type", p.get("type", "PACKAGE")),
                        }
                        for p in unraveled
                    ],
                    "payerType": payer_type,
                    "receiver": {
                        "address": f"{receiver.get('street', '')} {receiver.get('building_number', '')}",
                        "city": receiver.get("city", ""),
                        "company": receiver_company,
                        "countryCode": receiver.get("country_code", "PL"),
                        "email": receiver.get("email", ""),
                        "fid": fid if payer_type == "RECEIVER" else None,
                        "name": f"{receiver.get('first_name', '')} {receiver.get('last_name', '')}",
                        "phone": receiver.get("phone", ""),
                        "postalCode": self._strip_postcode(receiver.get("postal_code", "")),
                    },
                    "reference": content,
                    "ref1": content,
                    "sender": {
                        "address": f"{shipper.get('street', '')} {shipper.get('building_number', '')}",
                        "city": shipper.get("city", ""),
                        "company": shipper.get("company_name", ""),
                        "countryCode": shipper.get("country_code", "PL"),
                        "email": shipper.get("email", ""),
                        "fid": fid if payer_type == "SENDER" else None,
                        "name": f"{shipper.get('first_name', '')} {shipper.get('last_name', '')}",
                        "phone": shipper.get("phone", ""),
                        "postalCode": self._strip_postcode(shipper.get("postal_code", "")),
                    },
                    "services": {
                        "cod": {"amount": cod_value, "currency": cod_curr} if cod else None,
                        "declaredValue": {
                            "amount": dpd_extras.get("insurance_value"),
                            "currency": dpd_extras.get("insurance_curr", "PLN"),
                        }
                        if dpd_extras.get("insurance")
                        else None,
                        "dpdPickup": {"pudo": target_point} if target_point else None,
                        "duty": {
                            "amount": dpd_extras.get("duty"),
                            "currency": cod_curr,
                        }
                        if dpd_extras.get("duty")
                        else None,
                        "cud": {} if dpd_extras.get("return_pack") else None,
                        "carryIn": {} if dpd_extras.get("bringing_pack") else None,
                        "rod": {} if dpd_extras.get("rod") else None,
                        "guarantee": guarantee,
                        "inPers": dpd_extras.get("in_pers"),
                        "pallet": dpd_extras.get("pallet") if dpd_extras.get("pallet") else None,
                        "privPers": dpd_extras.get("priv_pers") if dpd_extras.get("priv_pers") else None,
                    },
                    "thirdPartyFID": fid if payer_type == "THIRD_PARTY" else None,
                },
            ],
        }

    # ------------------------------------------------------------------
    # Private — pickup call
    # ------------------------------------------------------------------

    def _packages_pickup_call(
        self,
        auth_data: dict,
        command: dict,
    ) -> tuple[dict | str, int]:
        """Book a courier pickup via ``packagesPickupCallV4``."""
        dpd_pickup_params = self._get_dpd_pickup_params(command, auth_data["masterFid"])
        try:
            response = self.client.service.packagesPickupCallV4(
                dpdPickupParamsV3=dpd_pickup_params,
                authDataV1=auth_data,
            )
        except TransportError as exc:
            return exc.content, exc.status_code
        except Fault as exc:
            return exc.message, HTTPStatus.BAD_REQUEST

        if response is None:
            return "Brak danych", HTTPStatus.OK

        if response.statusInfo.status == "OK":
            status_code = HTTPStatus.OK
        else:
            status_code = HTTPStatus.BAD_REQUEST
            response = self._format_error(response)
        return wsdl_to_json(response), status_code

    def _get_dpd_pickup_params(self, command: dict, fid: int | None) -> dict:
        """Build the pickup call structure."""
        extras_dpd = command.get("extras", {}).get("dpd", {})
        parcels = command.get("parcels", [])
        shipper = command.get("shipper", {})
        receiver = command.get("receiver", {})

        parcel_count = sum(p.get("quantity", 1) for p in parcels)

        return {
            "orderType": "DOMESTIC",
            "operationType": "INSERT",
            "pickupDate": extras_dpd["pickup_date"],
            "pickupTimeFrom": extras_dpd["pickup_time_from"],
            "pickupTimeTo": extras_dpd["pickup_time_to"],
            "waybillsReady": "true",
            "pickupCallSimplifiedDetails": {
                "pickupCustomer": {
                    "customerFullName": receiver.get("contact_person", ""),
                    "customerName": receiver.get("contact_person", ""),
                    "customerPhone": receiver.get("phone", ""),
                },
                "packagesParams": {
                    "dox": "false",
                    "doxCount": 0,
                    "pallet": "false",
                    "palletsCount": 0,
                    "standardParcel": "true",
                    "parcelsCount": parcel_count,
                },
                "pickupPayer": {
                    "payerName": shipper.get("contact_person", ""),
                    "payerNumber": fid,
                },
                "pickupSender": {
                    "senderAddress": f"{shipper.get('street', '')} {shipper.get('building_number', '')}",
                    "senderCity": shipper.get("city", ""),
                    "senderFullName": shipper.get("contact_person", ""),
                    "senderName": f"{shipper.get('first_name', '')} {shipper.get('last_name', '')}",
                    "senderPhone": shipper.get("phone", ""),
                    "senderPostalCode": self._strip_postcode(shipper.get("postal_code", "")),
                },
            },
        }

    # ------------------------------------------------------------------
    # Private — authentication
    # ------------------------------------------------------------------

    @staticmethod
    def _get_auth_data(credentials: DpdCredentials) -> dict:
        master_fid = credentials.master_fid
        return {
            "login": credentials.login,
            "password": credentials.password,
            "masterFid": master_fid,
        }

    @staticmethod
    def _get_info_service_auth_data(
        credentials: DpdCredentials,
        info_credentials: DpdInfoCredentials | None = None,
    ) -> dict:
        if info_credentials:
            return {
                "login": info_credentials.login,
                "password": info_credentials.password,
                "channel": info_credentials.channel,
            }
        return {
            "login": credentials.login,
            "password": credentials.password,
            "channel": "",
        }

    # ------------------------------------------------------------------
    # Private — services params
    # ------------------------------------------------------------------

    @staticmethod
    def _get_dpd_services_params_v1(
        waybill_numbers: list[str],
        package_id: str | None = None,
        fid: int | None = None,
        session_type: str = "DOMESTIC",
    ) -> dict:
        return {
            "policy": "STOP_ON_FIRST_ERROR",
            "pickupAddress": {"fid": fid} if fid else None,
            "session": {
                "packages": [
                    {
                        "packageId": package_id if package_id else None,
                        "parcels": [
                            {"waybill": waybill}
                            for waybill in waybill_numbers
                        ],
                    },
                ],
                "sessionType": session_type,
            },
        }

    # ------------------------------------------------------------------
    # Private — event processing
    # ------------------------------------------------------------------

    def _mark_events_as_processed(self, confirm_id: object, auth_data: dict) -> None:
        try:
            self.info_client.service.markEventsAsProcessedV1(confirm_id, auth_data)
        except Exception:
            logger.warning("Failed to mark events as processed for confirm_id=%s", confirm_id)

    # ------------------------------------------------------------------
    # Private — normalisation
    # ------------------------------------------------------------------

    def _normalize_order(self, response: dict, command: dict) -> dict:
        """Build a normalised response from generatePackagesNumbersV4 result."""
        package = response.get("Packages", {}).get("Package", [{}])[0]
        parcel = package.get("Parcels", {}).get("Parcel", [{}])[0]
        waybill = parcel.get("Waybill", "")
        package_id = package.get("PackageId", "")

        shipper = command.get("shipper", {})
        receiver = command.get("receiver", {})

        return {
            "id": package_id,
            "waybill_number": waybill,
            "shipper": self._normalize_shipment_party(shipper),
            "receiver": self._normalize_shipment_party(receiver),
            "orderStatus": package.get("Status", ""),
        }

    @staticmethod
    def _normalize_shipment_party(party: dict) -> dict:
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
    def _strip_postcode(postcode: str) -> str:
        return postcode.replace("-", "")

    @staticmethod
    def _map_payer_type(payer_type: str) -> str:
        return PAYER_TYPES.get(payer_type, payer_type)

    @staticmethod
    def _get_target_point_from_extras(extras: dict) -> str | None:
        target_point = extras.get("custom_attributes", {}).get("target_point")
        if target_point == "0":
            return None
        return target_point

    @staticmethod
    def _format_error(response: object) -> dict:
        return {"detail": response}
