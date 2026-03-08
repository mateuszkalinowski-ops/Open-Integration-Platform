"""Pinquark WMS Integration REST API connector.

Proxies requests to the Pinquark WMS integration-rest application.
Endpoints mirror the official Pinquark Integration REST API documentation.
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.client import PinquarkWmsClient, WriteResult
from src.config import settings
from src.event_poller import EventPoller
from src.schemas import (
    Article,
    ArticleBatch,
    Contractor,
    DeleteCommand,
    Document,
    DocumentWrapper,
    PositionDeleteCommand,
    PositionWrapper,
    WmsCredentials,
)
from pinquark_common.kafka import KafkaMessageProducer

logger = logging.getLogger("pinquark-wms")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

wms_client = PinquarkWmsClient()

_kafka_producer: KafkaMessageProducer | None = None
event_poller: EventPoller | None = None


_CREDENTIAL_REFRESH_INTERVAL = 300


async def _fetch_credentials_once() -> int:
    """Fetch WMS credentials from platform vault. Returns count of accounts registered."""
    if not settings.platform_api_url:
        return 0
    registered = 0
    try:
        headers: dict[str, str] = {}
        if settings.platform_internal_secret:
            headers["X-Internal-Secret"] = settings.platform_internal_secret
        async with httpx.AsyncClient(timeout=15.0, headers=headers) as client:
            resp = await client.get(
                f"{settings.platform_api_url}/internal/connector-credentials/pinquark-wms",
            )
            if resp.status_code == 200:
                accounts = resp.json()
                if isinstance(accounts, list):
                    for acct in accounts:
                        name = acct.get("credential_name", "default")
                        creds_data = acct.get("credentials", {})
                        if creds_data.get("api_url") and creds_data.get("username"):
                            creds = WmsCredentials(
                                api_url=creds_data["api_url"],
                                username=creds_data["username"],
                                password=creds_data.get("password", ""),
                            )
                            event_poller.register_credentials(name, creds)
                            registered += 1
                elif isinstance(accounts, dict) and accounts.get("api_url"):
                    creds = WmsCredentials(
                        api_url=accounts["api_url"],
                        username=accounts.get("username", ""),
                        password=accounts.get("password", ""),
                    )
                    event_poller.register_credentials("default", creds)
                    registered = 1
                logger.info(
                    "Credential refresh: %d account(s) registered from platform",
                    registered,
                )
            else:
                logger.info(
                    "No credentials from platform (HTTP %d), poller waiting",
                    resp.status_code,
                )
    except Exception:
        logger.warning("Could not fetch credentials from platform", exc_info=True)
    return registered


async def _credential_refresh_loop() -> None:
    """Periodically re-fetch credentials so new ones are picked up without restart."""
    await asyncio.sleep(10)
    while True:
        await _fetch_credentials_once()
        await asyncio.sleep(_CREDENTIAL_REFRESH_INTERVAL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _kafka_producer, event_poller

    if settings.kafka_enabled:
        _kafka_producer = KafkaMessageProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            security_protocol=settings.kafka_security_protocol,
        )
        await _kafka_producer.start()
        logger.info("Kafka producer started: %s", settings.kafka_bootstrap_servers)

    event_poller = EventPoller(wms_client, kafka_producer=_kafka_producer)
    await event_poller.start()
    cred_task = asyncio.create_task(_credential_refresh_loop())
    yield
    cred_task.cancel()
    await event_poller.stop()
    if _kafka_producer:
        await _kafka_producer.stop()
    await wms_client.close()


app = FastAPI(
    title="Pinquark WMS Connector",
    description="Connector for Pinquark WMS Integration REST API",
    version="1.0.0",
    lifespan=lifespan,
)


# --- Health ---

@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "healthy", "service": "pinquark-wms", "version": "1.0.0"}


@app.get("/readiness", tags=["health"])
async def readiness() -> dict[str, str]:
    return {"status": "ready", "service": "pinquark-wms", "version": "1.0.0"}


# --- Helpers ---

class CredentialsBody(BaseModel):
    credentials: WmsCredentials


def _make_creds_body(model_class):
    """Create a request body model that includes credentials + a payload field."""
    pass


def _error(detail: str, status_code: int = 502) -> HTTPException:
    return HTTPException(status_code=status_code, detail=detail)


async def _forward_get(creds: WmsCredentials, path_label: str, client_method):
    try:
        data, status = await client_method(creds)
        if status >= 400:
            raise _error(f"{path_label} returned HTTP {status}: {data}", status)
        return data
    except httpx.HTTPError as exc:
        raise _error(f"{path_label} request failed: {exc}")


async def _forward_post(creds: WmsCredentials, body: Any, path_label: str, client_method):
    try:
        data, status = await client_method(creds, body)
        if status >= 400:
            raise _error(f"{path_label} returned HTTP {status}: {data}", status)
        return data
    except httpx.HTTPError as exc:
        raise _error(f"{path_label} request failed: {exc}")


def _write_result_to_response(result: WriteResult, path_label: str) -> dict[str, Any]:
    if not result.accepted:
        raise _error(f"{path_label} returned HTTP {result.http_status}: {result.api_response}", result.http_status)

    response: dict[str, Any] = {
        "accepted": True,
        "api_response": result.api_response,
    }

    if result.timed_out:
        response["feedback"] = {"status": "timeout", "message": "No feedback received within polling window"}
    elif result.confirmed is not None:
        response["feedback"] = {
            "status": "confirmed" if result.feedback_success else "failed",
            "id": result.feedback_id,
            "success": result.feedback_success,
            "errors": result.feedback_errors,
            "messages": result.feedback_messages,
        }
        if not result.feedback_success:
            response["feedback"]["message"] = "WMS reported processing failure"
    return response


async def _forward_write(
    creds: WmsCredentials,
    body: Any,
    entity: str,
    action: str,
    path: str,
    path_label: str,
):
    try:
        result = await wms_client.write_with_feedback(creds, entity, action, path, body)
        return _write_result_to_response(result, path_label)
    except httpx.HTTPError as exc:
        raise _error(f"{path_label} request failed: {exc}")


# =========================================================================
# AUTH
# =========================================================================

class LoginRequest(BaseModel):
    credentials: WmsCredentials


@app.post("/auth/sign-in", tags=["auth"])
async def login(req: LoginRequest) -> dict:
    try:
        token = await wms_client._login(req.credentials)
        return {"status": "authenticated", "accessToken": token}
    except Exception as exc:
        raise _error(f"Login failed: {exc}", 401)


# =========================================================================
# ARTICLES
# =========================================================================

@app.post("/articles/get", tags=["articles"])
async def get_articles(req: CredentialsBody) -> Any:
    return await _forward_get(req.credentials, "GET /articles", wms_client.get_articles)


@app.post("/articles/get-delete-commands", tags=["articles"])
async def get_articles_delete_commands(req: CredentialsBody) -> Any:
    return await _forward_get(
        req.credentials, "GET /articles/delete-commands",
        wms_client.get_articles_delete_commands,
    )


class CreateArticleRequest(BaseModel):
    credentials: WmsCredentials
    article: Article


@app.post("/articles/create", tags=["articles"])
async def create_article(req: CreateArticleRequest) -> Any:
    return await _forward_write(
        req.credentials, req.article.model_dump(exclude_none=True),
        entity="ARTICLE", action="SAVE", path="/articles",
        path_label="POST /articles",
    )


class CreateArticlesRequest(BaseModel):
    credentials: WmsCredentials
    articles: list[Article]


@app.post("/articles/create-list", tags=["articles"])
async def create_articles(req: CreateArticlesRequest) -> Any:
    return await _forward_write(
        req.credentials,
        [a.model_dump(exclude_none=True) for a in req.articles],
        entity="ARTICLE", action="SAVE", path="/articles/list",
        path_label="POST /articles/list",
    )


class DeleteArticleRequest(BaseModel):
    credentials: WmsCredentials
    command: DeleteCommand


@app.post("/articles/delete", tags=["articles"])
async def delete_article(req: DeleteArticleRequest) -> Any:
    return await _forward_write(
        req.credentials, req.command.model_dump(exclude_none=True),
        entity="ARTICLE", action="DELETE", path="/articles/delete-commands",
        path_label="POST /articles/delete-commands",
    )


class DeleteArticlesRequest(BaseModel):
    credentials: WmsCredentials
    commands: list[DeleteCommand]


@app.post("/articles/delete-list", tags=["articles"])
async def delete_articles(req: DeleteArticlesRequest) -> Any:
    return await _forward_write(
        req.credentials,
        [c.model_dump(exclude_none=True) for c in req.commands],
        entity="ARTICLE", action="DELETE", path="/articles/delete-commands/list",
        path_label="POST /articles/delete-commands/list",
    )


# =========================================================================
# ARTICLE BATCHES
# =========================================================================

@app.post("/article-batches/get", tags=["article-batches"])
async def get_batches(req: CredentialsBody) -> Any:
    return await _forward_get(req.credentials, "GET /article-batches", wms_client.get_batches)


class CreateBatchRequest(BaseModel):
    credentials: WmsCredentials
    batch: ArticleBatch


@app.post("/article-batches/create", tags=["article-batches"])
async def create_batch(req: CreateBatchRequest) -> Any:
    return await _forward_write(
        req.credentials, req.batch.model_dump(exclude_none=True),
        entity="ARTICLE_BATCH", action="SAVE", path="/article-batches",
        path_label="POST /article-batches",
    )


class CreateBatchesRequest(BaseModel):
    credentials: WmsCredentials
    batches: list[ArticleBatch]


@app.post("/article-batches/create-list", tags=["article-batches"])
async def create_batches(req: CreateBatchesRequest) -> Any:
    return await _forward_write(
        req.credentials,
        [b.model_dump(exclude_none=True) for b in req.batches],
        entity="ARTICLE_BATCH", action="SAVE", path="/article-batches/list",
        path_label="POST /article-batches/list",
    )


# =========================================================================
# DOCUMENTS
# =========================================================================

@app.post("/documents/get", tags=["documents"])
async def get_documents(req: CredentialsBody) -> Any:
    return await _forward_get(req.credentials, "GET /documents", wms_client.get_documents)


@app.post("/documents/get-delete-commands", tags=["documents"])
async def get_documents_delete_commands(req: CredentialsBody) -> Any:
    return await _forward_get(
        req.credentials, "GET /documents/delete-commands",
        wms_client.get_documents_delete_commands,
    )


class CreateDocumentRequest(BaseModel):
    credentials: WmsCredentials
    document: Document


@app.post("/documents/create", tags=["documents"])
async def create_document(req: CreateDocumentRequest) -> Any:
    return await _forward_write(
        req.credentials, req.document.model_dump(exclude_none=True),
        entity="DOCUMENT", action="SAVE", path="/documents",
        path_label="POST /documents",
    )


class CreateDocumentsRequest(BaseModel):
    credentials: WmsCredentials
    wrapper: DocumentWrapper


@app.post("/documents/create-list", tags=["documents"])
async def create_documents(req: CreateDocumentsRequest) -> Any:
    return await _forward_write(
        req.credentials, req.wrapper.model_dump(exclude_none=True),
        entity="DOCUMENT", action="SAVE", path="/documents/wrappers",
        path_label="POST /documents/wrappers",
    )


class DeleteDocumentRequest(BaseModel):
    credentials: WmsCredentials
    command: DeleteCommand


@app.post("/documents/delete", tags=["documents"])
async def delete_document(req: DeleteDocumentRequest) -> Any:
    return await _forward_write(
        req.credentials, req.command.model_dump(exclude_none=True),
        entity="DOCUMENT", action="DELETE", path="/documents/delete-commands",
        path_label="POST /documents/delete-commands",
    )


class DeleteDocumentsRequest(BaseModel):
    credentials: WmsCredentials
    commands: list[DeleteCommand]


@app.post("/documents/delete-list", tags=["documents"])
async def delete_documents(req: DeleteDocumentsRequest) -> Any:
    return await _forward_write(
        req.credentials,
        [c.model_dump(exclude_none=True) for c in req.commands],
        entity="DOCUMENT", action="DELETE", path="/documents/delete-commands/list",
        path_label="POST /documents/delete-commands/list",
    )


# =========================================================================
# POSITIONS
# =========================================================================

@app.post("/positions/get", tags=["positions"])
async def get_positions(req: CredentialsBody) -> Any:
    return await _forward_get(req.credentials, "GET /positions", wms_client.get_positions)


@app.post("/positions/get-delete-commands", tags=["positions"])
async def get_positions_delete_commands(req: CredentialsBody) -> Any:
    return await _forward_get(
        req.credentials, "GET /positions/delete-commands",
        wms_client.get_positions_delete_commands,
    )


class CreatePositionRequest(BaseModel):
    credentials: WmsCredentials
    position: PositionWrapper


@app.post("/positions/create", tags=["positions"])
async def create_position(req: CreatePositionRequest) -> Any:
    return await _forward_write(
        req.credentials, req.position.model_dump(exclude_none=True),
        entity="POSITION", action="SAVE", path="/positions",
        path_label="POST /positions",
    )


class CreatePositionsRequest(BaseModel):
    credentials: WmsCredentials
    positions: list[PositionWrapper]


@app.post("/positions/create-list", tags=["positions"])
async def create_positions(req: CreatePositionsRequest) -> Any:
    return await _forward_write(
        req.credentials,
        [p.model_dump(exclude_none=True) for p in req.positions],
        entity="POSITION", action="SAVE", path="/positions/list",
        path_label="POST /positions/list",
    )


class DeletePositionRequest(BaseModel):
    credentials: WmsCredentials
    command: PositionDeleteCommand


@app.post("/positions/delete", tags=["positions"])
async def delete_position(req: DeletePositionRequest) -> Any:
    return await _forward_write(
        req.credentials, req.command.model_dump(exclude_none=True),
        entity="POSITION", action="DELETE", path="/positions/delete-commands",
        path_label="POST /positions/delete-commands",
    )


class DeletePositionsRequest(BaseModel):
    credentials: WmsCredentials
    commands: list[PositionDeleteCommand]


@app.post("/positions/delete-list", tags=["positions"])
async def delete_positions(req: DeletePositionsRequest) -> Any:
    return await _forward_write(
        req.credentials,
        [c.model_dump(exclude_none=True) for c in req.commands],
        entity="POSITION", action="DELETE", path="/positions/delete-commands/list",
        path_label="POST /positions/delete-commands/list",
    )


# =========================================================================
# CONTRACTORS
# =========================================================================

@app.post("/contractors/get", tags=["contractors"])
async def get_contractors(req: CredentialsBody) -> Any:
    return await _forward_get(req.credentials, "GET /contractors", wms_client.get_contractors)


@app.post("/contractors/get-delete-commands", tags=["contractors"])
async def get_contractors_delete_commands(req: CredentialsBody) -> Any:
    return await _forward_get(
        req.credentials, "GET /contractors/delete-commands",
        wms_client.get_contractors_delete_commands,
    )


class CreateContractorRequest(BaseModel):
    credentials: WmsCredentials
    contractor: Contractor


@app.post("/contractors/create", tags=["contractors"])
async def create_contractor(req: CreateContractorRequest) -> Any:
    return await _forward_write(
        req.credentials, req.contractor.model_dump(exclude_none=True),
        entity="CONTRACTOR", action="SAVE", path="/contractors",
        path_label="POST /contractors",
    )


class CreateContractorsRequest(BaseModel):
    credentials: WmsCredentials
    contractors: list[Contractor]


@app.post("/contractors/create-list", tags=["contractors"])
async def create_contractors(req: CreateContractorsRequest) -> Any:
    return await _forward_write(
        req.credentials,
        [c.model_dump(exclude_none=True) for c in req.contractors],
        entity="CONTRACTOR", action="SAVE", path="/contractors/list",
        path_label="POST /contractors/list",
    )


class DeleteContractorRequest(BaseModel):
    credentials: WmsCredentials
    command: DeleteCommand


@app.post("/contractors/delete", tags=["contractors"])
async def delete_contractor(req: DeleteContractorRequest) -> Any:
    return await _forward_write(
        req.credentials, req.command.model_dump(exclude_none=True),
        entity="CONTRACTOR", action="DELETE", path="/contractors/delete-commands",
        path_label="POST /contractors/delete-commands",
    )


class DeleteContractorsRequest(BaseModel):
    credentials: WmsCredentials
    commands: list[DeleteCommand]


@app.post("/contractors/delete-list", tags=["contractors"])
async def delete_contractors(req: DeleteContractorsRequest) -> Any:
    return await _forward_write(
        req.credentials,
        [c.model_dump(exclude_none=True) for c in req.commands],
        entity="CONTRACTOR", action="DELETE", path="/contractors/delete-commands/list",
        path_label="POST /contractors/delete-commands/list",
    )


# =========================================================================
# FEEDBACK & ERRORS
# =========================================================================

@app.post("/feedbacks/get", tags=["feedback"])
async def get_feedbacks(req: CredentialsBody) -> Any:
    return await _forward_get(req.credentials, "GET /feedbacks", wms_client.get_feedbacks)


@app.post("/errors/get", tags=["errors"])
async def get_errors(req: CredentialsBody) -> Any:
    return await _forward_get(req.credentials, "GET /errors", wms_client.get_errors)


# =========================================================================
# EVENT POLLER MANAGEMENT
# =========================================================================

class RegisterPollingRequest(BaseModel):
    account_name: str = "default"
    credentials: WmsCredentials


@app.post("/poller/register", tags=["poller"])
async def register_polling_account(req: RegisterPollingRequest) -> dict[str, Any]:
    """Register WMS credentials for event polling."""
    event_poller.register_credentials(req.account_name, req.credentials)
    return {
        "status": "registered",
        "account_name": req.account_name,
        "polling_interval": settings.event_polling_interval_seconds,
        "polling_enabled": settings.event_polling_enabled,
    }


@app.get("/poller/status", tags=["poller"])
async def poller_status() -> dict[str, Any]:
    """Get current event poller status."""
    return {
        "running": event_poller._running,
        "enabled": settings.event_polling_enabled,
        "interval_seconds": settings.event_polling_interval_seconds,
        "registered_accounts": list(event_poller._credential_store.keys()),
        "tracked_entities": {
            k: len(v) for k, v in event_poller._state.items()
        },
        "initialized_entities": list(event_poller._initialized),
        "platform_url": settings.platform_api_url,
    }


@app.post("/poller/reset", tags=["poller"])
async def poller_reset() -> dict[str, str]:
    """Reset poller state so the next cycle treats all entities as new."""
    event_poller.reset_state()
    return {"status": "reset", "message": "Next poll cycle will emit events for all entities"}


@app.post("/poller/poll-now", tags=["poller"])
async def poller_poll_now() -> dict[str, str]:
    """Trigger an immediate poll cycle (does not wait for result)."""
    if not event_poller._running:
        raise HTTPException(status_code=400, detail="Poller is not running")
    asyncio.create_task(event_poller._poll_cycle())
    return {"status": "triggered", "message": "Poll cycle started"}


@app.get("/poller/diagnose", tags=["poller"])
async def poller_diagnose() -> dict[str, Any]:
    """Test WMS API connectivity for all registered accounts and return raw responses."""
    results: dict[str, Any] = {}
    for account_name, creds in event_poller._credential_store.items():
        acct_result: dict[str, Any] = {"base_url": wms_client._base_url(creds)}
        for entity, fetch_fn in [
            ("documents", wms_client.get_documents),
            ("articles", wms_client.get_articles),
            ("contractors", wms_client.get_contractors),
        ]:
            try:
                data, status = await fetch_fn(creds)
                acct_result[entity] = {
                    "http_status": status,
                    "type": type(data).__name__,
                    "count": len(data) if isinstance(data, list) else None,
                    "sample": data[:2] if isinstance(data, list) and data else data,
                }
            except Exception as exc:
                acct_result[entity] = {"error": str(exc)}
        results[account_name] = acct_result
    return results
