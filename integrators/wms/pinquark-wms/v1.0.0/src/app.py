"""Pinquark WMS Integration REST API connector.

Proxies requests to the Pinquark WMS integration-rest application.
Endpoints mirror the official Pinquark Integration REST API documentation.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.client import PinquarkWmsClient, WriteResult
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

logger = logging.getLogger("pinquark-wms")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

wms_client = PinquarkWmsClient()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
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
