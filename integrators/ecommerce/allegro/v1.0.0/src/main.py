"""Allegro Integrator — FastAPI application entry point."""

import asyncio
import logging
import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_client import make_asgi_app

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
from src.allegro.auth import AllegroAuthManager
from src.allegro.client import AllegroClient
from src.allegro.integration import AllegroIntegration
from src.allegro.scraper import OrderScraper
from src.api.dependencies import app_state
from src.api.routes import router
from src.config import settings
from src.models.database import TokenStore
from src.services.account_manager import AccountManager
from pinquark_common.logging import setup_logging
from pinquark_common.monitoring.health import HealthChecker
from pinquark_common.kafka import KafkaMessageProducer

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI):
    setup_logging(f"allegro-integrator-v{settings.app_version}", settings.log_level)
    logger.info("Starting Allegro Integrator v%s", settings.app_version)

    # Database
    token_store = TokenStore()
    await token_store.initialize()
    app_state.token_store = token_store

    # Auth manager
    auth_manager = AllegroAuthManager(token_store)
    await auth_manager.initialize()
    app_state.auth_manager = auth_manager

    # Allegro HTTP client
    client = AllegroClient(auth_manager)
    app_state.client = client

    # Account manager
    account_manager = AccountManager()
    account_manager.load_from_yaml()
    app_state.account_manager = account_manager

    # Integration service
    integration = AllegroIntegration(client, account_manager)
    app_state.integration = integration

    # Kafka producer
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

    # Health checker
    health_checker = HealthChecker(settings.app_version)

    async def check_db():
        await token_store.load_all_last_event_ids()

    health_checker.register_check("database", check_db)
    app_state.health_checker = health_checker

    # Order scraper (background task)
    scraper_task = None
    if settings.scraping_enabled:
        scraper = OrderScraper(client, account_manager, token_store, kafka_producer)
        app_state.scraper = scraper
        scraper_task = asyncio.create_task(scraper.start())
        logger.info("Order scraper scheduled every %ds", settings.scraping_interval_seconds)

    logger.info(
        "Allegro Integrator ready — accounts=%d, kafka=%s, scraping=%s",
        len(account_manager.list_accounts()),
        settings.kafka_enabled,
        settings.scraping_enabled,
    )

    yield

    # Shutdown
    logger.info("Shutting down Allegro Integrator")
    if app_state.scraper:
        await app_state.scraper.stop()
    if scraper_task:
        scraper_task.cancel()
        try:
            await scraper_task
        except asyncio.CancelledError:
            pass
    if kafka_producer:
        await kafka_producer.stop()
    await client.close()


def create_app() -> FastAPI:
    application = FastAPI(
        title="Allegro Connector",
        description="Allegro marketplace integration — orders, offers, shipping, payments and more",
        version=settings.app_version,
        docs_url="/docs",
        lifespan=lifespan,
    )
    application.include_router(router)

    metrics_app = make_asgi_app()
    application.mount("/metrics", metrics_app)

    return application


app = create_app()
if augment_legacy_fastapi_app is not None:
    app = augment_legacy_fastapi_app(
        app,
        manifest_path=Path(__file__).resolve().parent.parent / "connector.yaml",
    )
