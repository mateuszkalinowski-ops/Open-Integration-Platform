"""InsERT Nexo Cloud Connector — FastAPI application entry point.

Proxies requests from the Pinquark Integration Platform to on-premise
Nexo agents running at client sites.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_client import make_asgi_app

from src.api.dependencies import app_state
from src.api.routes import router
from src.config import settings
from src.services.account_manager import AccountManager
from pinquark_common.logging import setup_logging
from pinquark_common.monitoring.health import HealthChecker

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI):  # type: ignore[no-untyped-def]
    setup_logging(f"nexo-connector-v{settings.app_version}", settings.log_level)
    logger.info("Starting InsERT Nexo Cloud Connector v%s", settings.app_version)

    account_manager = AccountManager()
    account_manager.load_from_yaml()
    app_state.account_manager = account_manager

    health_checker = HealthChecker(settings.app_version)
    app_state.health_checker = health_checker

    logger.info(
        "InsERT Nexo Connector ready — agents=%d",
        len(account_manager.list_accounts()),
    )

    yield

    logger.info("Shutting down InsERT Nexo Cloud Connector")
    await account_manager.close_all()


def create_app() -> FastAPI:
    application = FastAPI(
        title="InsERT Nexo Connector",
        description=(
            "Cloud connector for InsERT Nexo ERP — proxies requests to on-premise agents. "
            "Supports contractors, products, documents, orders, and stock."
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
