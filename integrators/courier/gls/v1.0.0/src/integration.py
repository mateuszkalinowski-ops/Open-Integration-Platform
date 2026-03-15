"""GLS Courier Integration — migrated from meriship codebase.

Handles all GLS SOAP API interactions including:
- Session-based login/logout (adeLogin/adeLogout)
- Shipment creation (multi-step: insert -> pickup -> consign)
- Label retrieval (single and multi-parcel)
- Tracking info (adeTrackID_Get)

The GLS API uses session tokens valid for 30 minutes, with a max of 10
concurrent sessions per company.
"""

from __future__ import annotations

import base64
import logging
from contextlib import contextmanager
from http import HTTPStatus

from zeep import Client, Transport
from zeep.exceptions import Fault, TransportError

from src.config import settings
from src.schemas import GlsCredentials

logger = logging.getLogger("courier-gls")


TRACKING_URL = "https://gls-group.com/PL/pl/sledzenie-paczek?match={tracking_number}"


def unravel_parcels(parcels: list[dict]) -> list[dict]:
    """Expand parcels so each entry represents qty=1."""
    result: list[dict] = []
    for p in parcels:
        qty = p.get("quantity", 1) or 1
        for _ in range(qty):
            copy = dict(p)
            copy["quantity"] = 1
            result.append(copy)
    return result


class GlsIntegration:
    """GLS SOAP integration with session-based authentication."""

    def __init__(self) -> None:
        self.client: Client | None = None
        self._create_soap_client()

    # ------------------------------------------------------------------
    # Session management
    # ------------------------------------------------------------------

    def _login(self, credentials: GlsCredentials) -> tuple[str, int]:
        """Authenticate and get a session ID."""
        try:
            session_id = self.client.service.adeLogin(
                user_name=credentials.username,
                user_password=credentials.password,
            )
        except TransportError as exc:
            return exc.content, exc.status_code
        except Fault as exc:
            return exc.code, HTTPStatus.BAD_REQUEST

        return session_id, HTTPStatus.OK

    def _logout(self, session_id: str) -> tuple[str, int]:
        """Release the session."""
        try:
            result = self.client.service.adeLogout(session=session_id)
        except TransportError as exc:
            return exc.content, exc.status_code
        except Fault as exc:
            return exc.code, HTTPStatus.BAD_REQUEST

        return result, HTTPStatus.OK

    @contextmanager
    def _session(self, credentials: GlsCredentials):
        """Context manager that logs in, yields the session_id, then logs out."""
        session_id, status_code = self._login(credentials)
        if status_code != HTTPStatus.OK:
            raise GlsSessionError(f"GLS login failed — {session_id}", status_code)
        try:
            yield session_id
        finally:
            _, logout_status = self._logout(session_id)
            if logout_status != HTTPStatus.OK:
                logger.warning("Error logging out of GLS session: %s", session_id)

    # ------------------------------------------------------------------
    # SOAP client init
    # ------------------------------------------------------------------

    def _create_soap_client(self) -> None:
        try:
            self.client = Client(
                wsdl=settings.gls_wsdl_url,
                transport=Transport(
                    timeout=settings.soap_timeout,
                    operation_timeout=settings.soap_operation_timeout,
                ),
            )
            logger.info("SOAP client connected — %s", settings.gls_wsdl_url)
        except ConnectionError:
            logger.error("SOAP client timeout — %s", settings.gls_wsdl_url)
        except Exception:
            logger.exception("SOAP client init failed — %s", settings.gls_wsdl_url)

    # ------------------------------------------------------------------
    # Service call helper
    # ------------------------------------------------------------------

    def _call_service(self, method: str, **kwargs) -> tuple[object, tuple | None]:
        """Call a SOAP service method, returning (result, error_tuple_or_None)."""
        try:
            return getattr(self.client.service, method)(**kwargs), None
        except TransportError as exc:
            return None, (exc.content, exc.status_code)
        except Fault as exc:
            return None, (exc.code, HTTPStatus.BAD_REQUEST)

    # ------------------------------------------------------------------
    # Tracking info
    # ------------------------------------------------------------------

    def get_tracking_info(
        self,
        credentials: GlsCredentials,
        waybill_number: str,
    ) -> tuple[dict | str, int]:
        """Get tracking URL for a waybill via ``adeTrackID_Get``."""
        try:
            with self._session(credentials) as session_id:
                track_id, error = self._call_service(
                    "adeTrackID_Get",
                    session=session_id,
                    number=waybill_number,
                )
                if error:
                    return error[0], error[1]

                return {
                    "tracking_number": track_id,
                    "tracking_url": TRACKING_URL.format(tracking_number=track_id),
                }, HTTPStatus.OK
        except GlsSessionError as exc:
            return str(exc), exc.status_code

    # ------------------------------------------------------------------
    # Create shipment (multi-step flow)
    # ------------------------------------------------------------------

    def create_order(
        self,
        credentials: GlsCredentials,
        command: dict,
    ) -> tuple[dict | str, int]:
        """Create a GLS shipment.

        Multi-step flow:
        1. adePreparingBox_Insert — add shipment to buffer
        2. adePickup_Create — create proof of posting
        3. adePickup_GetConsignBinds — get new internal ID
        4. adePickup_GetConsign — retrieve waybill number
        5. adeTrackID_Get — get tracking info
        """
        try:
            with self._session(credentials) as session_id:
                # Step 1: insert into buffer
                consign_prep_data = self._get_consign(command)
                consign_id, error = self._call_service(
                    "adePreparingBox_Insert",
                    session=session_id,
                    consign_prep_data=consign_prep_data,
                )
                if error:
                    return error[0], error[1]

                # Step 2: create pickup (unless explicitly skipped)
                gls_extras = command.get("extras", {}).get("gls", {})
                pickup_create = str(gls_extras.get("not_pickup", "")).lower() != "true"

                order_id = consign_id
                if pickup_create:
                    order_id, error = self._call_service(
                        "adePickup_Create",
                        session=session_id,
                        consigns_ids=[consign_id],
                        desc=gls_extras.get("confirmation_description"),
                    )
                    if error:
                        return error[0], error[1]

                # Step 3: get consign binds
                consign_binds, error = self._call_service(
                    "adePickup_GetConsignBinds",
                    session=session_id,
                    id=order_id,
                )
                if error:
                    return error[0], error[1]

                # Step 4: get consign details with waybill
                new_consign_id = consign_binds[0]["id"]
                consign, error = self._call_service(
                    "adePickup_GetConsign",
                    session=session_id,
                    id=new_consign_id,
                )
                if error:
                    return error[0], error[1]

                waybill_number = consign["parcels"]["items"][0]["number"]
                order: dict = {
                    "id": new_consign_id,
                    "waybill_number": waybill_number,
                    "status_code": "Created",
                }

                # Step 5: tracking info (best-effort)
                tracking_info, error = self._call_service(
                    "adeTrackID_Get",
                    session=session_id,
                    number=waybill_number,
                )
                if not error:
                    order["tracking"] = tracking_info

                return self._normalize_order_item(command, order), HTTPStatus.CREATED

        except GlsSessionError as exc:
            return str(exc), exc.status_code

    # ------------------------------------------------------------------
    # Labels
    # ------------------------------------------------------------------

    def get_waybill_label_bytes(
        self,
        credentials: GlsCredentials,
        waybill_numbers: list[str],
        args: dict,
    ) -> tuple[bytes | str, int]:
        """Retrieve label PDF bytes for one or more waybills."""
        session_id = args.get("session_id")
        owns_session = False

        if not session_id:
            session_id, status_code = self._login(credentials)
            if status_code != HTTPStatus.OK:
                return f"GLS login failed — {session_id}", HTTPStatus.BAD_REQUEST
            owns_session = True

        try:
            waybill_number = waybill_numbers[0]
            parcel_id = args.get("external_id")
            if parcel_id and parcel_id == waybill_number:
                parcel_id = None

            if parcel_id is None:
                return self._get_label(session_id, waybill_number)

            consign, error = self._call_service(
                "adePickup_GetConsign",
                session=session_id,
                id=parcel_id,
            )
            if error:
                return error[0], error[1]

            parcel_list = consign["parcels"]["items"]
            if len(parcel_list) > 1:
                waybills = {"items": [p["number"] for p in parcel_list]}
                return self._get_labels(session_id, waybills, waybill_number)

            return self._get_label(session_id, waybill_number)
        finally:
            if owns_session:
                self._logout(session_id)

    def _get_label(self, session_id: str, waybill_number: str) -> tuple[bytes | str, int]:
        """Fetch a single parcel label."""
        label, error = self._call_service(
            "adePickup_GetParcelLabel",
            session=session_id,
            number=waybill_number,
            mode="roll_160x100_vertical_pdf",
        )
        if error:
            return error[0], error[1]

        return self._prepare_label_response(label)

    def _get_labels(
        self,
        session_id: str,
        waybills: dict,
        _waybill_number: str,
    ) -> tuple[bytes | str, int]:
        """Fetch labels for multiple parcels."""
        labels, error = self._call_service(
            "adePickup_GetParcelsLabels",
            session=session_id,
            numbers=waybills,
            mode="roll_160x100_vertical_pdf",
        )
        if error:
            return error[0], error[1]

        return self._prepare_label_response(labels)

    @staticmethod
    def _prepare_label_response(label_data: str) -> tuple[bytes, int]:
        """Decode base64 label data to raw PDF bytes."""
        return base64.b64decode(label_data), HTTPStatus.OK

    # ------------------------------------------------------------------
    # Private — build consign structure
    # ------------------------------------------------------------------

    def _get_consign(self, command: dict) -> dict:
        """Build the consignment data for ``adePreparingBox_Insert``."""
        receiver = command.get("receiver", {})
        shipper = command.get("shipper", {})
        parcels = command.get("parcels", [])
        content = command.get("content", "")
        shipment_date = command.get("shipment_date", command.get("shipmentDate", ""))

        gls_extras: dict = command.get("extras", {}).get("gls", {})
        srv_bool = self._get_services(command)

        if gls_extras.get("custom_attributes", {}).get("target_point"):
            srv_bool["sds"] = True

        unraveled = unravel_parcels(parcels)

        return {
            "rname1": receiver.get("first_name", ""),
            "rname2": receiver.get("last_name", ""),
            "rname3": None,
            "rcountry": receiver.get("country_code", "PL"),
            "rzipcode": self._strip_postcode(receiver.get("postal_code", "")),
            "rcity": receiver.get("city", ""),
            "rstreet": f"{receiver.get('street', '')} {receiver.get('building_number', '')}",
            "rphone": receiver.get("phone", ""),
            "rcontact": receiver.get("email", ""),
            "references": content,
            "notes": "",
            "quantity": sum(p.get("quantity", 1) for p in unraveled),
            "weight": sum(p.get("weight", 0) for p in unraveled),
            "date": shipment_date,
            "sendaddr": self._get_sender(shipper),
            "srv_bool": srv_bool,
            "srv_daw": {
                "name": f"{receiver.get('first_name', '')} {receiver.get('last_name', '')}",
                "building": receiver.get("building_number", ""),
                "floor": None,
                "room": None,
                "phone": receiver.get("phone", ""),
                "altrec": receiver.get("contact_person", ""),
            }
            if gls_extras.get("bringing_pack")
            else None,
            "srv_ppe": {
                "sname1": shipper.get("first_name", ""),
                "sname2": shipper.get("last_name", ""),
                "scountry": shipper.get("country_code", "PL"),
                "szipcode": shipper.get("postal_code", ""),
                "scity": shipper.get("city", ""),
                "sstreet": shipper.get("street", ""),
                "sphone": shipper.get("phone", ""),
                "scontact": shipper.get("email", ""),
                "rname1": receiver.get("first_name", ""),
                "rname2": receiver.get("last_name", ""),
                "rcountry": receiver.get("country_code", "PL"),
                "rzipcode": receiver.get("postal_code", ""),
                "rcity": receiver.get("city", ""),
                "rstreet": receiver.get("street", ""),
                "rphone": receiver.get("phone", ""),
                "rcontact": receiver.get("email", ""),
                "references": content,
                "weight": sum(p.get("weight", 0) for p in unraveled),
            },
            "srv_sds": {
                "id": gls_extras.get("custom_attributes", {}).get("target_point"),
            },
            "parcels": {
                "items": [{"weight": p.get("weight", 0)} for p in unraveled],
            },
        }

    # ------------------------------------------------------------------
    # Private — sender / services
    # ------------------------------------------------------------------

    @staticmethod
    def _get_sender(sender: dict) -> dict:
        return {
            "name1": sender.get("first_name", ""),
            "name2": sender.get("last_name", ""),
            "name3": "",
            "country": sender.get("country_code", "PL"),
            "zipcode": GlsIntegration._strip_postcode(sender.get("postal_code", "")),
            "city": sender.get("city", ""),
            "street": sender.get("street", ""),
        }

    @staticmethod
    def _get_services(command: dict) -> dict:
        """Build srv_bool flags from command extras."""
        gls_extras: dict = command.get("extras", {}).get("gls", {})
        return {
            "cod": command.get("cod", False),
            "cod_amount": command.get("cod_value", command.get("codValue", 0)),
            "rod": gls_extras.get("rod", False),
            "daw": gls_extras.get("bringing_pack", False),
            "pr": gls_extras.get("return_pack", False),
            "s10": gls_extras.get("delivery9", False),
            "s12": gls_extras.get("delivery12", False),
            "sat": gls_extras.get("delivery_saturday", False),
            "srs": gls_extras.get("shop_return_service", False),
            "sds": gls_extras.get("sds", False),
            "exc": gls_extras.get("exchange_service", False),
        }

    # ------------------------------------------------------------------
    # Private — normalisation
    # ------------------------------------------------------------------

    def _normalize_order_item(self, command: dict, order: dict) -> dict:
        tracking = order.get("tracking")
        shipper = command.get("shipper", {})
        receiver = command.get("receiver", {})

        result: dict = {
            "id": order["id"],
            "waybill_number": order["waybill_number"],
            "shipper": self._normalize_shipment_party(shipper),
            "receiver": self._normalize_shipment_party(receiver),
            "orderStatus": order["status_code"],
        }

        if tracking:
            result["tracking"] = {
                "tracking_number": tracking,
                "tracking_url": TRACKING_URL.format(tracking_number=tracking),
            }

        return result

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


class GlsSessionError(Exception):
    """Raised when GLS session login fails."""

    def __init__(self, message: str, status_code: int = HTTPStatus.BAD_REQUEST) -> None:
        super().__init__(message)
        self.status_code = status_code
