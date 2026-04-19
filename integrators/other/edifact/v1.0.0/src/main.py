"""EDIFACT Container Terminal Connector — FastAPI application entry point."""

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
    setup_logging(f"edifact-connector-v{settings.app_version}", settings.log_level)
    logger.info("Starting EDIFACT Connector v%s", settings.app_version)

    account_manager = AccountManager()
    account_manager.load_from_yaml()
    app_state.account_manager = account_manager

    health_checker = HealthChecker(settings.app_version)

    async def check_external_system() -> None:
        accounts = account_manager.list_accounts()
        if accounts:
            client = account_manager.get_client(accounts[0]["name"])
            result = await client.check_health()
            if result["status"] == "unhealthy":
                raise RuntimeError(f"External system unhealthy: {result.get('error')}")

    health_checker.register_check("external_system", check_external_system)
    app_state.health_checker = health_checker

    logger.info(
        "EDIFACT Connector ready — accounts=%d, base_url=%s",
        len(account_manager.list_accounts()),
        settings.base_url,
    )

    yield

    logger.info("Shutting down EDIFACT Connector")
    await account_manager.close_all()


def create_app() -> FastAPI:
    application = FastAPI(
        title="EDIFACT Container Terminal Connector",
        description=(
            "REST/JSON connector for UN/EDIFACT container terminal messages: "
            "CODECO (gate-in/out), BAPLIE (bay plan/stowage), "
            "IFTMIN (transport instructions). "
            "Maps EDIFACT D.95B+ message concepts to clean JSON APIs."
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
