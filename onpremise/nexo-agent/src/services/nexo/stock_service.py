"""Stock level queries via InsERT Nexo SDK."""

import logging
from datetime import datetime, timezone
from typing import Any

from src.bridge.nexo_connection import NexoConnection
from src.bridge.nexo_types import _iterate_net_collection, _safe_str, _safe_float
from src.models.stock import StockLevel, StockQuery, WarehouseStock

logger = logging.getLogger(__name__)


class StockService:
    def __init__(self, connection: NexoConnection):
        self._conn = connection

    def get_stock_levels(self, query: StockQuery | None = None) -> WarehouseStock:
        """Query current stock levels from Nexo."""
        from InsERT.Moria.ModelDanych import IAsortymenty  # type: ignore[import-not-found]
        asortymenty = self._conn.get_typed_object(IAsortymenty)

        all_products = _iterate_net_collection(asortymenty.Dane.Wszystkie())

        if query and query.product_symbols:
            all_products = [
                a for a in all_products
                if _safe_str(getattr(a, "Symbol", "")) in query.product_symbols
            ]

        page = (query.page if query else 1) or 1
        page_size = (query.page_size if query else 100) or 100
        start = (page - 1) * page_size
        end = start + page_size
        page_products = all_products[start:end]

        items: list[StockLevel] = []
        warehouse = (query.warehouse_symbol if query else None) or self._conn._default_warehouse

        for prod in page_products:
            try:
                stock_data = self._get_product_stock(prod, warehouse)
                if stock_data:
                    if query and query.only_available and stock_data.quantity_available <= 0:
                        continue
                    items.append(stock_data)
            except Exception:
                symbol = _safe_str(getattr(prod, "Symbol", "?"))
                logger.debug("Could not get stock for product %s", symbol)

        return WarehouseStock(
            warehouse_symbol=warehouse or "",
            items=items,
            total_products=len(items),
            as_of=datetime.now(timezone.utc),
        )

    def get_stock_for_product(self, product_symbol: str, warehouse_symbol: str = "") -> StockLevel | None:
        """Get stock level for a single product."""
        from InsERT.Moria.ModelDanych import IAsortymenty  # type: ignore[import-not-found]
        asortymenty = self._conn.get_typed_object(IAsortymenty)

        for a in _iterate_net_collection(asortymenty.Dane.Wszystkie()):
            if _safe_str(getattr(a, "Symbol", "")) == product_symbol:
                wh = warehouse_symbol or self._conn._default_warehouse
                return self._get_product_stock(a, wh)

        return None

    def _get_product_stock(self, product: Any, warehouse_symbol: str) -> StockLevel | None:
        """Extract stock information from a product entity.

        Nexo stores stock on the Asortyment entity via StanyMagazynowe collection
        or via dedicated stock queries through the Sfera API.
        """
        symbol = _safe_str(getattr(product, "Symbol", ""))
        name = _safe_str(getattr(product, "Nazwa", ""))

        qty_available = 0.0
        qty_reserved = 0.0
        qty_total = 0.0

        try:
            stany = getattr(product, "StanyMagazynowe", None)
            if stany is not None:
                for stan in _iterate_net_collection(stany):
                    mag = _safe_str(getattr(stan, "SymbolMagazynu", ""))
                    if warehouse_symbol and mag != warehouse_symbol:
                        continue
                    qty_available += _safe_float(getattr(stan, "Dostepna", 0))
                    qty_reserved += _safe_float(getattr(stan, "Zarezerwowana", 0))
                    qty_total += _safe_float(getattr(stan, "Calkowita", 0))
        except Exception:
            try:
                qty_total = _safe_float(getattr(product, "StanMagazynowy", 0))
                qty_available = qty_total
            except Exception:
                pass

        unit = _safe_str(
            getattr(
                getattr(product, "PodstawowaJednostkaMiaryAsortymentu", None),
                "Symbol",
                "szt",
            )
        )

        return StockLevel(
            product_symbol=symbol,
            product_name=name,
            warehouse_symbol=warehouse_symbol,
            quantity_available=qty_available,
            quantity_reserved=qty_reserved,
            quantity_total=qty_total,
            unit=unit,
            last_updated=datetime.now(timezone.utc),
        )
