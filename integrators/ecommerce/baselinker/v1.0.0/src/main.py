"""BaseLinker Integrator — FastAPI application entry point."""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_client import make_asgi_app

from src.api.dependencies import app_state
from src.api.routes import router
from src.config import settings
from src.baselinker.client import BaseLinkerClient
from src.baselinker.integration import BaseLinkerIntegration
from src.baselinker.scraper import BaseLinkerScraper
from src.models.database import StateStore
from src.services.account_manager import AccountManager
from pinquark_common.logging import setup_logging
from pinquark_common.monitoring.health import HealthChecker
from pinquark_common.kafka import KafkaMessageProducer

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI):  # type: ignore[no-untyped-def]
    setup_logging(f"baselinker-integrator-v{settings.app_version}", settings.log_level)
    logger.info("Starting BaseLinker Integrator v%s", settings.app_version)

    state_store = StateStore()
    await state_store.initialize()
    app_state.state_store = state_store

    client = BaseLinkerClient()
    app_state.client = client

    account_manager = AccountManager()
    account_manager.load_from_yaml()
    app_state.account_manager = account_manager

    integration = BaseLinkerIntegration(client, account_manager)
    app_state.integration = integration

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

    health_checker = HealthChecker(settings.app_version)

    async def check_db() -> None:
        await state_store.load_all_timestamps()

    health_checker.register_check("database", check_db)
    app_state.health_checker = health_checker

    scraper_task = None
    if settings.scraping_enabled:
        scraper = BaseLinkerScraper(client, account_manager, state_store, kafka_producer)
        app_state.scraper = scraper
        scraper_task = asyncio.create_task(scraper.start())
        logger.info("BaseLinker scraper scheduled every %ds", settings.scraping_interval_seconds)

    logger.info(
        "BaseLinker Integrator ready — accounts=%d, kafka=%s, scraping=%s",
        len(account_manager.list_accounts()),
        settings.kafka_enabled,
        settings.scraping_enabled,
    )

    yield

    logger.info("Shutting down BaseLinker Integrator")
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
        title="Pinquark BaseLinker Integrator",
        description="E-commerce integration between Pinquark platform and BaseLinker",
        version=settings.app_version,
        docs_url="/docs",
        lifespan=lifespan,
    )
    application.include_router(router)

    metrics_app = make_asgi_app()
    application.mount("/metrics", metrics_app)

    return application


app = create_app()
