"""WooCommerce Integrator — FastAPI application entry point."""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_client import make_asgi_app

from src.woocommerce.auth import WooCommerceAuth
from src.woocommerce.client import WooCommerceClient
from src.woocommerce.integration import WooCommerceIntegration
from src.woocommerce.scraper import OrderScraper
from src.api.dependencies import app_state
from src.api.routes import router
from src.config import settings
from src.models.database import StateStore
from src.services.account_manager import AccountManager
from pinquark_common.logging import setup_logging
from pinquark_common.monitoring.health import HealthChecker
from pinquark_common.kafka import KafkaMessageProducer

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI):
    setup_logging(f"woocommerce-integrator-v{settings.app_version}", settings.log_level)
    logger.info("Starting WooCommerce Integrator v%s", settings.app_version)

    # Database / state store
    state_store = StateStore()
    await state_store.initialize()
    app_state.state_store = state_store

    # Auth manager
    auth = WooCommerceAuth()
    app_state.auth = auth

    # Account manager
    account_manager = AccountManager()
    account_manager.load_from_yaml()
    app_state.account_manager = account_manager

    # Register auth for each account
    for account in account_manager.list_accounts():
        auth.register_account(
            account.name, account.store_url, account.consumer_key,
            account.consumer_secret, account.api_version,
        )

    # WooCommerce HTTP client
    client = WooCommerceClient(auth)
    app_state.client = client

    # Integration service
    integration = WooCommerceIntegration(client, account_manager)
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
        await state_store.get_all_states()

    health_checker.register_check("database", check_db)
    app_state.health_checker = health_checker

    # Order scraper (background task)
    scraper_task = None
    if settings.scraping_enabled and settings.scraping_orders_enabled:
        scraper = OrderScraper(client, account_manager, state_store, kafka_producer)
        app_state.scraper = scraper
        scraper_task = asyncio.create_task(scraper.start())
        logger.info("Order scraper scheduled every %ds", settings.scraping_interval_seconds)

    logger.info(
        "WooCommerce Integrator ready — accounts=%d, kafka=%s, scraping=%s",
        len(account_manager.list_accounts()),
        settings.kafka_enabled,
        settings.scraping_enabled,
    )

    yield

    # Shutdown
    logger.info("Shutting down WooCommerce Integrator")
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
        title="pinquark WooCommerce Integrator",
        description="E-commerce integration between pinquark WMS and WooCommerce stores",
        version=settings.app_version,
        docs_url="/docs",
        lifespan=lifespan,
    )
    application.include_router(router)

    metrics_app = make_asgi_app()
    application.mount("/metrics", metrics_app)

    return application


app = create_app()
