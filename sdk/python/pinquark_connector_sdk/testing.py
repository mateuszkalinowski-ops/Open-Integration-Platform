"""Test utilities for connector development."""

from __future__ import annotations

import re
from typing import Any

import httpx


def make_test_account(
    name: str = "test-account",
    credentials: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "name": name,
        "credentials": credentials or {"api_key": "test-key-12345", "sandbox_mode": True},
    }


class ConnectorTestClient:
    """Wraps httpx.AsyncClient for testing connector FastAPI apps.

    Usage::

        from pinquark_connector_sdk.testing import ConnectorTestClient
        from my_connector import MyConnector

        async def test_health():
            app = MyConnector()
            async with ConnectorTestClient(app) as client:
                resp = await client.get("/health")
                assert resp.status_code == 200
    """

    def __init__(self, connector_app: Any) -> None:
        from pinquark_connector_sdk.app import ConnectorApp

        if isinstance(connector_app, ConnectorApp):
            fastapi_app = connector_app._fastapi
        else:
            fastapi_app = connector_app

        self._transport = httpx.ASGITransport(app=fastapi_app)
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> ConnectorTestClient:
        self._client = httpx.AsyncClient(
            transport=self._transport,
            base_url="http://testserver",
        )
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self._client:
            await self._client.aclose()

    async def get(self, url: str, **kwargs: Any) -> httpx.Response:
        assert self._client is not None
        return await self._client.get(url, **kwargs)

    async def post(self, url: str, **kwargs: Any) -> httpx.Response:
        assert self._client is not None
        return await self._client.post(url, **kwargs)

    async def put(self, url: str, **kwargs: Any) -> httpx.Response:
        assert self._client is not None
        return await self._client.put(url, **kwargs)

    async def delete(self, url: str, **kwargs: Any) -> httpx.Response:
        assert self._client is not None
        return await self._client.delete(url, **kwargs)

    async def setup_account(
        self,
        name: str = "test-account",
        credentials: dict[str, Any] | None = None,
    ) -> httpx.Response:
        """Create a test account via the accounts API."""
        return await self.post("/accounts", json=make_test_account(name, credentials))


class _MockRoute:
    """A single mocked route definition."""

    def __init__(self, method: str, url_pattern: str, response_status: int, response_json: Any) -> None:
        self.method = method.upper()
        self.url_pattern = re.compile(url_pattern)
        self.response_status = response_status
        self.response_json = response_json
        self.calls: list[httpx.Request] = []

    def matches(self, request: httpx.Request) -> bool:
        return (
            request.method == self.method
            and self.url_pattern.search(str(request.url)) is not None
        )

    @property
    def call_count(self) -> int:
        return len(self.calls)


class MockExternalAPI:
    """Context manager that intercepts httpx requests for testing.

    Usage::

        async with MockExternalAPI() as mock:
            mock.get(r"https://api\\.example\\.com/items", json={"items": []})
            mock.post(r"https://api\\.example\\.com/items", json={"id": 1}, status=201)

            client = ConnectorHttpClient()
            resp = await client.get("https://api.example.com/items")
            assert resp.status_code == 200
    """

    def __init__(self) -> None:
        self._routes: list[_MockRoute] = []
        self._original_send: Any = None

    def get(self, url_pattern: str, *, json: Any = None, status: int = 200) -> _MockRoute:
        return self._add_route("GET", url_pattern, status, json)

    def post(self, url_pattern: str, *, json: Any = None, status: int = 200) -> _MockRoute:
        return self._add_route("POST", url_pattern, status, json)

    def put(self, url_pattern: str, *, json: Any = None, status: int = 200) -> _MockRoute:
        return self._add_route("PUT", url_pattern, status, json)

    def delete(self, url_pattern: str, *, json: Any = None, status: int = 200) -> _MockRoute:
        return self._add_route("DELETE", url_pattern, status, json)

    def _add_route(self, method: str, url_pattern: str, status: int, json_data: Any) -> _MockRoute:
        route = _MockRoute(method, url_pattern, status, json_data)
        self._routes.append(route)
        return route

    async def _mock_send(self, request: httpx.Request, **kwargs: Any) -> httpx.Response:
        for route in self._routes:
            if route.matches(request):
                route.calls.append(request)
                import json as json_mod
                body = json_mod.dumps(route.response_json).encode() if route.response_json is not None else b""
                return httpx.Response(
                    status_code=route.response_status,
                    headers={"content-type": "application/json"},
                    content=body,
                    request=request,
                )
        raise httpx.ConnectError(f"No mock route matched: {request.method} {request.url}")

    async def __aenter__(self) -> MockExternalAPI:
        self._original_send = httpx.AsyncClient.send
        httpx.AsyncClient.send = self._mock_send  # type: ignore[assignment]
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self._original_send is not None:
            httpx.AsyncClient.send = self._original_send  # type: ignore[assignment]
