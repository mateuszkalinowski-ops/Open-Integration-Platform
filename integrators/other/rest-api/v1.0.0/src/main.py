"""REST API Gateway Connector — FastAPI application entry point."""

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from prometheus_client import make_asgi_app

from src.api.dependencies import app_state
from src.api.routes import router
from src.config import settings
from src.services.account_manager import AccountManager
from src.services.openapi_discovery import OpenAPIDiscovery
from src.services.response_parser import ResponseParser

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
async def lifespan(_application: FastAPI):  # type: ignore[no-untyped-def]
    setup_logging(f"rest-api-connector-v{settings.app_version}", settings.log_level)
    logger.info("Starting REST API Gateway Connector v%s", settings.app_version)

    ResponseParser.load_profiles(settings.profiles_dir)

    account_manager = AccountManager()
    account_manager.load_from_yaml()
    app_state.account_manager = account_manager
    app_state.discovery = OpenAPIDiscovery()

    health_checker = HealthChecker(settings.app_version)
    app_state.health_checker = health_checker

    logger.info(
        "REST API Gateway ready — accounts=%d",
        len(account_manager.list_accounts()),
    )

    yield

    logger.info("Shutting down REST API Gateway Connector")
    await account_manager.close_all()


def create_app() -> FastAPI:
    application = FastAPI(
        title="REST API Gateway Connector",
        description=(
            "Universal REST API connector for OIP. Connects to any REST/JSON system "
            "with configurable auth (Bearer, Basic, OAuth2, API Key, custom headers), "
            "response parsing profiles, and automatic endpoint discovery from OpenAPI specs."
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
