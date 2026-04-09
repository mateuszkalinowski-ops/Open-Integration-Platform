"""Symfonia ERP WebAPI Connector — FastAPI application entry point.

Integrates with Symfonia ERP Handel and Finanse i Księgowość modules
via the Symfonia WebAPI REST/JSON interface.
"""

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from prometheus_client import make_asgi_app

from src.api.dependencies import app_state
from src.api.routes import router
from src.config import settings
from src.services.symfonia_client import SymfoniaClient

try:
    sdk_path = Path(__file__).resolve().parents[5] / "sdk/python"
    if sdk_path.exists() and str(sdk_path) not in sys.path:
        sys.path.insert(0, str(sdk_path))
except (IndexError, OSError):
    pass

try:
    from pinquark_connector_sdk.legacy import augment_legacy_fastapi_app
except ImportError:
    augment_legacy_fastapi_app = None  # type: ignore[assignment,misc]
from pinquark_common.logging import setup_logging
from pinquark_common.monitoring.health import HealthChecker

logger = logging.getLogger(__name__)
MANIFEST_PATH = Path(__file__).resolve().parents[1] / "connector.yaml"


@asynccontextmanager
async def lifespan(application: FastAPI):  # type: ignore[no-untyped-def]
    setup_logging(f"symfonia-connector-v{settings.app_version}", settings.log_level)
    logger.info("Starting Symfonia ERP Connector v%s", settings.app_version)

    symfonia_client = SymfoniaClient(
        base_url=settings.webapi_url,
        application_guid=settings.application_guid,
        device_name=settings.device_name,
        session_timeout_minutes=settings.session_timeout_minutes,
        connect_timeout=settings.http_connect_timeout,
        read_timeout=settings.http_read_timeout,
        max_retries=settings.max_retries,
    )
    app_state.symfonia_client = symfonia_client

    health_checker = HealthChecker(settings.app_version)
    app_state.health_checker = health_checker

    logger.info(
        "Symfonia ERP Connector ready — webapi_url=%s, device=%s",
        settings.webapi_url,
        settings.device_name,
    )

    yield

    logger.info("Shutting down Symfonia ERP Connector")
    await symfonia_client.close()


def create_app() -> FastAPI:
    application = FastAPI(
        title="Symfonia ERP Connector",
        description=(
            "Connector for Symfonia ERP WebAPI — integrates with Symfonia Handel "
            "(trade, warehouse, sales, purchases) and Symfonia Finanse i Księgowość "
            "(finance & accounting) modules via REST/JSON API."
        ),
        version=settings.app_version,
        docs_url="/docs",
        lifespan=lifespan,
    )
    application.include_router(router)

    metrics_app = make_asgi_app()
    application.mount("/metrics", metrics_app)

    if augment_legacy_fastapi_app is not None:
        return augment_legacy_fastapi_app(application, manifest_path=MANIFEST_PATH)
    return application


app = create_app()
