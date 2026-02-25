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
class ApiVersionCheck:
    """Describes how to check the external API for newer versions."""
    current_api_version: str
    check_url: str
    check_type: str = "openapi"  # openapi | json | html
    version_field: str = "info.version"
    docs_url: str = ""


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
    api_version_check: ApiVersionCheck | None = None


@dataclass
class VerificationTarget:
    """A connector to verify — combines manifest + DB instance + resolved URL."""
    manifest: ConnectorManifest
    base_url: str
    tenant_id: str | None = None
    credentials: dict[str, str] | None = None
    is_deployed: bool = True


def resolve_service_url(connector_name: str, version: str | None = None, version_count: int = 1) -> str:
    """Resolve Docker service URL for a connector.

    When multiple versions of the same connector exist, the service name
    includes the major version suffix: ``connector-inpost-v3``.
    Single-version connectors keep the plain name for backward compat.
    """
    base = _CONNECTOR_SERVICE_NAMES.get(connector_name, f"connector-{connector_name}")
    if version_count > 1 and version:
        major = version.split(".")[0]
        service = f"{base}-v{major}"
    else:
        service = base
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
            avc_data = data.get("api_version_check")
            avc = None
            if avc_data and isinstance(avc_data, dict):
                avc = ApiVersionCheck(
                    current_api_version=str(avc_data.get("current_api_version", "")),
                    check_url=avc_data.get("check_url", ""),
                    check_type=avc_data.get("check_type", "openapi"),
                    version_field=avc_data.get("version_field", "info.version"),
                    docs_url=avc_data.get("docs_url", ""),
                )

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
                api_version_check=avc,
            ))
        except Exception as exc:
            logger.warning("Failed to load manifest %s: %s", manifest_path, exc)

    return manifests


async def discover_targets(db: AsyncSession) -> list[VerificationTarget]:
    """Build list of verification targets from manifests + DB instances.

    All discovered versions of a connector are included so that each
    deployed version is verified independently.
    """
    manifests = discover_manifests()
    targets: list[VerificationTarget] = []

    result = await db.execute(
        select(ConnectorInstance).where(ConnectorInstance.is_enabled.is_(True))
    )
    instances = {row.connector_name: row for row in result.scalars().all()}

    versions_per_connector: dict[str, list[ConnectorManifest]] = {}
    for m in manifests:
        versions_per_connector.setdefault(m.name, []).append(m)

    for name, versions in versions_per_connector.items():
        versions.sort(key=lambda m: m.version)
        instance = instances.get(name)
        tenant_id = str(instance.tenant_id) if instance else None

        for manifest in versions:
            base_url = resolve_service_url(
                name, version=manifest.version, version_count=len(versions),
            )
            targets.append(VerificationTarget(
                manifest=manifest,
                base_url=base_url,
                tenant_id=tenant_id,
            ))

    return targets
