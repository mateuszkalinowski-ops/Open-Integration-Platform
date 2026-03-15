"""Email Client Integrator — FastAPI application entry point."""

import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI
from prometheus_client import make_asgi_app

from src.api.dependencies import app_state
from src.api.routes import router
from src.config import EmailAccountConfig, settings
from src.email_client.integration import EmailIntegration
from src.email_client.poller import EmailPoller
from src.models.database import StateStore
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
from pinquark_common.kafka import KafkaMessageProducer

logger = logging.getLogger(__name__)
MANIFEST_PATH = Path(__file__).resolve().parents[1] / "connector.yaml"

_CREDENTIAL_REFRESH_INTERVAL = 300


async def _fetch_credentials_once(
    account_manager: AccountManager,
    poller: EmailPoller | None,
    integration: EmailIntegration | None = None,
) -> int:
    """Fetch email credentials from the platform vault and register them."""
    if not settings.platform_api_url:
        return 0
    registered = 0
    try:
        headers: dict[str, str] = {"X-Connector-Name": "email-client"}
        if settings.platform_internal_secret:
            headers["X-Internal-Secret"] = settings.platform_internal_secret
        elif settings.platform_api_key:
            headers["X-API-Key"] = settings.platform_api_key
        async with httpx.AsyncClient(timeout=15.0, headers=headers) as client:
            resp = await client.get(
                f"{settings.platform_api_url}/internal/connector-credentials/email-client",
            )
            if resp.status_code != 200:
                logger.info(
                    "No credentials from platform (HTTP %d), waiting",
                    resp.status_code,
                )
                return 0
            accounts = resp.json()
            if not isinstance(accounts, list):
                return 0
            for acct in accounts:
                cred_name = acct.get("credential_name", "default")
                tenant_id = acct.get("tenant_id", "")
                account_key = f"{tenant_id}:{cred_name}" if tenant_id else cred_name
                creds = acct.get("credentials", {})
                email_address = creds.get("email_address", "")
                imap_host = creds.get("imap_host", "")
                if not email_address or not imap_host:
                    continue
                raw_interval = creds.get("polling_interval_seconds")
                account = EmailAccountConfig(
                    name=account_key,
                    tenant_id=tenant_id,
                    email_address=email_address,
                    username=creds.get("username", ""),
                    password=creds.get("password", ""),
                    imap_host=imap_host,
                    imap_port=int(creds.get("imap_port", "993")),
                    smtp_host=creds.get("smtp_host", ""),
                    smtp_port=int(creds.get("smtp_port", "587")),
                    use_ssl=creds.get("use_ssl", "true").lower()
                    in ("true", "1", "yes"),
                    polling_folder=creds.get("polling_folder", "INBOX"),
                    polling_interval_seconds=int(raw_interval) if raw_interval else None,
                )
                old = account_manager.get_account(account_key)
                account_manager.add_account(account)
                creds_changed = old and (
                    old.login != account.login
                    or old.password != account.password
                    or old.imap_host != account.imap_host
                    or old.imap_port != account.imap_port
                    or old.smtp_host != account.smtp_host
                    or old.smtp_port != account.smtp_port
                    or old.use_ssl != account.use_ssl
                )
                if creds_changed:
                    if poller:
                        await poller.reset_imap_client(account_key)
                    if integration:
                        await integration.invalidate_clients(account_key)
                    logger.info("Credentials changed for account=%s, clients reset", account_key)
                registered += 1
            logger.info(
                "Credential refresh: %d account(s) registered from platform",
                registered,
            )
    except Exception:
        logger.warning("Could not fetch credentials from platform", exc_info=True)
    return registered


async def _credential_refresh_loop(
    account_manager: AccountManager,
    poller: EmailPoller | None,
    integration: EmailIntegration | None = None,
    initial_delay: int = 15,
) -> None:
    """Periodically refresh credentials from the platform vault.

    Starts with a short initial_delay (for retry after startup failure),
    then switches to _CREDENTIAL_REFRESH_INTERVAL.
    """
    delay = initial_delay
    while True:
        await asyncio.sleep(delay)
        try:
            count = await _fetch_credentials_once(account_manager, poller, integration)
            delay = _CREDENTIAL_REFRESH_INTERVAL
            if count == 0 and delay == _CREDENTIAL_REFRESH_INTERVAL:
                delay = 30
        except Exception:
            logger.warning("Credential refresh failed", exc_info=True)
            delay = min(delay * 2, _CREDENTIAL_REFRESH_INTERVAL)


@asynccontextmanager
async def lifespan(application: FastAPI):  # type: ignore[no-untyped-def]
    setup_logging(f"email-client-integrator-v{settings.app_version}", settings.log_level)
    logger.info("Starting Email Client Integrator v%s", settings.app_version)

    state_store = StateStore()
    await state_store.initialize()
    app_state.state_store = state_store

    account_manager = AccountManager()
    account_manager.load_from_yaml()
    app_state.account_manager = account_manager

    integration = EmailIntegration(account_manager)
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

    poller: EmailPoller | None = None
    poller_task = None
    if settings.polling_enabled:
        poller = EmailPoller(account_manager, state_store, kafka_producer)
        app_state.poller = poller

    await _fetch_credentials_once(account_manager, poller, integration)

    if poller:
        poller_task = asyncio.create_task(poller.start())
        logger.info("Email poller scheduled every %ds", settings.polling_interval_seconds)

    cred_refresh_task = asyncio.create_task(
        _credential_refresh_loop(account_manager, poller, integration)
    )

    logger.info(
        "Email Client Integrator ready — accounts=%d, kafka=%s, polling=%s",
        len(account_manager.list_accounts()),
        settings.kafka_enabled,
        settings.polling_enabled,
    )

    yield

    logger.info("Shutting down Email Client Integrator")
    cred_refresh_task.cancel()
    try:
        await cred_refresh_task
    except asyncio.CancelledError:
        pass
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
    await integration.close()


def create_app() -> FastAPI:
    application = FastAPI(
        title="Email Client Connector",
        description="IMAP/SMTP email integration — send and receive emails at configurable intervals",
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
