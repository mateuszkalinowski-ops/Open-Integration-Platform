from abc import ABC, abstractmethod
from datetime import datetime

from pinquark_common.schemas.ecommerce import (
    Order,
    OrdersPage,
    OrderStatus,
    Product,
    PriceUpdate,
    StockItem,
)
from pinquark_common.schemas.common import SyncResult


class EcommerceIntegration(ABC):
    """Base interface for all e-commerce integrations.

    Every e-commerce integrator MUST implement the abstract methods.
    Optional methods have default implementations that raise NotImplementedError.
    """

    @abstractmethod
    async def fetch_orders(
        self,
        account_name: str,
        since: datetime | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> OrdersPage:
        """Fetch orders from the e-commerce platform."""
        ...

    @abstractmethod
    async def get_order(self, account_name: str, order_id: str) -> Order:
        """Get a single order by its external ID."""
        ...

    @abstractmethod
    async def update_order_status(
        self,
        account_name: str,
        order_id: str,
        status: OrderStatus,
    ) -> None:
        """Update order fulfillment status on the e-commerce platform."""
        ...

    @abstractmethod
    async def sync_stock(
        self,
        account_name: str,
        items: list[StockItem],
    ) -> SyncResult:
        """Synchronize stock levels to the e-commerce platform."""
        ...

    async def sync_products(
        self,
        account_name: str,
        products: list[Product],
    ) -> SyncResult:
        """Synchronize product data to the e-commerce platform."""
        raise NotImplementedError("sync_products not supported by this integration")

    async def get_product(self, account_name: str, product_id: str) -> Product:
        """Get a single product by its external ID."""
        raise NotImplementedError("get_product not supported by this integration")

    async def sync_prices(
        self,
        account_name: str,
        prices: list[PriceUpdate],
    ) -> SyncResult:
        """Synchronize prices to the e-commerce platform."""
        raise NotImplementedError("sync_prices not supported by this integration")

    async def fetch_returns(
        self,
        account_name: str,
        since: datetime | None = None,
    ) -> list[Order]:
        """Fetch return/refund orders from the platform."""
        raise NotImplementedError("fetch_returns not supported by this integration")
