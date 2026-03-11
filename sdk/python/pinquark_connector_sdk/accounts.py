"""Auto-generated account management routes for connector FastAPI apps."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from pinquark_connector_sdk.app import ConnectorApp

logger = structlog.get_logger(__name__)


class AccountCreate(BaseModel):
    """Accepts both SDK format {name, credentials} and platform flat format {name, key1, key2, ...}."""

    model_config = {"extra": "allow"}
    name: str
    credentials: dict[str, Any] = Field(default_factory=dict)

    def resolved_credentials(self) -> dict[str, Any]:
        """Return credentials, falling back to extra fields for platform flat payloads."""
        if self.credentials:
            return self.credentials
        extra = (self.__pydantic_extra__ or {}).copy()
        return extra


class AccountUpdate(BaseModel):
    """Accepts both SDK format {credentials} and platform flat format {key1, key2, ...}."""

    model_config = {"extra": "allow"}
    credentials: dict[str, Any] = Field(default_factory=dict)

    def resolved_credentials(self) -> dict[str, Any]:
        if self.credentials:
            return self.credentials
        extra = (self.__pydantic_extra__ or {}).copy()
        return extra


class AccountResponse(BaseModel):
    name: str
    credential_keys: list[str] = Field(default_factory=list)


class AuthStatusResponse(BaseModel):
    account: str
    authenticated: bool
    message: str = ""


class ConnectionStatusResponse(BaseModel):
    account: str
    connected: bool
    message: str = ""


class AccountStore:
    """In-memory account storage. Replace with persistent storage for production."""

    def __init__(self) -> None:
        self._accounts: dict[str, dict[str, Any]] = {}

    def list_accounts(self) -> list[str]:
        return list(self._accounts.keys())

    def get(self, name: str) -> dict[str, Any] | None:
        return self._accounts.get(name)

    def create(self, name: str, credentials: dict[str, Any]) -> None:
        self._accounts[name] = credentials

    def update(self, name: str, credentials: dict[str, Any]) -> None:
        if name not in self._accounts:
            raise KeyError(name)
        self._accounts[name] = credentials

    def delete(self, name: str) -> None:
        self._accounts.pop(name, None)

    def get_credentials(self, name: str) -> dict[str, Any]:
        if name not in self._accounts:
            raise KeyError(name)
        return self._accounts[name]


def register_account_routes(app: FastAPI, connector_app: ConnectorApp) -> AccountStore:
    """Add account CRUD + auth/connection status endpoints to the FastAPI app."""
    store = AccountStore()

    @app.get("/accounts", response_model=list[AccountResponse], tags=["accounts"])
    async def list_accounts() -> list[AccountResponse]:
        return [
            AccountResponse(
                name=name,
                credential_keys=list((store.get(name) or {}).keys()),
            )
            for name in store.list_accounts()
        ]

    @app.post("/accounts", response_model=AccountResponse, status_code=201, tags=["accounts"])
    async def create_account(body: AccountCreate) -> AccountResponse:
        if store.get(body.name) is not None:
            raise HTTPException(status_code=409, detail=f"Account '{body.name}' already exists")

        creds = body.resolved_credentials()
        store.create(body.name, creds)
        logger.info("account_created", account=body.name)
        return AccountResponse(name=body.name, credential_keys=list(creds.keys()))

    @app.get("/accounts/{name}", response_model=AccountResponse, tags=["accounts"])
    async def get_account(name: str) -> AccountResponse:
        creds = store.get(name)
        if creds is None:
            raise HTTPException(status_code=404, detail=f"Account '{name}' not found")
        return AccountResponse(name=name, credential_keys=list(creds.keys()))

    @app.put("/accounts/{name}", response_model=AccountResponse, tags=["accounts"])
    async def update_account(name: str, body: AccountUpdate) -> AccountResponse:
        creds = body.resolved_credentials()
        try:
            store.update(name, creds)
        except KeyError:
            raise HTTPException(status_code=404, detail=f"Account '{name}' not found")
        logger.info("account_updated", account=name)
        return AccountResponse(name=name, credential_keys=list(creds.keys()))

    @app.delete(
        "/accounts/{name}",
        status_code=204,
        response_model=None,
        response_class=Response,
        tags=["accounts"],
    )
    async def delete_account(name: str) -> Response:
        store.delete(name)
        logger.info("account_deleted", account=name)
        return Response(status_code=204)

    @app.get("/auth/{account}/status", response_model=AuthStatusResponse, tags=["accounts"])
    async def auth_status(account: str) -> AuthStatusResponse:
        creds = store.get(account)
        if creds is None:
            return AuthStatusResponse(account=account, authenticated=False, message="Account not found")
        return AuthStatusResponse(account=account, authenticated=True, message="Credentials stored")

    @app.get("/connection/{account}/status", response_model=ConnectionStatusResponse, tags=["accounts"])
    async def connection_status(account: str) -> ConnectionStatusResponse:
        creds = store.get(account)
        if creds is None:
            return ConnectionStatusResponse(account=account, connected=False, message="Account not found")

        try:
            connected = await connector_app.test_connection()
            return ConnectionStatusResponse(
                account=account,
                connected=connected,
                message="Connection OK" if connected else "Connection failed",
            )
        except NotImplementedError:
            return ConnectionStatusResponse(
                account=account,
                connected=True,
                message="test_connection not implemented, assuming connected",
            )
        except Exception as exc:
            return ConnectionStatusResponse(
                account=account,
                connected=False,
                message=f"Connection check failed: {exc}",
            )

    return store
