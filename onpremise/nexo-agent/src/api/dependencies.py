"""FastAPI dependency injection — provides shared services to route handlers."""

from src.bridge.nexo_connection import NexoConnectionPool
from src.services.nexo.contractor_service import ContractorService
from src.services.nexo.product_service import ProductService
from src.services.nexo.sales_document_service import SalesDocumentService
from src.services.nexo.warehouse_document_service import WarehouseDocumentService
from src.services.nexo.order_service import OrderService
from src.services.nexo.stock_service import StockService


class AppState:
    """Holds initialized service instances shared across the application."""

    def __init__(self) -> None:
        self.connection_pool: NexoConnectionPool | None = None
        self.contractor_service: ContractorService | None = None
        self.product_service: ProductService | None = None
        self.sales_document_service: SalesDocumentService | None = None
        self.warehouse_document_service: WarehouseDocumentService | None = None
        self.order_service: OrderService | None = None
        self.stock_service: StockService | None = None
        self.health_checker: object | None = None


app_state = AppState()
