"""FedEx Courier Integration — migrated from meriship codebase.

Handles all FedEx REST API interactions including:
- OAuth2 token acquisition (client_credentials)
- Shipment creation
- Shipment cancellation
- Label retrieval (from create response)
- Location/service-point lookup
- Tracking info
"""

from __future__ import annotations

import base64
import contextlib
import io
import logging
import zipfile
from http import HTTPStatus

import httpx

from src.config import settings
from src.schemas import FedexCredentials, RateProduct, StandardizedRateResponse

logger = logging.getLogger("courier-fedex")

DAY_TRANSLATION: dict[str, str] = {
    "MONDAY": "Poniedziałek",
    "TUESDAY": "Wtorek",
    "WEDNESDAY": "Środa",
    "THURSDAY": "Czwartek",
    "FRIDAY": "Piątek",
    "SATURDAY": "Sobota",
    "SUNDAY": "Niedziela",
}

TRACKING_URL = "https://www.fedex.com/fedextrack/?trknbr={tracking_number}"

POST_ORDER_SCHEMA: dict = {
    "id": "",
    "waybill_number": "",
    "shipper": {},
    "receiver": {},
    "created_at": "",
    "orderStatus": "",
    "tracking": {},
    "extras": {},
}

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


def _deep_copy_schema(schema: dict) -> dict:
    import json

    return json.loads(json.dumps(schema))


def format_postcode(postcode: str) -> str:
    if len(postcode) > 5 and "-" not in postcode:
        return f"{postcode[:2]}-{postcode[2:]}"
    return postcode


def _translate_payer_type(payment_type: str) -> str:
    if payment_type == "USER":
        return "THIRD_PARTY"
    if payment_type == "RECIPIENT":
        return "RECIPIENT"
    return "SENDER"


def _translate_distance_to_km(distance_obj: dict) -> float:
    if distance_obj["units"] == "MI":
        return round(distance_obj["value"] * 1.609344, 3)
    return distance_obj["value"]


class FedexIntegration:
    """FedEx REST integration (OAuth2 + JSON API)."""

    def __init__(self) -> None:
        logger.info("FedEx REST integrator using %s", settings.fedex_api_url)

    # ------------------------------------------------------------------
    # OAuth2
    # ------------------------------------------------------------------

    @staticmethod
    async def _get_oauth_token(client_id: str, client_secret: str) -> str | None:
        async with httpx.AsyncClient(timeout=settings.rest_timeout) as client:
            response = await client.post(
                f"{settings.fedex_api_url}oauth/token",
                headers={"content-type": "application/x-www-form-urlencoded"},
                data={
                    "grant_type": "client_credentials",
                    "client_id": client_id,
                    "client_secret": client_secret,
                },
            )
        return response.json().get("access_token")

    @staticmethod
    def _get_headers(access_token: str) -> dict[str, str]:
        return {
            "authorization": f"Bearer {access_token}",
            "content-type": "application/json",
            "x-locale": "pl_PL",
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _pack_errors(response: httpx.Response) -> tuple[str, int]:
        error_str = " ".join(error["message"] for error in response.json()["errors"])
        return error_str, response.status_code

    @staticmethod
    def _strip_package_label(order: dict) -> dict:
        shipments = order.get("extras", {}).get("fedex", {}).get("output", {}).get("transactionShipments", {})
        if not shipments:
            return order
        for piece in shipments[0].get("pieceResponses", []):
            piece.pop("packageDocuments", None)
        return order

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
    # Create shipment
    # ------------------------------------------------------------------

    async def create_order(
        self,
        credentials: FedexCredentials,
        data: dict,
    ) -> tuple[dict | str, int]:
        """Create a FedEx shipment via /ship/v1/shipments.

        See: https://developer.fedex.com/api/pl-pl/catalog/ship/v1/docs.html
        """
        extras_fedex = data.get("extras", {}).get("fedex", {})
        service_type = extras_fedex.get("service_type")
        packaging_type = extras_fedex.get("packaging_type")
        if not service_type or not packaging_type:
            return (
                "extras.fedex must contain 'service_type' and 'packaging_type'",
                HTTPStatus.BAD_REQUEST,
            )

        access_token = await self._get_oauth_token(
            credentials.client_id,
            credentials.client_secret,
        )
        if not access_token:
            return (
                "Nie udało się pobrać tokenu logowania FedEx. Zweryfikuj dane logowania.",
                HTTPStatus.BAD_REQUEST,
            )

        payload = {
            "labelResponseOptions": "LABEL",
            "requestedShipment": {
                "recipientLocationNumber": "1234567",
                "pickupType": "USE_SCHEDULED_PICKUP",
                "serviceType": service_type,
                "totalWeight": sum(parcel["weight"] for parcel in data["parcels"]),
                "preferredCurrency": settings.default_currency,
                "totalPackageCount": 1,
                "shipper": {
                    "contact": {
                        "personName": f"{data['shipper']['first_name']} {data['shipper']['last_name']}",
                        "phoneNumber": data["shipper"]["phone"],
                    },
                    "address": {
                        "streetLines": [
                            data["shipper"]["street"],
                            data["shipper"]["building_number"],
                        ],
                        "city": data["shipper"]["city"],
                        "postalCode": data["shipper"]["postal_code"],
                        "countryCode": data["shipper"]["country_code"],
                    },
                },
                "recipients": [
                    {
                        "contact": {
                            "personName": f"{data['receiver']['first_name']} {data['receiver']['last_name']}",
                            "phoneNumber": data["receiver"]["phone"],
                        },
                        "address": {
                            "streetLines": [
                                data["receiver"]["street"],
                                data["receiver"]["building_number"],
                            ],
                            "city": data["receiver"]["city"],
                            "postalCode": data["receiver"]["postal_code"],
                            "countryCode": data["receiver"]["country_code"],
                        },
                        "deliveryInstructions": data.get("comment", ""),
                    }
                ],
                "shipDatestamp": data.get("shipment_date", ""),
                "packagingType": packaging_type,
                "blockInsightVisibility": False,
                "shippingChargesPayment": {
                    "paymentType": _translate_payer_type(
                        data.get("payment", {}).get("payer_type", "SENDER"),
                    ),
                },
                "labelSpecification": {
                    "imageType": "PDF",
                    "labelStockType": "PAPER_85X11_TOP_HALF_LABEL",
                },
                "requestedPackageLineItems": [
                    {
                        "weight": {"units": "KG", "value": parcel["weight"]},
                        "dimensions": {
                            "length": parcel["length"],
                            "width": parcel["width"],
                            "height": parcel["height"],
                            "units": "CM",
                        },
                        "itemDescription": data.get("content", ""),
                    }
                    for parcel in data["parcels"]
                ],
            },
            "accountNumber": {"value": data.get("payment", {}).get("account_id", "")},
        }

        async with httpx.AsyncClient(timeout=settings.rest_timeout) as client:
            response = await client.post(
                f"{settings.fedex_api_url}ship/v1/shipments",
                headers=self._get_headers(access_token),
                json=payload,
            )

        if response.status_code != HTTPStatus.OK:
            return self._pack_errors(response)

        resp_json = response.json()

        normalized = _deep_copy_schema(POST_ORDER_SCHEMA)
        tx_shipment = resp_json["output"]["transactionShipments"][0]
        normalized["id"] = tx_shipment["masterTrackingNumber"]
        normalized["waybill_number"] = tx_shipment["masterTrackingNumber"]
        normalized["created_at"] = tx_shipment.get("shipDatestamp", "")
        normalized["extras"]["fedex"] = resp_json

        tracking_number = tx_shipment["masterTrackingNumber"]
        normalized["tracking"] = {
            "tracking_number": tracking_number,
            "tracking_url": TRACKING_URL.format(tracking_number=tracking_number),
        }

        shipper = data.get("shipper", {})
        receiver = data.get("receiver", {})
        normalized["shipper"] = self._normalize_shipment_party(shipper)
        normalized["receiver"] = self._normalize_shipment_party(receiver)
        normalized["orderStatus"] = "CREATED"

        return self._strip_package_label(normalized), HTTPStatus.CREATED

    # ------------------------------------------------------------------
    # Delete (cancel) shipment
    # ------------------------------------------------------------------

    async def delete_order(
        self,
        credentials: FedexCredentials,
        order_id: str,
        data: dict,
    ) -> tuple[dict | str, int]:
        """Cancel a FedEx shipment via /ship/v1/shipments/cancel."""
        extras = data.get("fedex", data.get("extras", {}).get("fedex", {}))
        account_id = extras.get("account_id", "")
        if not account_id:
            return "extras.fedex.account_id is required", HTTPStatus.BAD_REQUEST

        access_token = await self._get_oauth_token(
            credentials.client_id,
            credentials.client_secret,
        )
        if not access_token:
            return (
                "Nie udało się pobrać tokenu logowania FedEx. Zweryfikuj dane logowania.",
                HTTPStatus.BAD_REQUEST,
            )

        async with httpx.AsyncClient(timeout=settings.rest_timeout) as client:
            response = await client.put(
                f"{settings.fedex_api_url}ship/v1/shipments/cancel",
                headers=self._get_headers(access_token),
                json={
                    "accountNumber": {"value": account_id},
                    "trackingNumber": order_id,
                },
            )

        resp_json = response.json()
        if not resp_json.get("output", {}).get("cancelledShipment", False):
            return (
                "Nie udało się anulować wysyłki: wysyłka mogła być już anulowana lub nie istnieje",
                HTTPStatus.NOT_FOUND,
            )

        return {}, HTTPStatus.NO_CONTENT

    # ------------------------------------------------------------------
    # Labels
    # ------------------------------------------------------------------

    async def get_label_bytes_from_shipment(
        self,
        credentials: FedexCredentials,
        shipment_response: dict,
    ) -> tuple[bytes | str, int]:
        """Extract label PDF bytes from a stored create-shipment response.

        The FedEx REST API returns encoded labels inline in the create-shipment
        response (transactionShipments.pieceResponses.packageDocuments.encodedLabel).
        """
        shipments = shipment_response.get("output", {}).get("transactionShipments", [])
        if not shipments:
            return "Nie znaleziono etykiet", HTTPStatus.NOT_FOUND

        labels: dict[str, str] = {}
        for piece in shipments[0].get("pieceResponses", []):
            docs = piece.get("packageDocuments", [])
            if docs:
                labels[piece["trackingNumber"]] = docs[0]["encodedLabel"]

        if not labels:
            return "Nie znaleziono etykiet", HTTPStatus.NOT_FOUND

        if len(labels) == 1:
            _tracking, base_str = labels.popitem()
            return base64.b64decode(base_str), HTTPStatus.OK

        output = io.BytesIO()
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED, False) as zf:
            for tracking, base_str in labels.items():
                zf.writestr(f"{tracking}.pdf", base64.b64decode(base_str))
        return output.getvalue(), HTTPStatus.OK

    # ------------------------------------------------------------------
    # Service points (locations)
    # ------------------------------------------------------------------

    async def get_points(
        self,
        credentials: FedexCredentials,
        data: dict,
    ) -> tuple[dict | str, int]:
        """Find FedEx locations via /location/v1/locations."""
        access_token = await self._get_oauth_token(
            credentials.client_id,
            credentials.client_secret,
        )
        if not access_token:
            return (
                "Nie udało się pobrać tokenu logowania FedEx. Zweryfikuj dane logowania.",
                HTTPStatus.BAD_REQUEST,
            )

        async with httpx.AsyncClient(timeout=settings.rest_timeout) as client:
            response = await client.post(
                f"{settings.fedex_api_url}location/v1/locations",
                headers=self._get_headers(access_token),
                json={
                    "location": {
                        "address": {
                            "city": data.get("city", ""),
                            "countryCode": "PL",
                            "postalCode": data.get("postcode", ""),
                        }
                    }
                },
            )

        if response.status_code != HTTPStatus.OK:
            return self._pack_errors(response)

        points: dict = {}
        for fedex_point in response.json()["output"]["locationDetailList"]:
            point = _deep_copy_schema(GET_POINT_SCHEMA)
            fedex_address = fedex_point["contactAndAddress"]["address"]

            point["type"] = fedex_point.get("locationType", "")
            point["name"] = fedex_point["contactAndAddress"].get("addressAncillaryDetail", {}).get("displayName", "")

            street_lines = fedex_address.get("streetLines", [])
            if len(street_lines) > 0:
                point["address"]["line1"] = street_lines[0]
                if len(street_lines) > 1:
                    point["address"]["line2"] = street_lines[1]

            point["address"]["postal_code"] = format_postcode(
                fedex_address.get("postalCode", ""),
            )
            point["address"]["country_code"] = fedex_address.get("countryCode", "")

            geo = fedex_point.get("geoPositionalCoordinates", {})
            point["address"]["longitude"] = geo.get("longitude", "")
            point["address"]["latitude"] = geo.get("latitude", "")

            point["additional_info"] = fedex_point.get("specialInstructions", "")
            point["distance"] = _translate_distance_to_km(fedex_point["distance"])

            open_hours_lines: list[str] = []
            for hours in fedex_point.get("storeHours", []):
                day_name = DAY_TRANSLATION.get(hours["dayOfWeek"], hours["dayOfWeek"])
                hours_type = hours.get("operationalHoursType")
                if hours_type == "OPEN_BY_HOURS" and "operationalHours" in hours:
                    oh = hours["operationalHours"]
                    open_hours_lines.append(f"{day_name}: {oh['begins']} - {oh['ends']}")
                elif hours_type == "CLOSED_ALL_DAY":
                    open_hours_lines.append(f"{day_name}: zamknięte cały dzień")
                elif hours_type == "OPEN_ALL_DAY":
                    open_hours_lines.append(f"{day_name}: otwarte cały dzień")

            point["open_hours"] = "\n".join(open_hours_lines)
            points[fedex_point["locationId"]] = point

        return points, response.status_code

    # ------------------------------------------------------------------
    # Rating
    # ------------------------------------------------------------------

    async def get_rates(
        self,
        credentials: FedexCredentials,
        request: object,
    ) -> tuple[dict | str, int]:
        """Retrieve shipping rates via FedEx Rate API (/rate/v1/rates/quotes)."""
        access_token = await self._get_oauth_token(
            credentials.client_id,
            credentials.client_secret,
        )
        if not access_token:
            return "FedEx token acquisition failed", HTTPStatus.BAD_REQUEST

        payload = {
            "accountNumber": {"value": getattr(request, "account_id", "")},
            "requestedShipment": {
                "shipper": {
                    "address": {
                        "postalCode": getattr(request, "sender_postal_code", ""),
                        "city": getattr(request, "sender_city", ""),
                        "countryCode": getattr(request, "sender_country_code", "PL"),
                    },
                },
                "recipient": {
                    "address": {
                        "postalCode": getattr(request, "receiver_postal_code", ""),
                        "city": getattr(request, "receiver_city", ""),
                        "countryCode": getattr(request, "receiver_country_code", "PL"),
                    },
                },
                "pickupType": "DROPOFF_AT_FEDEX_LOCATION",
                "rateRequestType": ["LIST", "ACCOUNT"],
                "requestedPackageLineItems": [
                    {
                        "weight": {
                            "units": "KG",
                            "value": getattr(request, "weight", 1),
                        },
                        "dimensions": {
                            "length": int(getattr(request, "length", 1)),
                            "width": int(getattr(request, "width", 1)),
                            "height": int(getattr(request, "height", 1)),
                            "units": "CM",
                        },
                    },
                ],
            },
        }

        async with httpx.AsyncClient(timeout=settings.rest_timeout) as client:
            response = await client.post(
                f"{settings.fedex_api_url}rate/v1/rates/quotes",
                headers=self._get_headers(access_token),
                json=payload,
            )

        if response.status_code != HTTPStatus.OK:
            return self._pack_errors(response)

        raw = response.json()
        return self._normalize_rate_response(raw).model_dump(), HTTPStatus.OK

    @staticmethod
    def _normalize_rate_response(raw: dict) -> StandardizedRateResponse:
        products: list[RateProduct] = []
        rate_details = raw.get("output", {}).get("rateReplyDetails", [])

        for detail in rate_details:
            service_type = detail.get("serviceType", "")
            service_name = detail.get("serviceName", service_type)

            rated = detail.get("ratedShipmentDetails", [])
            if not rated:
                continue

            charges = rated[0].get("totalNetCharge", 0)
            currency = rated[0].get("currency", "PLN")
            if isinstance(charges, str):
                charges = float(charges)

            transit_days = None
            if (transit := detail.get("commit", {})) and (date_detail := transit.get("dateDetail", {})):
                transit_days_str = date_detail.get("dayCount")
                if transit_days_str:
                    with contextlib.suppress(ValueError, TypeError):
                        transit_days = int(transit_days_str)

            products.append(
                RateProduct(
                    name=service_name,
                    price=float(charges),
                    currency=currency,
                    delivery_days=transit_days,
                    attributes={
                        "source": "fedex",
                        "service_type": service_type,
                    },
                )
            )

        return StandardizedRateResponse(products=products, source="fedex", raw=raw)

    # ------------------------------------------------------------------
    # Tracking
    # ------------------------------------------------------------------

    @staticmethod
    def get_tracking_info(tracking_number: str) -> tuple[dict, int]:
        return {
            "tracking_number": tracking_number,
            "tracking_url": TRACKING_URL.format(tracking_number=tracking_number),
        }, HTTPStatus.OK
