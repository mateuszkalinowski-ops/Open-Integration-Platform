"""Poczta Polska Courier Integration — migrated from meriship codebase.

Handles all Poczta Polska SOAP API interactions including:
- Shipment creation (clearEnvelope -> addShipment -> zamowKuriera -> sendEnvelope)
- Label retrieval (getPrintForParcel)
- Shipment status tracking (sprawdzPrzesylke via WSSE)
- Postal office points lookup (getPlacowkiPocztowe)

Uses TWO separate SOAP clients:
- tracking_client: WSSE UsernameToken authentication
- posting_client: HTTP Basic authentication
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import date, datetime
from enum import Enum
from http import HTTPStatus
from typing import ClassVar

from requests import Session
from requests.auth import HTTPBasicAuth
from zeep import Client, Transport
from zeep.exceptions import Fault, TransportError
from zeep.helpers import serialize_object
from zeep.wsse.username import UsernameToken

from src.config import settings
from src.schemas import (
    CreateShipmentRequest,
    Parcel,
    PocztaPolskaCredentials,
    ShipmentParty,
)

logger = logging.getLogger("courier-pocztapolska")

MAX_PARCEL_SUM_SIZE = 2500.0
MAX_PARCEL_SIZE = 1200.0
MAX_PARCEL_WEIGHT = 50000.0

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


def wsdl_to_json(data: object) -> dict:
    """Convert a zeep SOAP response object to a JSON-serializable dict."""
    return json.loads(json.dumps(serialize_object(data)))


def _deep_copy_schema(schema: dict) -> dict:
    return json.loads(json.dumps(schema))


class PocztaPolskaIntegration:
    """Poczta Polska SOAP integration.

    Requires two separate SOAP clients because tracking and posting use
    different authentication mechanisms (WSSE vs HTTP Basic Auth).
    """

    TRACKING_URL = "https://emonitoring.poczta-polska.pl/?numer={tracking_number}"

    PAYER_TYPES: ClassVar[dict[str, str]] = {
        "SHIPPER": "NADAWCA",
        "RECIPIENT": "ADRESAT",
    }

    class OrderStatus(Enum):
        OK = 0
        OTHER_PACKAGES = 1
        NOT_FOUND = -1
        INVALID_PACKAGE_NUMBER = -2
        OTHER_ERROR = -99

    def __init__(self) -> None:
        self.tracking_client: Client | None = None
        self.posting_client: Client | None = None
        self._create_soap_client_for_tracking(None, None)
        self._create_soap_client_for_posting(None, None)

    # ------------------------------------------------------------------
    # Order status
    # ------------------------------------------------------------------

    def get_order_status(
        self,
        credentials: PocztaPolskaCredentials,
        order_id: str,
    ) -> tuple[str | int, int]:
        """Get order status via tracking SOAP client (sprawdzPrzesylke)."""
        login, password = credentials.login, credentials.password
        try:
            if self._are_tracking_credentials_different(login, password):
                self._create_soap_client_for_tracking(login, password)
            response = self.tracking_client.service.sprawdzPrzesylke(numer=order_id)

            match response.status:
                case self.OrderStatus.OK.value:
                    events = response.danePrzesylki.zdarzenia.zdarzenie
                    events = sorted(
                        events,
                        key=lambda event: datetime.strptime(event.czas, "%Y-%m-%d %H:%M"),
                        reverse=True,
                    )
                    order_status_code = events[0].kod
                    return order_status_code, HTTPStatus.OK
                case self.OrderStatus.NOT_FOUND.value:
                    return response.status, HTTPStatus.NOT_FOUND
                case _:
                    return response.status, HTTPStatus.BAD_REQUEST

        except Fault as e:
            return str(e), HTTPStatus.BAD_REQUEST
        except AttributeError:
            return "SOAP client has not been created", HTTPStatus.BAD_REQUEST

    # ------------------------------------------------------------------
    # Tracking info
    # ------------------------------------------------------------------

    def get_tracking_info(
        self,
        order_id: str,
    ) -> tuple[dict, int]:
        """Return tracking URL — no API call needed."""
        return {
            "tracking_number": order_id,
            "tracking_url": self.TRACKING_URL.format(tracking_number=order_id),
        }, HTTPStatus.OK

    # ------------------------------------------------------------------
    # Create order (multi-step envelope flow)
    # ------------------------------------------------------------------

    def create_order(
        self,
        credentials: PocztaPolskaCredentials,
        command: CreateShipmentRequest,
    ) -> tuple[object, int]:
        """Create order using the Poczta Polska envelope workflow:

        1. clearEnvelope — clear buffer of unsent data
        2. addShipment — add shipment data
        3. zamowKuriera — book courier (optional)
        4. sendEnvelope — finalize and send all shipments
        """
        login, password = credentials.login, credentials.password
        if self._are_posting_credentials_different(login, password):
            self._create_soap_client_for_posting(login, password)

        pocztapolska_extras: dict = command.extras.get("pocztapolska", {})
        dispatch_office = pocztapolska_extras.get("dispatch_office")
        if not dispatch_office:
            dispatch_office = self._get_default_dispatch_office()

        clear_envelope = not pocztapolska_extras.get("not_clear_envelope", False)
        send_envelope = not pocztapolska_extras.get("not_send_envelope", False)

        # 1) Clear the buffer
        if clear_envelope:
            response = self.posting_client.service.clearEnvelope()
            if not response["retval"]:
                return response["error"], HTTPStatus.BAD_REQUEST

        # 2) Add parcels to the shipment
        response, status_code = self._create_order(command)
        if status_code != HTTPStatus.OK:
            return response, status_code

        waybill_number = response[0]["numerNadania"]
        guid = response[0]["guid"]

        # 3) Book a courier (optional)
        if pocztapolska_extras.get("book_courier"):
            status_code = self._book_courier(command)
            if status_code != HTTPStatus.CREATED:
                return "Wystąpił błąd podczas zamawiania kuriera!", status_code

        order: dict = {}

        # 4) Send all shipments
        if send_envelope:
            response = self.posting_client.service.sendEnvelope(
                urzadNadania=dispatch_office,
                pakiet=[],
            )

            status_code = HTTPStatus.CREATED if not response["error"] else HTTPStatus.BAD_REQUEST
            if status_code != HTTPStatus.CREATED:
                return self._get_list_error_response(response), status_code

            order["orderStatus"] = response["envelopeStatus"]
        else:
            order["orderStatus"] = "UNKNOWN"
            status_code = HTTPStatus.OK

        order["waybill"] = waybill_number
        order["id"] = guid

        return self._normalize_order_item(command, order), status_code

    # ------------------------------------------------------------------
    # Labels
    # ------------------------------------------------------------------

    def get_waybill_label_bytes(
        self,
        credentials: PocztaPolskaCredentials,
        waybill_numbers: list[str],
        args: dict,
    ) -> tuple[bytes | str | list, int]:
        """Retrieve label PDF bytes via getPrintForParcel.

        Note: uses GUIDs (external_id) rather than waybill numbers.
        """
        login, password = credentials.login, credentials.password
        if self._are_posting_credentials_different(login, password):
            self._create_soap_client_for_posting(login, password)

        guids = args.get("external_id", waybill_numbers)
        try:
            response = self.posting_client.service.getPrintForParcel(
                guid=guids,
                type={
                    "kind": "ADDRESS_LABEL",
                    "method": "ALL_PARCELS_IN_ONE_FILE",
                    "format": "PDF_FORMAT",
                },
            )
        except TransportError as e:
            return e.content, e.status_code
        except Fault as e:
            return e.message, HTTPStatus.BAD_REQUEST

        if response is None:
            return "Brak danych", HTTPStatus.NO_CONTENT

        status_code = HTTPStatus.OK if not response["error"] else HTTPStatus.BAD_REQUEST

        if status_code == HTTPStatus.BAD_REQUEST:
            return self._get_list_error_response(response), status_code

        return response["printResult"][0]["print"], status_code

    # ------------------------------------------------------------------
    # Postal office points
    # ------------------------------------------------------------------

    def get_points(
        self,
        credentials: PocztaPolskaCredentials,
        voivodeship_id: str,
    ) -> tuple[object, int]:
        """Get postal office points filtered by voivodeship (GUS code)."""
        login, password = credentials.login, credentials.password
        if self._are_posting_credentials_different(login, password):
            self._create_soap_client_for_posting(login, password)

        try:
            response = self.posting_client.service.getPlacowkiPocztowe(voivodeship_id)
        except TransportError as e:
            return e.content, e.status_code
        except Fault as e:
            return e.message, HTTPStatus.BAD_REQUEST

        if not response:
            return "Brak danych", HTTPStatus.NOT_FOUND

        points: dict = {}
        for pp_point in response:
            point = _deep_copy_schema(GET_POINT_SCHEMA)
            point["type"] = pp_point["typ"]
            point["name"] = pp_point["nazwa"]
            point["address"]["line1"] = f"{pp_point['ulica']} {pp_point['numerDomu']}"
            point["address"]["line2"] = pp_point["numerLokalu"]
            point["address"]["postal_code"] = pp_point["kodPocztowy"]
            point["address"]["country_code"] = "PL"
            point["address"]["city"] = pp_point["miejscowosc"]
            point["address"]["longitude"] = pp_point["lokalizacjaGeograficzna"]["dlugosc"]["dec"]
            point["address"]["latitude"] = pp_point["lokalizacjaGeograficzna"]["szerokosc"]["dec"]

            work_hours = pp_point["godzinyPracy"]
            point["open_hours"] = {
                day: {
                    "od": work_hours[day][0]["od"].strftime("%H:%M") if work_hours[day][0]["od"] else None,
                    "do": work_hours[day][0]["do"].strftime("%H:%M") if work_hours[day][0]["do"] else None,
                }
                for day in ("robocze", "sobota", "niedziela", "swieta")
                if work_hours and work_hours[day]
            }
            point["option_cod"] = pp_point["maksymalnaKwotaPobrania"] not in (None, 0)
            point["option_send"] = pp_point["funkcja"] in ("NADAWCZA", "NADAWCZO-ODDAWCZA")
            point["additional_info"] = pp_point["opis"]

            points[point["name"]] = point

        return points, HTTPStatus.OK

    # ------------------------------------------------------------------
    # Envelope list (utility)
    # ------------------------------------------------------------------

    def get_envelope_list(
        self,
        credentials: PocztaPolskaCredentials,
        start_date: str,
        end_date: str,
    ) -> tuple[object, int]:
        login, password = credentials.login, credentials.password
        if self._are_posting_credentials_different(login, password):
            self._create_soap_client_for_posting(login, password)
        try:
            response = self.posting_client.service.getEnvelopeList(
                startDate=start_date,
                endDate=end_date,
            )
        except TransportError as e:
            return e.content, e.status_code
        except Fault as e:
            return e.message, HTTPStatus.BAD_REQUEST

        if not response:
            return "Brak danych", HTTPStatus.NOT_FOUND
        return wsdl_to_json(response), HTTPStatus.OK

    # ------------------------------------------------------------------
    # Private — SOAP client management
    # ------------------------------------------------------------------

    def _create_soap_client_for_tracking(self, login: str | None, password: str | None) -> None:
        """Create WSSE-authenticated SOAP client for shipment tracking."""
        transport = Transport(
            timeout=settings.soap_timeout,
            operation_timeout=settings.soap_operation_timeout,
        )
        try:
            self.tracking_client = Client(
                settings.poczta_polska_tracking_wsdl,
                wsse=UsernameToken(login, password),
                transport=transport,
            )
            logger.info("Tracking SOAP client connected — %s", settings.poczta_polska_tracking_wsdl)
        except ConnectionError:
            logger.error("Tracking SOAP client timeout — %s", settings.poczta_polska_tracking_wsdl)
        except Exception:
            logger.exception("Tracking SOAP client init failed — %s", settings.poczta_polska_tracking_wsdl)

    def _create_soap_client_for_posting(self, login: str | None, password: str | None) -> None:
        """Create HTTP Basic Auth SOAP client for shipment posting."""
        session = Session()
        session.auth = HTTPBasicAuth(login, password)
        transport = Transport(
            session=session,
            timeout=settings.soap_timeout,
            operation_timeout=settings.soap_operation_timeout,
        )
        try:
            self.posting_client = Client(
                wsdl=settings.poczta_polska_posting_wsdl,
                transport=transport,
            )
            logger.info("Posting SOAP client connected — %s", settings.poczta_polska_posting_wsdl)
        except ConnectionError:
            logger.error("Posting SOAP client timeout — %s", settings.poczta_polska_posting_wsdl)
        except Exception:
            logger.exception("Posting SOAP client init failed — %s", settings.poczta_polska_posting_wsdl)

    def _are_tracking_credentials_different(self, login: str, password: str) -> bool:
        if self.tracking_client:
            wsse = self.tracking_client.wsse
            if wsse and wsse.username == login and wsse.password == password:
                return False
        return True

    def _are_posting_credentials_different(self, login: str, password: str) -> bool:
        if self.posting_client:
            auth = self.posting_client.transport.session.auth
            if auth and auth.username == login and auth.password == password:
                return False
        return True

    # ------------------------------------------------------------------
    # Private — internal shipment creation
    # ------------------------------------------------------------------

    def _create_order(
        self,
        command: CreateShipmentRequest,
    ) -> tuple[object, int]:
        """Add parcel to an order via addShipment."""
        try:
            guid = self._generate_guid()
            shipment = self._get_pocztex_2021_data(command, guid)
            response = self.posting_client.service.addShipment(shipment)
        except TransportError as e:
            return e.content, e.status_code
        except Fault as e:
            return e.message, HTTPStatus.BAD_REQUEST

        if response is None:
            return "Brak danych", HTTPStatus.NO_CONTENT

        status_code = HTTPStatus.OK if not self._service_return_error(response) else HTTPStatus.BAD_REQUEST
        if status_code == HTTPStatus.OK:
            return wsdl_to_json(response), status_code

        return self._get_error_response_msg(response), status_code

    def _generate_guid(self) -> str:
        if settings.use_pocztapolska_guid:
            return self.posting_client.service.getGuid(ilosc=1)[0]
        return uuid.uuid4().hex.upper()

    def _get_default_dispatch_office(self) -> str:
        response: list[dict] = self.posting_client.service.getUrzedyNadania()
        if len(response) == 0:
            raise ValueError("Podany klient nie ma podpisanej umowy z zadnym urzadem nadania")
        return str(response[0]["urzadNadania"])

    # ------------------------------------------------------------------
    # Private — Pocztex 2021 shipment data builder
    # ------------------------------------------------------------------

    def _get_pocztex_2021_data(self, command: CreateShipmentRequest, guid: str) -> object:
        parcel = command.parcels[0]
        parcel_data = {
            "masa": parcel.weight,
            "ponadgabaryt": self._is_oversized(parcel),
            "format": self._get_format_pocztex_2021(parcel),
        }

        shipper_receiver_data = {
            "nadawca": self._get_shipment_party_info(command.shipper),
            "adresat": self._get_shipment_party_info(command.receiver),
            "adresDlaZwrotu": self._get_shipment_party_info(command.shipper),
        }

        pocztapolska_extras: dict = command.extras.get("pocztapolska", {})
        payment_data = self._extract_payment_data(command, pocztapolska_extras)

        shipment_data = {
            **parcel_data,
            **shipper_receiver_data,
            **payment_data,
            "guid": guid,
            "uiszczaOplate": self.PAYER_TYPES.get(command.payment.payer_type),
            "zawartosc": {"zawartoscInna": command.content},
            "zwrotDokumentow": "POCZTEX_KURIER" if pocztapolska_extras.get("rod") else None,
            "idDokumentyZwrotneAdresy": pocztapolska_extras.get("return_documents_address_id"),
            "odbiorWSobote": pocztapolska_extras.get("delivery_saturday"),
            "doreczenieDoRakWlasnych": pocztapolska_extras.get("bringing_pack"),
            "opis": command.content,
            "planowanaDataNadania": command.shipment_date,
            "numerPrzesylkiKlienta": pocztapolska_extras.get("customer_shipment_number"),
        }

        pocztapolska_shipment_class = self.posting_client.get_type("ns0:pocztex2021KurierType")
        return pocztapolska_shipment_class(**shipment_data)

    def _extract_payment_data(
        self,
        command: CreateShipmentRequest,
        pocztapolska_extras: dict,
    ) -> dict:
        payment = command.payment
        cod_value, is_cod = command.cod_value, command.cod
        return {
            "pobranie": None
            if not is_cod
            else {
                "sposobPobrania": "RACHUNEK_BANKOWY" if payment.payment_method == "BANK_TRANSFER" else "PRZEKAZ",
                "kwotaPobrania": int(float(cod_value) * 100) if is_cod else None,
                "nrb": payment.account_id,
                "tytulem": payment.transfer_title,
                "sprawdzenieZawartosciPrzesylkiPrzezOdbiorce": pocztapolska_extras.get(
                    "check_shipment_content_by_receiver"
                ),
            },
            "oplacaOdbiorca": None
            if (is_cod or self.PAYER_TYPES.get(payment.payer_type) == "NADAWCA")
            else {
                "typ": pocztapolska_extras.get("receiver_type"),
                "karta": None
                if pocztapolska_extras.get("receiver_type") == "ADRESAT_INDYWIDUALNY"
                else {
                    "idKarta": payment.account_id,
                    "idAdresKorespondencyjny": pocztapolska_extras.get("correspondence_address_id"),
                },
            },
            "ubezpieczenie": None
            if not pocztapolska_extras.get("insurance", False)
            else {
                "rodzaj": "STANDARD",
                "kwota": pocztapolska_extras.get("insurance_value"),
                "akceptacjaOWU": True,
            },
        }

    # ------------------------------------------------------------------
    # Private — book courier
    # ------------------------------------------------------------------

    def _book_courier(self, command: CreateShipmentRequest) -> int:
        """Book courier pickup via zamowKuriera. Response can take up to 5 minutes."""
        pocztapolska_extras = command.extras.get("pocztapolska", {})

        courier_data = {
            "miejsceOdbioru": self._get_shipment_party_info(command.shipper),
            "nadawca": self._get_shipment_party_info(command.shipper),
            "oczekiwanaDataOdbioru": command.shipment_date,
            "oczekiwanaGodzinaOdbioru": pocztapolska_extras.get("pickup_time_from"),
            "szacowanaIloscPrzeslek": str(sum(parcel.quantity for parcel in command.parcels)),
            "szacowanaLacznaMasaPrzesylek": str(sum(parcel.quantity * parcel.weight for parcel in command.parcels)),
            "potwierdzenieZamowieniaEmail": command.shipper.email,
        }

        try:
            error = self.posting_client.service.zamowKuriera(**courier_data)
        except TransportError as e:
            return e.status_code
        except Fault:
            return HTTPStatus.BAD_REQUEST

        return HTTPStatus.CREATED if not error else HTTPStatus.BAD_REQUEST

    # ------------------------------------------------------------------
    # Private — shipment party builder
    # ------------------------------------------------------------------

    @staticmethod
    def _get_shipment_party_info(shipment_party: ShipmentParty) -> dict:
        return {
            "nazwa": f"{shipment_party.first_name} {shipment_party.last_name}",
            "nazwa2": None,
            "ulica": shipment_party.street,
            "numerDomu": shipment_party.building_number,
            "numerLokalu": None,
            "miejscowosc": shipment_party.city,
            "kodPocztowy": shipment_party.postal_code.replace("-", ""),
            "kraj": shipment_party.country_code,
            "telefon": None,
            "email": shipment_party.email,
            "mobile": shipment_party.phone,
            "osobaKontaktowa": shipment_party.contact_person,
        }

    # ------------------------------------------------------------------
    # Private — normalisation
    # ------------------------------------------------------------------

    def _normalize_order_item(
        self,
        command: CreateShipmentRequest,
        order: dict,
    ) -> dict:
        waybill = order["waybill"]
        tracking_info, _ = self.get_tracking_info(waybill)
        return {
            "id": order["id"],
            "waybill_number": waybill,
            "shipper": self._normalize_shipment_party(command.shipper),
            "receiver": self._normalize_shipment_party(command.receiver),
            "created_at": date.today().isoformat(),
            "orderStatus": order["orderStatus"],
            "tracking": tracking_info,
        }

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
    # Private — parcel size / format helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _is_oversized(parcel: Parcel) -> bool:
        """Check oversized based on PP limits: sum(L+H+W) > 2500mm, max dim > 1200mm, weight > 50kg."""
        return (
            sum((parcel.length, parcel.height, parcel.width)) > MAX_PARCEL_SUM_SIZE
            or max(parcel.length, parcel.height, parcel.width) > MAX_PARCEL_SIZE
            or parcel.weight > MAX_PARCEL_WEIGHT
        )

    @staticmethod
    def _get_format_pocztex_2021(parcel: Parcel) -> str:
        """Determine format (S/M/L/XL/2XL) based on sorted dimensions and weight."""
        sizes = {
            "S": {"dimensions": [90.0, 400.0, 650.0], "weight": 20000.0},
            "M": {"dimensions": [200.0, 400.0, 650.0], "weight": 20000.0},
            "L": {"dimensions": [400.0, 420.0, 650.0], "weight": 20000.0},
            "XL": {"dimensions": [600.0, 600.0, 700.0], "weight": 20000.0},
        }
        parcel_size = sorted([float(parcel.width), float(parcel.length), float(parcel.height)])
        for key, value in sizes.items():
            if (
                parcel_size[0] <= value["dimensions"][0]
                and parcel_size[1] <= value["dimensions"][1]
                and parcel_size[2] <= value["dimensions"][2]
                and parcel.weight <= value["weight"]
            ):
                return key

        if (
            sum(parcel_size) <= MAX_PARCEL_SUM_SIZE
            and max(parcel_size) <= MAX_PARCEL_SIZE
            and parcel.weight <= MAX_PARCEL_WEIGHT
        ):
            return "2XL"

        raise ValueError("The parcel is too big!")

    @staticmethod
    def change_parcel_units(parcel: Parcel) -> Parcel:
        """Convert [kg] -> [g] and [cm] -> [mm]."""
        return Parcel(
            weight=parcel.weight * 1000,
            length=parcel.length * 10,
            height=parcel.height * 10,
            width=parcel.width * 10,
            quantity=parcel.quantity,
            parcel_type=parcel.parcel_type,
        )

    # ------------------------------------------------------------------
    # Private — error helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_error_response_msg(response: list) -> str:
        msg = "Podczas przetwarzania paczki napotkano następujące błędy: "
        for response_item in response:
            if response_item["error"]:
                msg += ", ".join(error["errorDesc"] for error in response_item["error"])
        return msg

    @staticmethod
    def _get_list_error_response(response: dict) -> list:
        return [f"{error['guid']}: {error['errorDesc']}" for error in response["error"]]

    @staticmethod
    def _service_return_error(response: list) -> bool:
        return any(response_item["error"] for response_item in response)
