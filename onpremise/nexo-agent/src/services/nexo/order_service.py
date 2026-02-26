"""Order (Zamówienie) operations via InsERT Nexo SDK."""

import logging
from typing import Any

from src.bridge.nexo_connection import NexoConnection
from src.bridge.nexo_types import nexo_order_to_model, _iterate_net_collection
from src.models.order import OrderCreate, OrderResponse, OrderType, OrderUpdate

logger = logging.getLogger(__name__)


class OrderService:
    def __init__(self, connection: NexoConnection):
        self._conn = connection

    def _get_zamowienia_od_klientow(self) -> Any:
        from InsERT.Moria.ModelDanych import IZamowieniaOdKlientow  # type: ignore[import-not-found]
        return self._conn.get_typed_object(IZamowieniaOdKlientow)

    def _get_zamowienia_do_dostawcow(self) -> Any:
        from InsERT.Moria.ModelDanych import IZamowieniaDoDostawcow  # type: ignore[import-not-found]
        return self._conn.get_typed_object(IZamowieniaDoDostawcow)

    def list_orders(
        self,
        order_type: OrderType = OrderType.FROM_CUSTOMER,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        if order_type == OrderType.FROM_CUSTOMER:
            zamowienia = self._get_zamowienia_od_klientow()
        else:
            zamowienia = self._get_zamowienia_do_dostawcow()

        all_items = _iterate_net_collection(zamowienia.Dane.Wszystkie())

        total = len(all_items)
        start = (page - 1) * page_size
        end = start + page_size
        page_items = all_items[start:end]

        results = [nexo_order_to_model(z, order_type) for z in page_items]

        return {
            "items": [r.model_dump() for r in results],
            "page": page,
            "page_size": page_size,
            "total": total,
            "has_next": end < total,
        }

    def get_order(self, order_id: int, order_type: OrderType = OrderType.FROM_CUSTOMER) -> OrderResponse | None:
        if order_type == OrderType.FROM_CUSTOMER:
            zamowienia = self._get_zamowienia_od_klientow()
        else:
            zamowienia = self._get_zamowienia_do_dostawcow()

        for z in _iterate_net_collection(zamowienia.Dane.Wszystkie()):
            if getattr(z, "Id", None) == order_id:
                return nexo_order_to_model(z, order_type)
        return None

    def create_order(self, data: OrderCreate) -> OrderResponse:
        if data.order_type == OrderType.FROM_CUSTOMER:
            zamowienia = self._get_zamowienia_od_klientow()
            zamowienie = zamowienia.UtworzZamowienieOdKlienta()
        else:
            zamowienia = self._get_zamowienia_do_dostawcow()
            zamowienie = zamowienia.UtworzZamowienieDoDostawcy()

        with self._conn.entity_scope(zamowienie):
            if data.order_type == OrderType.FROM_CUSTOMER:
                zamowienie.PodmiotyDokumentu.UstawZamawiajacegoWedlugSymbolu(data.contractor_symbol)
            else:
                zamowienie.PodmiotyDokumentu.UstawDostawceWedlugSymbolu(data.contractor_symbol)

            for pos in data.positions:
                try:
                    zamowienie.Pozycje.Dodaj(pos.product_symbol)
                except Exception:
                    logger.warning("Failed to add order position: %s", pos.product_symbol)

            zamowienie.Przelicz()

            if not zamowienie.Zapisz():
                errors = self._extract_errors(zamowienie)
                raise ValueError(f"Failed to create order: {errors}")

            return nexo_order_to_model(zamowienie.Dane, data.order_type)

    def update_order(self, order_id: int, data: OrderUpdate, order_type: OrderType = OrderType.FROM_CUSTOMER) -> OrderResponse:
        if order_type == OrderType.FROM_CUSTOMER:
            zamowienia = self._get_zamowienia_od_klientow()
        else:
            zamowienia = self._get_zamowienia_do_dostawcow()

        entity = None
        for z in _iterate_net_collection(zamowienia.Dane.Wszystkie()):
            if getattr(z, "Id", None) == order_id:
                entity = z
                break

        if entity is None:
            raise ValueError(f"Order not found: {order_id}")

        zamowienie = zamowienia.Znajdz(entity)
        with self._conn.entity_scope(zamowienie):
            if data.notes is not None:
                try:
                    zamowienie.Dane.Uwagi = data.notes
                except Exception:
                    pass

            if data.external_number is not None:
                try:
                    zamowienie.Dane.NumerZewnetrzny = data.external_number
                except Exception:
                    pass

            if not zamowienie.Zapisz():
                errors = self._extract_errors(zamowienie)
                raise ValueError(f"Failed to update order: {errors}")

            return nexo_order_to_model(zamowienie.Dane, order_type)

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
