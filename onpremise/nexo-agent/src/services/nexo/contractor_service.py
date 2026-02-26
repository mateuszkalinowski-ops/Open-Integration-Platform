"""Contractor (Podmiot) CRUD operations via InsERT Nexo SDK."""

import logging
from typing import Any

from src.bridge.nexo_connection import NexoConnection
from src.bridge.nexo_types import nexo_contractor_to_model, _iterate_net_collection
from src.models.contractor import ContractorCreate, ContractorResponse, ContractorUpdate

logger = logging.getLogger(__name__)


class ContractorService:
    def __init__(self, connection: NexoConnection):
        self._conn = connection

    def _get_podmioty(self) -> Any:
        from InsERT.Moria.ModelDanych import IPodmioty  # type: ignore[import-not-found]
        return self._conn.get_typed_object(IPodmioty)

    def list_contractors(
        self,
        page: int = 1,
        page_size: int = 50,
        search: str | None = None,
    ) -> dict[str, Any]:
        podmioty = self._get_podmioty()
        query = podmioty.Dane.Wszystkie()

        all_items = _iterate_net_collection(query)

        if search:
            search_lower = search.lower()
            all_items = [
                p for p in all_items
                if search_lower in str(getattr(p, "NazwaSkrocona", "")).lower()
                or search_lower in str(getattr(p, "NIP", "")).lower()
            ]

        total = len(all_items)
        start = (page - 1) * page_size
        end = start + page_size
        page_items = all_items[start:end]

        results = [nexo_contractor_to_model(p) for p in page_items]

        return {
            "items": [r.model_dump() for r in results],
            "page": page,
            "page_size": page_size,
            "total": total,
            "has_next": end < total,
        }

    def get_contractor(self, symbol: str) -> ContractorResponse | None:
        podmioty = self._get_podmioty()
        all_items = _iterate_net_collection(podmioty.Dane.Wszystkie())

        for p in all_items:
            sygnatura = getattr(p, "Sygnatura", None)
            s = str(getattr(sygnatura, "PelnaSygnatura", "")) if sygnatura else ""
            if s == symbol:
                return nexo_contractor_to_model(p)

        return None

    def get_contractor_by_nip(self, nip: str) -> ContractorResponse | None:
        podmioty = self._get_podmioty()
        nip_clean = nip.replace("-", "").replace(" ", "")

        for p in _iterate_net_collection(podmioty.Dane.Wszystkie()):
            p_nip = str(getattr(p, "NIP", "")).replace("-", "").replace(" ", "")
            if p_nip == nip_clean:
                return nexo_contractor_to_model(p)

        return None

    def create_contractor(self, data: ContractorCreate) -> ContractorResponse:
        podmioty = self._get_podmioty()

        from InsERT.Moria.ModelDanych import IPodmiot  # type: ignore[import-not-found]

        if data.contractor_type.value == "company":
            podmiot = podmioty.UtworzFirme()
        else:
            podmiot = podmioty.UtworzOsobe()

        with self._conn.entity_scope(podmiot):
            podmiot.AutoSymbol()
            podmiot.Dane.NazwaSkrocona = data.short_name

            if data.contractor_type.value == "company" and data.full_name:
                try:
                    podmiot.Dane.Firma.Nazwa = data.full_name
                except Exception:
                    pass

            if data.nip:
                podmiot.Dane.NIPSformatowany = data.nip

            if data.regon:
                try:
                    podmiot.Dane.REGON = data.regon
                except Exception:
                    pass

            if data.first_name:
                try:
                    podmiot.Dane.Imie = data.first_name
                except Exception:
                    pass

            if data.last_name:
                try:
                    podmiot.Dane.Nazwisko = data.last_name
                except Exception:
                    pass

            for addr_data in data.addresses:
                try:
                    from InsERT.Moria.ModelDanych import typyAdresu  # type: ignore[import-not-found]

                    addr_type = typyAdresu.DaneDomyslne.Glowny
                    adres = podmiot.DodajAdres(addr_type)
                    adres.Szczegoly.Ulica = addr_data.street
                    adres.Szczegoly.NrDomu = addr_data.house_number
                    if addr_data.apartment_number:
                        adres.Szczegoly.NrLokalu = addr_data.apartment_number
                    adres.Szczegoly.KodPocztowy = addr_data.postal_code
                    adres.Szczegoly.Miejscowosc = addr_data.city
                except Exception:
                    logger.warning("Failed to add address for contractor %s", data.short_name)

            for contact_data in data.contacts:
                try:
                    from InsERT.Moria.ModelDanych import Kontakt, rodzajeKontaktu  # type: ignore[import-not-found]

                    kontakt = Kontakt()
                    podmiot.Dane.Kontakty.Add(kontakt)

                    contact_type_map = {
                        "phone": rodzajeKontaktu.DaneDomyslne.Telefon,
                        "email": rodzajeKontaktu.DaneDomyslne.Email,
                        "fax": rodzajeKontaktu.DaneDomyslne.Fax,
                        "www": rodzajeKontaktu.DaneDomyslne.WWW,
                    }
                    rodzaj = contact_type_map.get(
                        contact_data.contact_type.lower(),
                        rodzajeKontaktu.DaneDomyslne.Telefon,
                    )
                    kontakt.Rodzaj = rodzaj
                    kontakt.Wartosc = contact_data.value
                    kontakt.Podstawowy = contact_data.is_primary
                except Exception:
                    logger.warning("Failed to add contact for contractor %s", data.short_name)

            if not podmiot.Zapisz():
                errors = self._extract_errors(podmiot)
                raise ValueError(f"Failed to create contractor: {errors}")

            return nexo_contractor_to_model(podmiot.Dane)

    def update_contractor(self, symbol: str, data: ContractorUpdate) -> ContractorResponse:
        podmioty = self._get_podmioty()

        entity = None
        for p in _iterate_net_collection(podmioty.Dane.Wszystkie()):
            sygnatura = getattr(p, "Sygnatura", None)
            s = str(getattr(sygnatura, "PelnaSygnatura", "")) if sygnatura else ""
            if s == symbol:
                entity = p
                break

        if entity is None:
            raise ValueError(f"Contractor not found: {symbol}")

        podmiot = podmioty.Znajdz(entity)
        with self._conn.entity_scope(podmiot):
            if data.short_name is not None:
                podmiot.Dane.NazwaSkrocona = data.short_name

            if data.nip is not None:
                podmiot.Dane.NIPSformatowany = data.nip

            if data.full_name is not None:
                try:
                    podmiot.Dane.Firma.Nazwa = data.full_name
                except Exception:
                    pass

            if not podmiot.Zapisz():
                errors = self._extract_errors(podmiot)
                raise ValueError(f"Failed to update contractor: {errors}")

            return nexo_contractor_to_model(podmiot.Dane)

    def delete_contractor(self, symbol: str) -> bool:
        podmioty = self._get_podmioty()

        for p in _iterate_net_collection(podmioty.Dane.Wszystkie()):
            sygnatura = getattr(p, "Sygnatura", None)
            s = str(getattr(sygnatura, "PelnaSygnatura", "")) if sygnatura else ""
            if s == symbol:
                try:
                    podmioty.Usun(p)
                    return True
                except Exception:
                    logger.exception("Failed to delete contractor %s", symbol)
                    return False

        return False

    @staticmethod
    def _extract_errors(entity: Any) -> str:
        try:
            errors = []
            if hasattr(entity, "Bledy"):
                for err in _iterate_net_collection(entity.Bledy):
                    errors.append(str(err))
            return "; ".join(errors) if errors else "Unknown error"
        except Exception:
            return "Could not extract error details"
