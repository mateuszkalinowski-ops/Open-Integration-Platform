"""KSeF Integrator — FastAPI application entry point."""

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
    setup_logging(f"ksef-integrator-v{settings.app_version}", settings.log_level)
    logger.info("Starting KSeF Integrator v%s", settings.app_version)

    account_manager = AccountManager()
    account_manager.load_from_yaml()
    app_state.account_manager = account_manager

    health_checker = HealthChecker(settings.app_version)

    async def check_ksef() -> None:
        accounts = account_manager.list_accounts()
        if accounts:
            client = account_manager.get_client(accounts[0].name)
            result = await client.check_health()
            if result["status"] == "unhealthy":
                raise RuntimeError(f"KSeF unhealthy: {result.get('error')}")

    health_checker.register_check("ksef_api", check_ksef)
    app_state.health_checker = health_checker

    logger.info(
        "KSeF Integrator ready — accounts=%d, environment=%s",
        len(account_manager.list_accounts()),
        settings.default_environment.value,
    )

    yield

    logger.info("Shutting down KSeF Integrator")
    await account_manager.close_all()


def create_app() -> FastAPI:
    application = FastAPI(
        title="KSeF Connector",
        description=(
            "Krajowy System e-Faktur (KSeF 2.0) — "
            "wysyłka, odbiór i weryfikacja faktur ustrukturyzowanych. "
            "Supports test, demo, and production environments."
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
