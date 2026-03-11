"""S3 Integrator — FastAPI application entry point."""

import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from prometheus_client import make_asgi_app

from src.api.dependencies import app_state
from src.api.routes import router
from src.config import settings
from src.s3_client.integration import S3Integration
from src.s3_client.poller import ObjectPoller
from src.models.database import StateStore
from src.services.account_manager import AccountManager

sdk_path = Path(__file__).resolve().parents[5] / "sdk/python"
if str(sdk_path) not in sys.path:
    sys.path.insert(0, str(sdk_path))

from pinquark_connector_sdk.legacy import augment_legacy_fastapi_app
from pinquark_common.logging import setup_logging
from pinquark_common.monitoring.health import HealthChecker
from pinquark_common.kafka import KafkaMessageProducer

logger = logging.getLogger(__name__)
MANIFEST_PATH = Path(__file__).resolve().parents[1] / "connector.yaml"


@asynccontextmanager
async def lifespan(application: FastAPI):  # type: ignore[no-untyped-def]
    setup_logging(f"s3-integrator-v{settings.app_version}", settings.log_level)
    logger.info("Starting S3 Integrator v%s", settings.app_version)

    state_store = StateStore()
    await state_store.initialize()
    app_state.state_store = state_store

    account_manager = AccountManager()
    account_manager.load_from_yaml()
    app_state.account_manager = account_manager

    kafka_producer = None
    if settings.kafka_enabled:
        kafka_producer = KafkaMessageProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            security_protocol=settings.kafka_security_protocol,
            sasl_mechanism=settings.kafka_sasl_mechanism,
            sasl_username=settings.kafka_sasl_username,
            sasl_password=settings.kafka_sasl_password,
        )
        await kafka_producer.start()
        app_state.kafka_producer = kafka_producer

    integration = S3Integration(account_manager, kafka_producer=kafka_producer)
    app_state.integration = integration

    health_checker = HealthChecker(settings.app_version)

    async def check_db() -> None:
        await state_store.load_all_timestamps()

    health_checker.register_check("database", check_db)
    app_state.health_checker = health_checker

    poller_task = None
    if settings.polling_enabled:
        poller = ObjectPoller(account_manager, state_store, kafka_producer)
        app_state.poller = poller
        poller_task = asyncio.create_task(poller.start())
        logger.info("Object poller scheduled every %ds", settings.polling_interval_seconds)

    logger.info(
        "S3 Integrator ready — accounts=%d, kafka=%s, polling=%s",
        len(account_manager.list_accounts()),
        settings.kafka_enabled,
        settings.polling_enabled,
    )

    yield

    logger.info("Shutting down S3 Integrator")
    if app_state.poller:
        await app_state.poller.stop()
    if poller_task:
        poller_task.cancel()
        try:
            await poller_task
        except asyncio.CancelledError:
            pass
    if kafka_producer:
        await kafka_producer.stop()


def create_app() -> FastAPI:
    application = FastAPI(
        title="Amazon S3 Connector",
        description=(
            "Amazon S3 and S3-compatible object storage integration — "
            "upload, download, list, delete, copy objects and manage buckets"
        ),
        version=settings.app_version,
        docs_url="/docs",
        lifespan=lifespan,
    )
    application.include_router(router)

    metrics_app = make_asgi_app()
    application.mount("/metrics", metrics_app)

    return augment_legacy_fastapi_app(application, manifest_path=MANIFEST_PATH)


app = create_app()
