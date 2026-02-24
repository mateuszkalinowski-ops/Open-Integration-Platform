"""Connector Registry -- discovers and manages available connectors.

Scans the integrators directory for connector.yaml manifests and provides
a registry of available connectors with their capabilities.
"""

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class ConnectorManifest:
    name: str
    category: str
    version: str
    display_name: str
    description: str
    interface: str
    country: str = ""
    logo_url: str = ""
    website_url: str = ""
    capabilities: list[str] = field(default_factory=list)
    events: list[str] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)
    config_schema: dict = field(default_factory=dict)
    api_endpoints: list[dict] = field(default_factory=list)
    event_fields: dict[str, list[dict]] = field(default_factory=dict)
    action_fields: dict[str, list[dict]] = field(default_factory=dict)
    output_fields: dict[str, list[dict]] = field(default_factory=dict)
    health_endpoint: str = "/health"
    docs_url: str = "/docs"
    path: str = ""

    @property
    def connector_id(self) -> str:
        return f"{self.category}/{self.name}/{self.version}"


class ConnectorRegistry:
    def __init__(self, discovery_path: str = "../integrators") -> None:
        self._discovery_path = Path(discovery_path)
        self._connectors: dict[str, ConnectorManifest] = {}

    def discover(self) -> int:
        self._connectors.clear()
        count = 0

        if not self._discovery_path.exists():
            return 0

        for manifest_path in self._discovery_path.rglob("connector.yaml"):
            try:
                manifest = self._load_manifest(manifest_path)
                self._connectors[manifest.connector_id] = manifest
                count += 1
            except Exception:
                continue

        return count

    def _load_manifest(self, path: Path) -> ConnectorManifest:
        with open(path) as f:
            data = yaml.safe_load(f)

        return ConnectorManifest(
            name=data["name"],
            category=data["category"],
            version=str(data["version"]),
            display_name=data.get("display_name", data["name"]),
            description=data.get("description", ""),
            interface=data.get("interface", "generic"),
            country=data.get("country", ""),
            logo_url=data.get("logo_url", ""),
            website_url=data.get("website_url", ""),
            capabilities=data.get("capabilities", []),
            events=data.get("events", []),
            actions=data.get("actions", []),
            config_schema=data.get("config_schema", {}),
            api_endpoints=data.get("api_endpoints", []),
            event_fields=data.get("event_fields", {}),
            action_fields=data.get("action_fields", {}),
            output_fields=data.get("output_fields", {}),
            health_endpoint=data.get("health_endpoint", "/health"),
            docs_url=data.get("docs_url", "/docs"),
            path=str(path.parent),
        )

    def get_all(self) -> list[ConnectorManifest]:
        return list(self._connectors.values())

    def get_by_category(self, category: str) -> list[ConnectorManifest]:
        return [c for c in self._connectors.values() if c.category == category]

    def get_by_name(self, name: str) -> list[ConnectorManifest]:
        return [c for c in self._connectors.values() if c.name == name]

    def get(self, connector_id: str) -> ConnectorManifest | None:
        return self._connectors.get(connector_id)

    def get_latest(self, category: str, name: str) -> ConnectorManifest | None:
        versions = [
            c for c in self._connectors.values() if c.category == category and c.name == name
        ]
        if not versions:
            return None
        return max(versions, key=lambda c: c.version)

    def search(
        self,
        category: str | None = None,
        interface: str | None = None,
        capability: str | None = None,
        event: str | None = None,
        action: str | None = None,
    ) -> list[ConnectorManifest]:
        results = list(self._connectors.values())

        if category:
            results = [c for c in results if c.category == category]
        if interface:
            results = [c for c in results if c.interface == interface]
        if capability:
            results = [c for c in results if capability in c.capabilities]
        if event:
            results = [c for c in results if event in c.events]
        if action:
            results = [c for c in results if action in c.actions]

        return results
