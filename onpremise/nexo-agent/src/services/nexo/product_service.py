"""Product (Asortyment) CRUD operations via InsERT Nexo SDK."""

import logging
from typing import Any

from src.bridge.nexo_connection import NexoConnection
from src.bridge.nexo_types import nexo_product_to_model, _iterate_net_collection
from src.models.product import ProductCreate, ProductResponse, ProductUpdate

logger = logging.getLogger(__name__)


class ProductService:
    def __init__(self, connection: NexoConnection):
        self._conn = connection

    def _get_asortymenty(self) -> Any:
        from InsERT.Moria.ModelDanych import IAsortymenty  # type: ignore[import-not-found]
        return self._conn.get_typed_object(IAsortymenty)

    def list_products(
        self,
        page: int = 1,
        page_size: int = 50,
        search: str | None = None,
        group: str | None = None,
    ) -> dict[str, Any]:
        asortymenty = self._get_asortymenty()
        all_items = _iterate_net_collection(asortymenty.Dane.Wszystkie())

        if search:
            sl = search.lower()
            all_items = [
                a for a in all_items
                if sl in str(getattr(a, "Nazwa", "")).lower()
                or sl in str(getattr(a, "Symbol", "")).lower()
                or sl in str(getattr(a, "EAN", "")).lower()
            ]

        if group:
            all_items = [
                a for a in all_items
                if str(getattr(a, "Grupa", "")) == group
            ]

        total = len(all_items)
        start = (page - 1) * page_size
        end = start + page_size
        page_items = all_items[start:end]

        results = [nexo_product_to_model(a) for a in page_items]

        return {
            "items": [r.model_dump() for r in results],
            "page": page,
            "page_size": page_size,
            "total": total,
            "has_next": end < total,
        }

    def get_product(self, symbol: str) -> ProductResponse | None:
        asortymenty = self._get_asortymenty()
        for a in _iterate_net_collection(asortymenty.Dane.Wszystkie()):
            if str(getattr(a, "Symbol", "")) == symbol:
                return nexo_product_to_model(a)
        return None

    def get_product_by_ean(self, ean: str) -> ProductResponse | None:
        asortymenty = self._get_asortymenty()
        for a in _iterate_net_collection(asortymenty.Dane.Wszystkie()):
            if str(getattr(a, "EAN", "")) == ean:
                return nexo_product_to_model(a)
        return None

    def create_product(self, data: ProductCreate) -> ProductResponse:
        asortymenty = self._get_asortymenty()

        from InsERT.Moria.ModelDanych import ISzablonyAsortymentu  # type: ignore[import-not-found]
        szablony = self._conn.get_typed_object(ISzablonyAsortymentu)

        asortyment = asortymenty.Utworz()
        with self._conn.entity_scope(asortyment):
            template_map = {
                "goods": szablony.DaneDomyslne.Towar,
                "service": szablony.DaneDomyslne.Usluga,
            }
            template = template_map.get(data.product_type.value, szablony.DaneDomyslne.Towar)
            asortyment.WypelnijNaPodstawieSzablonu(template)

            if data.symbol:
                asortyment.Dane.Symbol = data.symbol
            else:
                asortyment.AutoSymbol()

            asortyment.Dane.Nazwa = data.name

            if data.ean:
                asortyment.Dane.EAN = data.ean
            if data.pkwiu:
                asortyment.Dane.PKWiU = data.pkwiu
            if data.description:
                try:
                    asortyment.Dane.Opis = data.description
                except Exception:
                    pass

            for supplier_data in data.suppliers:
                try:
                    from InsERT.Moria.ModelDanych import IPodmioty  # type: ignore[import-not-found]
                    podmioty = self._conn.get_typed_object(IPodmioty)

                    dostawca = None
                    for p in _iterate_net_collection(podmioty.Dane.Wszystkie()):
                        syg = getattr(p, "Sygnatura", None)
                        if syg and str(getattr(syg, "PelnaSygnatura", "")) == supplier_data.contractor_symbol:
                            dostawca = p
                            break

                    if dostawca:
                        dane_dostawcy = asortyment.Dostawcy.Dodaj(dostawca)
                        dane_dostawcy.CenaDeklarowana = supplier_data.declared_price
                except Exception:
                    logger.warning("Failed to add supplier %s", supplier_data.contractor_symbol)

            if not asortyment.Zapisz():
                errors = self._extract_errors(asortyment)
                raise ValueError(f"Failed to create product: {errors}")

            return nexo_product_to_model(asortyment.Dane)

    def update_product(self, symbol: str, data: ProductUpdate) -> ProductResponse:
        asortymenty = self._get_asortymenty()

        entity = None
        for a in _iterate_net_collection(asortymenty.Dane.Wszystkie()):
            if str(getattr(a, "Symbol", "")) == symbol:
                entity = a
                break

        if entity is None:
            raise ValueError(f"Product not found: {symbol}")

        asortyment = asortymenty.Znajdz(entity)
        with self._conn.entity_scope(asortyment):
            if data.name is not None:
                asortyment.Dane.Nazwa = data.name
            if data.ean is not None:
                asortyment.Dane.EAN = data.ean
            if data.description is not None:
                try:
                    asortyment.Dane.Opis = data.description
                except Exception:
                    pass

            if not asortyment.Zapisz():
                errors = self._extract_errors(asortyment)
                raise ValueError(f"Failed to update product: {errors}")

            return nexo_product_to_model(asortyment.Dane)

    def delete_product(self, symbol: str) -> bool:
        asortymenty = self._get_asortymenty()
        for a in _iterate_net_collection(asortymenty.Dane.Wszystkie()):
            if str(getattr(a, "Symbol", "")) == symbol:
                try:
                    asortymenty.Usun(a)
                    return True
                except Exception:
                    logger.exception("Failed to delete product %s", symbol)
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
