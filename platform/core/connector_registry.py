"""Connector Registry -- discovers and manages available connectors.

Scans the integrators directory for connector.yaml manifests and provides
a registry of available connectors with their capabilities.

Each connector is fully self-described by its connector.yaml — the platform
requires zero per-connector code.  Adding a new connector means creating its
folder with a connector.yaml; no platform files need to change.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

DEFAULT_CONNECTOR_PORT = 8000


def _parse_semver(version: str) -> tuple[int, ...]:
    """Parse a semver string into a tuple of ints for proper comparison."""
    parts: list[int] = []
    for segment in version.split("."):
        digits = ""
        for ch in segment:
            if ch.isdigit():
                digits += ch
            else:
                break
        parts.append(int(digits) if digits else 0)
    return tuple(parts)


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
    action_metadata: dict[str, dict] = field(default_factory=dict)
    config_schema: dict = field(default_factory=dict)
    api_endpoints: list[dict] = field(default_factory=list)
    event_fields: dict[str, list[dict]] = field(default_factory=dict)
    action_fields: dict[str, list[dict]] = field(default_factory=dict)
    output_fields: dict[str, list[dict]] = field(default_factory=dict)
    action_routes: dict[str, dict] = field(default_factory=dict)
    service_name: str = ""
    credential_provisioning: dict = field(default_factory=dict)
    credential_validation: dict = field(default_factory=dict)
    payload_hints: dict = field(default_factory=dict)
    rate_limits: dict = field(default_factory=dict)
    oauth2: dict = field(default_factory=dict)
    webhooks: dict = field(default_factory=dict)
    deployment: str = "cloud"
    requires_onpremise_agent: bool = False
    onpremise_agent: dict = field(default_factory=dict)
    health_endpoint: str = "/health"
    docs_url: str = "/docs"
    status: str = "stable"
    path: str = ""

    @property
    def connector_id(self) -> str:
        return f"{self.category}/{self.name}/{self.version}"

    @property
    def resolved_service_name(self) -> str:
        return self.service_name or f"connector-{self.name}"

    @property
    def base_url(self) -> str:
        return f"http://{self.resolved_service_name}:{DEFAULT_CONNECTOR_PORT}"

    @property
    def auth_type(self) -> str:
        """Best-effort auth classification for catalog filtering."""
        if self.oauth2 or (self.credential_validation or {}).get("oauth2"):
            return "oauth2"

        validation = self.credential_validation or {}
        required_fields = set(validation.get("required_fields", []))
        config_fields = set((self.config_schema or {}).get("required", [])) | set(
            (self.config_schema or {}).get("optional", [])
        )
        fields = {str(field).lower() for field in required_fields | config_fields}

        if validation.get("validate_mode") == "email_imap_smtp":
            return "email"
        if validation.get("auth") == "basic" or {"username", "password"} <= fields or {"login", "password"} <= fields:
            return "basic"
        if {"client_id", "client_secret"} <= fields:
            return "client_credentials"
        if {"username", "password"} & fields and "access_token" in fields:
            return "hybrid"
        if {"token", "api_key", "api_token", "access_token", "bot_token"} & fields:
            return "token"
        if {"consumer_key", "consumer_secret"} <= fields:
            return "api_key"
        if {"sql_server", "sql_database"} <= fields:
            return "onpremise"
        return "custom"

    @property
    def supports_oauth2(self) -> bool:
        return bool(self.oauth2 or (self.credential_validation or {}).get("oauth2"))

    @property
    def sandbox_available(self) -> bool:
        validation = self.credential_validation or {}
        config = self.config_schema or {}
        fields = set(config.get("required", [])) | set(config.get("optional", []))
        return bool(
            "sandbox" in validation
            or validation.get("defaults", {}).get("sandbox")
            or self.oauth2.get("sandbox")
            or "sandbox_mode" in fields
        )

    @property
    def has_webhooks(self) -> bool:
        return bool(self.webhooks)


class ConnectorRegistry:
    def __init__(self, discovery_path: str = "../integrators") -> None:
        self._discovery_path = Path(discovery_path).resolve()
        self._connectors: dict[str, ConnectorManifest] = {}

    def discover(self) -> int:
        self._connectors.clear()
        count = 0

        if not self._discovery_path.exists():
            logger.warning("Discovery path %s does not exist", self._discovery_path)
            return 0

        for manifest_path in self._discovery_path.rglob("connector.yaml"):
            try:
                manifest = self._load_manifest(manifest_path)
                self._connectors[manifest.connector_id] = manifest
                count += 1
            except Exception:
                logger.warning("Failed to load connector manifest %s", manifest_path, exc_info=True)
                continue

        return count

    def _load_manifest(self, path: Path) -> ConnectorManifest:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data or not isinstance(data, dict):
            raise ValueError(f"Empty or invalid manifest: {path}")

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
            action_metadata=data.get("action_metadata", {}),
            config_schema=data.get("config_schema", {}),
            api_endpoints=data.get("api_endpoints", []),
            event_fields=data.get("event_fields", {}),
            action_fields=data.get("action_fields", {}),
            output_fields=data.get("output_fields", {}),
            action_routes=data.get("action_routes", {}),
            service_name=data.get("service_name", ""),
            credential_provisioning=data.get("credential_provisioning", {}),
            credential_validation=data.get("credential_validation", {}),
            payload_hints=data.get("payload_hints", {}),
            rate_limits=data.get("rate_limits", {}),
            oauth2=data.get("oauth2", {}),
            webhooks=data.get("webhooks", {}),
            deployment=data.get("deployment", "cloud"),
            requires_onpremise_agent=data.get("requires_onpremise_agent", False),
            onpremise_agent=data.get("onpremise_agent", {}),
            health_endpoint=data.get("health_endpoint", "/health"),
            docs_url=data.get("docs_url", "/docs"),
            status=str(data.get("status", "stable")),
            path=str(path.parent),
        )

    def get_all(self) -> list[ConnectorManifest]:
        return list(self._connectors.values())

    def get_by_category(self, category: str) -> list[ConnectorManifest]:
        return [c for c in self._connectors.values() if c.category == category]

    def get_by_name(self, name: str) -> list[ConnectorManifest]:
        return [c for c in self._connectors.values() if c.name == name]

    def get_by_name_version(self, name: str, version: str | None = None) -> ConnectorManifest | None:
        """Return a specific version manifest, or the latest if *version* is ``None``."""
        candidates = self.get_by_name(name)
        if not candidates:
            return None
        if version:
            for c in candidates:
                if c.version == version:
                    return c
        return max(candidates, key=lambda c: _parse_semver(c.version))

    def get(self, connector_id: str) -> ConnectorManifest | None:
        return self._connectors.get(connector_id)

    def get_latest(self, category: str, name: str) -> ConnectorManifest | None:
        versions = [c for c in self._connectors.values() if c.category == category and c.name == name]
        if not versions:
            return None
        return max(versions, key=lambda c: _parse_semver(c.version))

    def search(
        self,
        category: str | None = None,
        interface: str | None = None,
        capability: str | None = None,
        event: str | None = None,
        action: str | None = None,
        country: str | None = None,
        q: str | None = None,
        auth_type: str | None = None,
        status: str | None = None,
        supports_oauth2: bool | None = None,
        has_webhooks: bool | None = None,
        sandbox_available: bool | None = None,
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
        if country:
            results = [c for c in results if c.country == country]
        if auth_type:
            results = [c for c in results if c.auth_type == auth_type]
        if status:
            results = [c for c in results if c.status == status]
        if supports_oauth2 is not None:
            results = [c for c in results if c.supports_oauth2 is supports_oauth2]
        if has_webhooks is not None:
            results = [c for c in results if c.has_webhooks is has_webhooks]
        if sandbox_available is not None:
            results = [c for c in results if c.sandbox_available is sandbox_available]
        if q:
            needle = q.strip().lower()
            if needle:
                results = [
                    c
                    for c in results
                    if needle in c.name.lower()
                    or needle in c.display_name.lower()
                    or needle in c.description.lower()
                    or needle in c.category.lower()
                    or needle in c.interface.lower()
                    or needle in c.country.lower()
                    or any(needle in item.lower() for item in c.capabilities)
                    or any(needle in item.lower() for item in c.events)
                    or any(needle in item.lower() for item in c.actions)
                ]

        return results
