"""UPS Courier Integration — migrated from meriship codebase.

Handles all UPS REST API interactions including:
- OAuth2 authentication (client_credentials grant)
- Shipment creation (multi-package, insurance, COD, international forms)
- Label retrieval with GIF→PDF conversion (rotation + img2pdf)
- Shipment status tracking
- Paperless document upload
"""

from __future__ import annotations

import base64
import functools
import logging
import os
from decimal import Decimal
from http import HTTPStatus
from io import BytesIO
from typing import Any

import httpx
import img2pdf
from PIL import Image

from src.config import settings
from src.schemas import (
    AddressResponse,
    CreateOrderResponse,
    CreateShipmentRequest,
    Parcel,
    RateProduct,
    RateRequest,
    ShipmentParty,
    ShipmentPartyResponse,
    StandardizedRateResponse,
    UpsCredentials,
    UpsExtras,
)

logger = logging.getLogger("courier-ups")


# ---------------------------------------------------------------------------
# Utility: unravel parcels (ported from app.integrations.utils)
# ---------------------------------------------------------------------------

def unravel_parcels(parcels: list[Parcel]) -> list[Parcel]:
    """Expand parcels with quantity > 1 into individual entries."""
    result: list[Parcel] = []
    for parcel in parcels:
        qty = parcel.quantity if parcel.quantity and parcel.quantity > 0 else 1
        for _ in range(qty):
            result.append(parcel.model_copy(update={"quantity": 1}))
    return result


# ---------------------------------------------------------------------------
# Async retry-with-token-refresh decorator
# ---------------------------------------------------------------------------

def retry_with_refresh_token(func):
    """Decorator that retries an async method after refreshing the OAuth2 token.

    Flow:
    1. Call the wrapped method.
    2. If 401 Unauthorized → call ``login()`` to get a fresh token.
    3. Retry the wrapped method once with the new token.
    """
    @functools.wraps(func)
    async def wrapper(self: "UpsIntegration", credentials: UpsCredentials, *args, **kwargs):
        result, status = await func(self, credentials, *args, **kwargs)
        if status != HTTPStatus.UNAUTHORIZED:
            return result, status

        logger.info("Received 401, attempting OAuth2 token refresh")
        login_result, login_status = await self.login(credentials)
        if login_status != HTTPStatus.OK:
            logger.warning("Token refresh failed with status %s", login_status)
            return result, status

        credentials.access_token = login_result["access_token"]
        return await func(self, credentials, *args, **kwargs)

    return wrapper


# ---------------------------------------------------------------------------
# Format REST error response (ported from Integration base)
# ---------------------------------------------------------------------------

async def _format_rest_error_response(response: httpx.Response) -> tuple[Any, int]:
    """Extract a meaningful error message from a UPS error response."""
    try:
        body = response.json()
        msg = body.get("message", "")
        if "Check details object for more info" in msg:
            msg = f'{msg} {body.get("details", "")}'
        if not msg:
            msg = str(body)
    except (ValueError, KeyError, AttributeError):
        msg = response.text
    logger.error("UPS API error %s: %s", response.url, msg)
    return msg, response.status_code


# ---------------------------------------------------------------------------
# UPS Integration
# ---------------------------------------------------------------------------

class UpsIntegration:
    """UPS REST API integration with OAuth2 authentication."""

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=settings.rest_timeout)

    # ------------------------------------------------------------------
    # OAuth2 login (client_credentials)
    # ------------------------------------------------------------------

    async def login(self, credentials: UpsCredentials) -> tuple[dict | str, int]:
        """Obtain an access token using client_credentials grant.

        ``credentials.login`` = client_id, ``credentials.password`` = client_secret.
        """
        url = f"{settings.base_url}/security/v1/oauth/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        payload = {"grant_type": "client_credentials"}

        response = await self._client.post(
            url,
            data=payload,
            headers=headers,
            auth=(credentials.login, credentials.password),
        )

        if response.status_code == HTTPStatus.OK:
            data = response.json()
            credentials.access_token = data.get("access_token", "")
            return {"access_token": credentials.access_token}, HTTPStatus.OK

        return await _format_rest_error_response(response)

    # ------------------------------------------------------------------
    # Shipment status
    # ------------------------------------------------------------------

    @retry_with_refresh_token
    async def get_order_status(
        self,
        credentials: UpsCredentials,
        waybill_number: str,
    ) -> tuple[Any, int]:
        """Retrieve shipment tracking status.

        https://developer.ups.com/api/reference?loc=en_PL#operation/getSingleTrackResponseUsingGET
        """
        url = f"{settings.base_url}/api/track/v1/details/{waybill_number}"
        headers = self._auth_headers(credentials)

        response = await self._client.get(url, headers=headers)

        status_code = response.status_code
        if status_code == HTTPStatus.MULTI_STATUS:
            status_code = HTTPStatus.NOT_FOUND

        if status_code != HTTPStatus.OK:
            return response.json(), status_code

        shipments = response.json()["shipment"]
        if len(shipments) != 1:
            return {"error": "Multishipment status not yet supported"}, HTTPStatus.NOT_IMPLEMENTED

        shipment_packages = shipments[0]["package"]
        if len(shipment_packages) != 1:
            return {"error": "Multipackage status not yet supported"}, HTTPStatus.NOT_IMPLEMENTED

        status_information = shipment_packages[0]["currentStatus"]["code"]
        return status_information, HTTPStatus.OK

    # ------------------------------------------------------------------
    # Create shipment
    # ------------------------------------------------------------------

    @retry_with_refresh_token
    async def create_order(
        self,
        credentials: UpsCredentials,
        command: CreateShipmentRequest,
    ) -> tuple[Any, int]:
        """Create a UPS shipment.

        https://developer.ups.com/api/reference?loc=en_PL#operation/Shipment
        """
        payload = self._get_create_package_payload(command, credentials)
        logger.info("UPS create order payload assembled")

        url = f"{settings.base_url}/api/shipments/{settings.ups_api_version}/ship"
        headers = self._auth_headers(credentials)

        response = await self._client.post(url, json=payload, headers=headers)

        if response.status_code == HTTPStatus.OK:
            shipment_response = response.json()["ShipmentResponse"]["ShipmentResults"]
            normalized = self._normalize_order_item(command, shipment_response)
            return normalized.model_dump(by_alias=True), HTTPStatus.CREATED

        return await _format_rest_error_response(response)

    # ------------------------------------------------------------------
    # Label retrieval (GIF → rotated PDF)
    # ------------------------------------------------------------------

    @retry_with_refresh_token
    async def get_waybill_label_bytes(
        self,
        credentials: UpsCredentials,
        waybill_numbers: list[str],
        _args: dict | None = None,
    ) -> tuple[bytes | Any, int]:
        """Retrieve label for the first waybill, convert GIF→PDF with 270° rotation."""
        waybill_number = waybill_numbers[0]

        url = f"{settings.base_url}/api/labels/{settings.ups_api_version}/recovery"
        payload = self._get_waybill_label_recovery_payload(waybill_number)
        headers = self._auth_headers(credentials)

        response = await self._client.post(url, json=payload, headers=headers)

        if response.status_code != HTTPStatus.OK:
            return await _format_rest_error_response(response)

        labels = response.json()["LabelRecoveryResponse"]["LabelResults"]
        encoded_waybills: list[str] = []

        try:
            if labels.get("LabelImage"):
                encoded_waybills.append(labels["LabelImage"]["GraphicImage"])
        except (TypeError, AttributeError):
            for label in labels:
                encoded_waybills.append(label["LabelImage"]["GraphicImage"])

        rotated_gif_bytes_list: list[bytes] = []
        for encoded in encoded_waybills:
            waybill_file = base64.b64decode(encoded)
            with BytesIO(waybill_file) as bio:
                gif = Image.open(bio)
                rotated_gif = gif.transpose(Image.Transpose.ROTATE_270)
                with BytesIO() as new_bio:
                    rotated_gif.save(new_bio, format="GIF")
                    rotated_gif_bytes_list.append(new_bio.getvalue())

        pdf_bytes = img2pdf.convert(rotated_gif_bytes_list)
        return pdf_bytes, HTTPStatus.OK

    # ------------------------------------------------------------------
    # Upload paperless documents
    # ------------------------------------------------------------------

    @retry_with_refresh_token
    async def upload_file_to_order(
        self,
        credentials: UpsCredentials,
        params: dict,
    ) -> tuple[Any, int]:
        """Upload a document (e.g. invoice) to a UPS shipment for paperless trade."""
        filename_full = params["filename"]
        filename, file_extension = os.path.splitext(filename_full)
        file_content = params["file"]
        document_type = params.get("type", "001")

        url = f"{settings.base_url}/api/paperlessdocuments/{settings.ups_api_version}/upload"
        headers = self._auth_headers(credentials)
        headers["ShipperNumber"] = credentials.shipper_number

        payload = {
            "UploadRequest": {
                "Request": {
                    "TransactionReference": {
                        "CustomerContext": "",
                    },
                },
                "UserCreatedForm": {
                    "UserCreatedFormFileName": filename,
                    "UserCreatedFormFileFormat": file_extension.lstrip("."),
                    "UserCreatedFormDocumentType": document_type,
                    "UserCreatedFormFile": file_content,
                },
                "ShipperNumber": credentials.shipper_number,
            },
        }

        response = await self._client.post(url, json=payload, headers=headers)
        return response.json(), response.status_code

    # ------------------------------------------------------------------
    # Rating
    # ------------------------------------------------------------------

    @retry_with_refresh_token
    async def get_rates(
        self,
        credentials: UpsCredentials,
        request: Any = None,
    ) -> tuple[Any, int]:
        """Retrieve shipping rates via the UPS Rating API.

        https://developer.ups.com/api/reference?loc=en_PL#operation/Rate
        """
        if request is None:
            return {"error": "No rate request provided"}, HTTPStatus.BAD_REQUEST

        payload = {
            "RateRequest": {
                "Request": {
                    "RequestOption": "Shop",
                    "SubVersion": "2205",
                },
                "Shipment": {
                    "Shipper": {
                        "Address": {
                            "PostalCode": request.sender_postal_code,
                            "City": request.sender_city,
                            "CountryCode": request.sender_country_code,
                        },
                        "ShipperNumber": credentials.shipper_number,
                    },
                    "ShipTo": {
                        "Address": {
                            "PostalCode": request.receiver_postal_code,
                            "City": request.receiver_city,
                            "CountryCode": request.receiver_country_code,
                        },
                    },
                    "ShipFrom": {
                        "Address": {
                            "PostalCode": request.sender_postal_code,
                            "City": request.sender_city,
                            "CountryCode": request.sender_country_code,
                        },
                    },
                    "Package": {
                        "PackagingType": {"Code": "02"},
                        "Dimensions": {
                            "UnitOfMeasurement": {"Code": "CM"},
                            "Length": str(int(request.length)) if request.length else "1",
                            "Width": str(int(request.width)) if request.width else "1",
                            "Height": str(int(request.height)) if request.height else "1",
                        },
                        "PackageWeight": {
                            "UnitOfMeasurement": {"Code": "KGS"},
                            "Weight": str(round(request.weight, 1)) if request.weight else "1",
                        },
                    },
                },
            },
        }

        url = f"{settings.base_url}/api/rating/{settings.ups_api_version}/Shop"
        headers = self._auth_headers(credentials)

        response = await self._client.post(url, json=payload, headers=headers)

        if response.status_code != HTTPStatus.OK:
            return await _format_rest_error_response(response)

        raw = response.json()
        return self._normalize_rate_response(raw).model_dump(), HTTPStatus.OK

    @staticmethod
    def _normalize_rate_response(raw: dict) -> StandardizedRateResponse:
        products: list[RateProduct] = []
        rated_shipments = raw.get("RateResponse", {}).get("RatedShipment", [])
        if isinstance(rated_shipments, dict):
            rated_shipments = [rated_shipments]

        service_names = {
            "01": "UPS Next Day Air", "02": "UPS 2nd Day Air",
            "03": "UPS Ground", "07": "UPS Worldwide Express",
            "08": "UPS Worldwide Expedited", "11": "UPS Standard",
            "12": "UPS 3 Day Select", "14": "UPS Next Day Air Early",
            "54": "UPS Worldwide Express Plus", "65": "UPS Saver",
            "70": "UPS Access Point Economy", "71": "UPS Worldwide Express Freight Midday",
            "72": "UPS Worldwide Economy", "74": "UPS Express 12:00",
            "75": "UPS Heavy Goods",
        }

        for shipment in rated_shipments:
            service_code = shipment.get("Service", {}).get("Code", "")
            total = shipment.get("TotalCharges", {})
            price = float(total.get("MonetaryValue", 0))
            currency = total.get("CurrencyCode", "PLN")
            name = service_names.get(service_code, f"UPS Service {service_code}")

            days = None
            if guaranteed := shipment.get("GuaranteedDelivery", {}):
                try:
                    days = int(guaranteed.get("BusinessDaysInTransit", 0))
                except (ValueError, TypeError):
                    pass

            products.append(RateProduct(
                name=name,
                price=price,
                currency=currency,
                delivery_days=days,
                attributes={
                    "source": "ups",
                    "service_code": service_code,
                },
            ))

        return StandardizedRateResponse(products=products, source="ups", raw=raw)

    # ------------------------------------------------------------------
    # Private — auth helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _auth_headers(credentials: UpsCredentials) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "transactionSrc": "testing",
            "Authorization": f"Bearer {credentials.access_token}",
        }

    # ------------------------------------------------------------------
    # Private — normalise response
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_order_item(
        command: CreateShipmentRequest,
        order_data: dict,
    ) -> CreateOrderResponse:
        shipment_id = order_data["ShipmentIdentificationNumber"]
        return CreateOrderResponse(
            id=shipment_id,
            waybill_number=shipment_id,
            shipper=UpsIntegration._normalize_shipment_party(command.shipper),
            receiver=UpsIntegration._normalize_shipment_party(command.receiver),
            orderStatus="CREATED",
        )

    @staticmethod
    def _normalize_shipment_party(party: ShipmentParty) -> ShipmentPartyResponse:
        street = party.street or ""
        building = party.building_number or ""
        postal = party.postal_code or ""
        city = party.city or ""
        country = party.country_code or "PL"
        return ShipmentPartyResponse(
            first_name=party.first_name,
            last_name=party.last_name,
            contact_person=party.contact_person,
            phone=party.phone,
            email=party.email,
            address=AddressResponse(
                building_number=building,
                city=city,
                country_code=country,
                line1=f"{street} {building}",
                line2=f"{postal} {city} {country}",
                post_code=postal,
                street=street,
            ),
        )

    # ------------------------------------------------------------------
    # Private — label recovery payload
    # ------------------------------------------------------------------

    @staticmethod
    def _get_waybill_label_recovery_payload(waybill_number: str) -> dict:
        return {
            "LabelRecoveryRequest": {
                "LabelSpecification": {
                    "LabelImageFormat": {"Code": "GIF"},
                },
                "Request": {
                    "RequestOption": "Non_Validate",
                    "SubVersion": settings.ups_api_version,
                },
                "TrackingNumber": waybill_number,
            },
        }

    # ------------------------------------------------------------------
    # Private — create shipment payload (FULL port)
    # ------------------------------------------------------------------

    @staticmethod
    def _get_create_package_payload(
        command: CreateShipmentRequest,
        credentials: UpsCredentials,
    ) -> dict:
        """Build the full UPS ``ShipmentRequest`` payload.

        Includes: insurance, COD, notifications, international forms,
        payment information (bill shipper / bill receiver), delivery12 override,
        and multi-package support via parcel unravelling.
        """
        shipper_payload = UpsIntegration._get_shipment_party_payload(command.shipper)
        receiver_payload = UpsIntegration._get_shipment_party_payload(command.receiver)

        shipper_account_number = credentials.shipper_number
        shipper_payload["ShipperNumber"] = shipper_account_number

        receiver_account_number = (
            command.payment.receiver_account_id if command.payment else None
        )

        ups_extras_raw = command.extras.get("ups", {})
        ups_extras = UpsExtras(**ups_extras_raw) if isinstance(ups_extras_raw, dict) else ups_extras_raw

        service = command.service_name
        if ups_extras.delivery12:
            logger.warning("UPS — overriding service to 74 (UPS Express 12:00)")
            service = "74"

        # --- Insurance ---
        insurance_code_type = "01"
        payer_type = command.payment.payer_type if command.payment else None
        if payer_type == "RECIPIENT":
            insurance_code_type = "02"

        parcels = unravel_parcels(command.parcels)

        insurance_value_decimal = round(
            Decimal(str(ups_extras.insurance_value)) / max(len(parcels), 1), 2,
        )
        formatted_insurance_value = f"{float(insurance_value_decimal):.2f}"

        package_service_options: dict | None = None
        if ups_extras.insurance:
            package_service_options = {
                "DeclaredValue": {
                    "Type": {"Code": insurance_code_type},
                    "CurrencyCode": ups_extras.insurance_curr,
                    "MonetaryValue": formatted_insurance_value,
                },
            }

        # --- Payment / shipment charges ---
        shipment_charges: list[dict] = []
        if receiver_account_number and payer_type in ("RECIPIENT", "RECEIVER"):
            shipment_charges.append({
                "Type": "01",
                "BillReceiver": {
                    "AccountNumber": receiver_account_number,
                },
            })
        else:
            shipment_charges.append({
                "Type": "01",
                "BillShipper": {
                    "AccountNumber": shipper_account_number,
                },
            })

        customs_payer_type = command.payment.customs_payer_type if command.payment else None
        if customs_payer_type and customs_payer_type == "SHIPPER":
            shipment_charges.append({
                "Type": "02",
                "BillShipper": {
                    "AccountNumber": shipper_account_number,
                },
            })

        # --- International forms ---
        international_forms: dict | None = None
        custom_document_ids = ups_extras.custom_document_ids
        if custom_document_ids:
            international_forms = {
                "FormType": "07",
                "UserCreatedForm": {
                    "DocumentID": custom_document_ids,
                },
            }

        # --- COD ---
        cod_section: dict | None = None
        if command.cod and command.cod_value is not None:
            cod_section = {
                "CODFundsCode": "1",
                "CODAmount": {
                    "CurrencyCode": command.cod_curr if command.cod_curr else "PLN",
                    "MonetaryValue": f"{float(command.cod_value):.2f}",
                },
            }

        # --- Notifications ---
        notifications: list[dict] = []
        receiver_email = command.receiver.email or ""
        if receiver_email:
            for code in ("6", "7", "8"):
                notifications.append({
                    "NotificationCode": code,
                    "EMail": {"EMailAddress": receiver_email},
                })

        # --- Shipment service options ---
        shipment_service_options: dict[str, Any] = {}
        if notifications:
            shipment_service_options["Notification"] = notifications
        if cod_section:
            shipment_service_options["COD"] = cod_section
        if international_forms:
            shipment_service_options["InternationalForms"] = international_forms

        # --- Package list ---
        packages: list[dict] = []
        for parcel in parcels:
            pkg: dict[str, Any] = {
                "Description": command.content or "",
                "Packaging": {"Code": parcel.parcel_type},
                "Dimensions": {
                    "UnitOfMeasurement": {"Code": "CM", "Description": "Centimeters"},
                    "Length": str(int(parcel.length)),
                    "Width": str(int(parcel.width)),
                    "Height": str(int(parcel.height)),
                },
                "PackageWeight": {
                    "UnitOfMeasurement": {"Code": "KGS", "Description": "Kilograms"},
                    "Weight": str(int(parcel.weight)),
                },
            }
            if package_service_options:
                pkg["PackageServiceOptions"] = package_service_options
            packages.append(pkg)

        return {
            "ShipmentRequest": {
                "Request": {
                    "SubVersion": "2205",
                    "RequestOption": "nonvalidate",
                },
                "Shipment": {
                    "Description": command.content or "",
                    "Shipper": shipper_payload,
                    "ShipTo": receiver_payload,
                    "PaymentInformation": {
                        "ShipmentCharge": shipment_charges,
                    },
                    "Service": {"Code": service},
                    "Package": packages,
                    "ShipmentServiceOptions": shipment_service_options,
                },
                "LabelSpecification": {
                    "LabelImageFormat": {"Code": "GIF", "Description": "GIF"},
                    "CharacterSet": "pol",
                },
            },
        }

    # ------------------------------------------------------------------
    # Private — shipment party payload
    # ------------------------------------------------------------------

    @staticmethod
    def _get_shipment_party_payload(party: ShipmentParty) -> dict:
        """Build the Shipper / ShipTo dict for the UPS API.

        Concatenates street + building_number, then splits into 35-char chunks
        (UPS allows max 3 AddressLine entries of 35 chars each).
        """
        address_line = " ".join(filter(None, [party.street, party.building_number]))
        chunk_size = 35
        address_lines = [
            address_line[i: i + chunk_size]
            for i in range(0, len(address_line), chunk_size)
        ]
        if len(address_lines) > 3:
            logger.warning("Address too long, truncating to 3 lines")
            address_lines = address_lines[:3]

        return {
            "Name": party.company_name or f"{party.first_name} {party.last_name}",
            "AttentionName": party.contact_person or f"{party.first_name} {party.last_name}",
            "Phone": {
                "Number": party.phone or "",
            },
            "EMailAddress": party.email or "",
            "Address": {
                "AddressLine": address_lines,
                "City": party.city,
                "StateProvinceCode": party.province or "",
                "PostalCode": party.postal_code,
                "CountryCode": party.country_code,
            },
        }
