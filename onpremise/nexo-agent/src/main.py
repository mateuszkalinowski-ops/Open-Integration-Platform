"""InsERT Nexo On-Premise Agent — FastAPI application entry point.

Bridges the InsERT Nexo ERP system (Subiekt) with the Pinquark Cloud
Integration Platform via a local REST API, pythonnet SDK bridge,
and background sync/heartbeat services.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_client import make_asgi_app

from src.api.dependencies import app_state
from src.api.routes import router
from src.bridge.nexo_connection import NexoConnectionPool, NexoProduct
from src.config import settings
from src.services.nexo.contractor_service import ContractorService
from src.services.nexo.product_service import ProductService
from src.services.nexo.sales_document_service import SalesDocumentService
from src.services.nexo.warehouse_document_service import WarehouseDocumentService
from src.services.nexo.order_service import OrderService
from src.services.nexo.stock_service import StockService
from src.sync.heartbeat import HeartbeatService
from src.sync.offline_queue import OfflineQueue
from src.sync.sync_engine import SyncEngine

logger = logging.getLogger(__name__)


def _setup_logging() -> None:
    log_format = (
        '{"timestamp":"%(asctime)s","level":"%(levelname)s",'
        '"service":"%(name)s","message":"%(message)s"}'
    )
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format=log_format,
    )


@asynccontextmanager
async def lifespan(application: FastAPI):  # type: ignore[no-untyped-def]
    _setup_logging()
    logger.info("Starting InsERT Nexo On-Premise Agent v%s", settings.app_version)

    offline_queue = OfflineQueue(settings.offline_queue_db)
    await offline_queue.initialize()

    product_enum = NexoProduct(settings.nexo_product)
    pool = NexoConnectionPool(
        sql_server=settings.sql_server,
        sql_database=settings.sql_database,
        operator_login=settings.nexo_operator_login,
        operator_password=settings.nexo_operator_password,
        product=product_enum,
        sdk_bin_path=settings.sdk_bin_path,
        windows_auth=settings.sql_auth_windows,
        sql_username=settings.sql_username,
        sql_password=settings.sql_password,
        default_warehouse=settings.default_warehouse,
        default_branch=settings.default_branch,
    )

    try:
        conn = pool.ensure_connected()
        logger.info("Connected to InsERT Nexo: %s / %s", settings.sql_server, settings.sql_database)
    except Exception:
        logger.warning(
            "Could not connect to InsERT Nexo on startup — will retry on first request",
            exc_info=True,
        )

    app_state.connection_pool = pool
    app_state.contractor_service = ContractorService(pool._connection)
    app_state.product_service = ProductService(pool._connection)
    app_state.sales_document_service = SalesDocumentService(pool._connection)
    app_state.warehouse_document_service = WarehouseDocumentService(pool._connection)
    app_state.order_service = OrderService(pool._connection)
    app_state.stock_service = StockService(pool._connection)

    heartbeat = HeartbeatService(pool, offline_queue)
    await heartbeat.start()

    sync_engine = SyncEngine(pool, offline_queue)
    await sync_engine.start()

    logger.info(
        "InsERT Nexo Agent ready — product=%s, warehouse=%s, sync_interval=%ds",
        settings.nexo_product,
        settings.default_warehouse,
        settings.sync_interval_seconds,
    )

    yield

    logger.info("Shutting down InsERT Nexo Agent")
    await sync_engine.stop()
    await heartbeat.stop()
    pool.shutdown()


def create_app() -> FastAPI:
    application = FastAPI(
        title="InsERT Nexo On-Premise Agent",
        description=(
            "On-premise agent connecting InsERT Nexo ERP (Subiekt) "
            "to the Pinquark Integration Platform. "
            "Provides REST API for contractors, products, documents, orders, and stock."
        ),
        version=settings.app_version,
        docs_url="/docs",
        lifespan=lifespan,
    )
    application.include_router(router)

    metrics_app = make_asgi_app()
    application.mount("/metrics", metrics_app)

    return application


app = create_app()
