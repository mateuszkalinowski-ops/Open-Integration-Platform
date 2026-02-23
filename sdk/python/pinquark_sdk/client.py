"""Pinquark SDK -- Python client for the Integration Platform API."""

from __future__ import annotations

from typing import Any

import httpx

from pinquark_sdk.models import (
    Connector,
    ConnectorInstance,
    EventResult,
    Flow,
    FlowExecution,
)


class _BaseAPI:
    def __init__(self, client: httpx.AsyncClient, api_key: str) -> None:
        self._client = client
        self._headers = {"X-API-Key": api_key}

    async def _request(
        self,
        method: str,
        path: str,
        json: dict | None = None,
        params: dict | None = None,
    ) -> Any:
        response = await self._client.request(
            method, path, json=json, params=params, headers=self._headers
        )
        if response.status_code >= 400:
            error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {"detail": response.text}
            raise PinquarkAPIError(response.status_code, error_data)
        if response.status_code == 204:
            return None
        return response.json()


class PinquarkAPIError(Exception):
    def __init__(self, status_code: int, detail: Any) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"API error {status_code}: {detail}")


class ConnectorAPI(_BaseAPI):
    """Browse and manage connectors."""

    async def list(
        self,
        category: str | None = None,
        interface: str | None = None,
        capability: str | None = None,
    ) -> list[Connector]:
        params = {}
        if category:
            params["category"] = category
        if interface:
            params["interface"] = interface
        if capability:
            params["capability"] = capability
        data = await self._request("GET", "/api/v1/connectors", params=params)
        return [Connector(**c) for c in data]

    async def get(self, category: str, name: str) -> Connector:
        data = await self._request("GET", f"/api/v1/connectors/{category}/{name}")
        return Connector(**data)

    async def activate(
        self,
        connector_name: str,
        connector_version: str,
        connector_category: str,
        display_name: str = "",
        config: dict | None = None,
    ) -> ConnectorInstance:
        data = await self._request("POST", "/api/v1/connector-instances", json={
            "connector_name": connector_name,
            "connector_version": connector_version,
            "connector_category": connector_category,
            "display_name": display_name,
            "config": config or {},
        })
        return ConnectorInstance(**data)

    async def list_instances(self) -> list[ConnectorInstance]:
        data = await self._request("GET", "/api/v1/connector-instances")
        return [ConnectorInstance(**i) for i in data]


class FlowAPI(_BaseAPI):
    """Create and manage integration flows."""

    async def create(
        self,
        name: str,
        source_connector: str,
        source_event: str,
        destination_connector: str,
        destination_action: str,
        field_mapping: list[dict] | None = None,
        source_filter: dict | None = None,
        on_error: str = "retry",
        max_retries: int = 3,
    ) -> Flow:
        data = await self._request("POST", "/api/v1/flows", json={
            "name": name,
            "source_connector": source_connector,
            "source_event": source_event,
            "destination_connector": destination_connector,
            "destination_action": destination_action,
            "field_mapping": field_mapping or [],
            "source_filter": source_filter,
            "on_error": on_error,
            "max_retries": max_retries,
        })
        return Flow(**data)

    async def list(self) -> list[Flow]:
        data = await self._request("GET", "/api/v1/flows")
        return [Flow(**f) for f in data]

    async def delete(self, flow_id: str) -> None:
        await self._request("DELETE", f"/api/v1/flows/{flow_id}")

    async def trigger_event(
        self,
        connector_name: str,
        event: str,
        data: dict,
    ) -> EventResult:
        result = await self._request("POST", "/api/v1/events", json={
            "connector_name": connector_name,
            "event": event,
            "data": data,
        })
        return EventResult(**result)

    async def list_executions(
        self,
        flow_id: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[FlowExecution]:
        params: dict[str, Any] = {"limit": limit}
        if flow_id:
            params["flow_id"] = flow_id
        if status:
            params["status"] = status
        data = await self._request("GET", "/api/v1/flow-executions", params=params)
        return [FlowExecution(**e) for e in data]


class CredentialAPI(_BaseAPI):
    """Manage encrypted credentials for connectors."""

    async def store(self, connector_name: str, credentials: dict[str, str]) -> dict:
        return await self._request("POST", "/api/v1/credentials", json={
            "connector_name": connector_name,
            "credentials": credentials,
        })


class PinquarkClient:
    """Main client for the Open Integration Platform by Pinquark.com.

    Usage:
        client = PinquarkClient(api_key="pk_live_xxx")

        # Browse connectors
        couriers = await client.connectors.list(category="courier")

        # Create a flow
        flow = await client.flows.create(
            name="Allegro -> InPost",
            source_connector="allegro",
            source_event="order.created",
            destination_connector="inpost",
            destination_action="shipment.create",
            field_mapping=[
                {"from": "order.buyer.name", "to": "receiver.first_name"},
            ],
        )

        # Trigger an event
        result = await client.flows.trigger_event(
            connector_name="allegro",
            event="order.created",
            data={"order": {"id": "123", "buyer": {"name": "Jan"}}},
        )
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.pinquark.com",
        timeout: float = 30.0,
    ) -> None:
        self._client = httpx.AsyncClient(base_url=base_url, timeout=timeout)
        self._api_key = api_key

        self.connectors = ConnectorAPI(self._client, api_key)
        self.flows = FlowAPI(self._client, api_key)
        self.credentials = CredentialAPI(self._client, api_key)

    async def health(self) -> dict:
        response = await self._client.get("/health")
        return response.json()

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> PinquarkClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
