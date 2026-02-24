"""Connector discovery — finds all connectors to verify using manifests + DB."""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.db import ConnectorInstance, Credential

logger = logging.getLogger(__name__)

_CONNECTOR_SERVICE_NAMES: dict[str, str] = {
    "email-client": "connector-email-client",
    "inpost": "connector-inpost",
    "dhl": "connector-dhl",
    "dhl-express": "connector-dhl-express",
    "dpd": "connector-dpd",
    "fedex": "connector-fedex",
    "fedexpl": "connector-fedexpl",
    "geis": "connector-geis",
    "gls": "connector-gls",
    "orlenpaczka": "connector-orlenpaczka",
    "packeta": "connector-packeta",
    "paxy": "connector-paxy",
    "pocztapolska": "connector-pocztapolska",
    "schenker": "connector-schenker",
    "sellasist": "connector-sellasist",
    "suus": "connector-suus",
    "ups": "connector-ups",
    "allegro": "connector-allegro",
    "amazon": "connector-amazon",
    "shoper": "connector-shoper",
    "idosell": "connector-idosell",
    "baselinker": "connector-baselinker",
    "woocommerce": "connector-woocommerce",
    "shopify": "connector-shopify",
    "pinquark-wms": "connector-pinquark-wms",
    "ai-agent": "connector-ai-agent",
    "ftp-sftp": "connector-ftp-sftp",
    "skanuj-fakture": "connector-skanuj-fakture",
    "raben": "connector-raben",
    "fxcouriers": "connector-fxcouriers",
    "slack": "connector-slack",
    "bulkgate": "connector-bulkgate",
    "apilo": "connector-apilo",
}


@dataclass
class ConnectorManifest:
    name: str
    category: str
    version: str
    display_name: str
    description: str
    interface: str
    capabilities: list[str] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)
    events: list[str] = field(default_factory=list)
    health_endpoint: str = "/health"
    docs_url: str = "/docs"
    config_schema: dict = field(default_factory=dict)


@dataclass
class VerificationTarget:
    """A connector to verify — combines manifest + DB instance + resolved URL."""
    manifest: ConnectorManifest
    base_url: str
    tenant_id: str | None = None
    credentials: dict[str, str] | None = None
    is_deployed: bool = True


def resolve_service_url(connector_name: str) -> str:
    service = _CONNECTOR_SERVICE_NAMES.get(connector_name, f"connector-{connector_name}")
    return f"http://{service}:{settings.default_connector_port}"


def discover_manifests() -> list[ConnectorManifest]:
    """Scan integrators directory for connector.yaml manifests."""
    discovery_path = Path(settings.connector_discovery_path)
    manifests: list[ConnectorManifest] = []

    if not discovery_path.exists():
        logger.warning("Discovery path %s does not exist", discovery_path)
        return manifests

    for manifest_path in discovery_path.rglob("connector.yaml"):
        try:
            with open(manifest_path) as f:
                data = yaml.safe_load(f)
            manifests.append(ConnectorManifest(
                name=data["name"],
                category=data["category"],
                version=str(data["version"]),
                display_name=data.get("display_name", data["name"]),
                description=data.get("description", ""),
                interface=data.get("interface", "generic"),
                capabilities=data.get("capabilities", []),
                actions=data.get("actions", []),
                events=data.get("events", []),
                health_endpoint=data.get("health_endpoint", "/health"),
                docs_url=data.get("docs_url", "/docs"),
                config_schema=data.get("config_schema", {}),
            ))
        except Exception as exc:
            logger.warning("Failed to load manifest %s: %s", manifest_path, exc)

    return manifests


async def discover_targets(db: AsyncSession) -> list[VerificationTarget]:
    """Build list of verification targets from manifests + DB instances."""
    manifests = discover_manifests()
    seen_connectors: set[str] = set()
    targets: list[VerificationTarget] = []

    result = await db.execute(
        select(ConnectorInstance).where(ConnectorInstance.is_enabled.is_(True))
    )
    instances = {row.connector_name: row for row in result.scalars().all()}

    latest_manifests: dict[str, ConnectorManifest] = {}
    for m in manifests:
        key = m.name
        if key not in latest_manifests or m.version > latest_manifests[key].version:
            latest_manifests[key] = m

    for name, manifest in latest_manifests.items():
        base_url = resolve_service_url(name)
        instance = instances.get(name)
        tenant_id = str(instance.tenant_id) if instance else None

        targets.append(VerificationTarget(
            manifest=manifest,
            base_url=base_url,
            tenant_id=tenant_id,
        ))
        seen_connectors.add(name)

    return targets
