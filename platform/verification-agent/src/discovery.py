"""Connector discovery — finds all connectors to verify using manifests + DB.

Service names and URLs are resolved from each connector's ``connector.yaml``
(the ``service_name`` field), eliminating the need for a hardcoded registry.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.db import ConnectorInstance

logger = logging.getLogger(__name__)


@dataclass
class ApiVersionCheck:
    """Describes how to check the external API for newer versions."""

    current_api_version: str
    check_url: str
    check_type: str = "openapi"
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
    service_name: str = ""
    credential_provisioning: dict = field(default_factory=dict)
    api_version_check: ApiVersionCheck | None = None

    @property
    def resolved_service_name(self) -> str:
        return self.service_name or f"connector-{self.name}"


@dataclass
class VerificationTarget:
    """A connector to verify — combines manifest + DB instance + resolved URL."""

    manifest: ConnectorManifest
    base_url: str
    tenant_id: str | None = None
    credentials: dict[str, str] | None = None
    is_deployed: bool = True


def resolve_service_url(
    manifest: ConnectorManifest,
    version_count: int = 1,
) -> str:
    """Resolve Docker service URL for a connector using its manifest.

    When multiple versions of the same connector exist, the service name
    includes the major version suffix: ``connector-inpost-v3``.
    Single-version connectors keep the plain name for backward compat.

    Skips the suffix when the service_name already contains a version
    indicator (e.g. ``connector-inpost-v1``) to avoid double-appending.
    """
    base = manifest.resolved_service_name
    if version_count > 1 and manifest.version:
        major = manifest.version.split(".")[0]
        suffix = f"-v{major}"
        service = f"{base}{suffix}" if not base.endswith(suffix) else base
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

            manifests.append(
                ConnectorManifest(
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
                    service_name=data.get("service_name", ""),
                    credential_provisioning=data.get("credential_provisioning", {}),
                    api_version_check=avc,
                )
            )
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

    result = await db.execute(select(ConnectorInstance).where(ConnectorInstance.is_enabled.is_(True)))
    all_instances = list(result.scalars().all())

    instance_index: dict[tuple[str, str], list[Any]] = {}
    instances_by_name: dict[str, list[Any]] = {}
    for row in all_instances:
        instance_index.setdefault((row.connector_name, row.connector_version), []).append(row)
        instances_by_name.setdefault(row.connector_name, []).append(row)

    versions_per_connector: dict[str, list[ConnectorManifest]] = {}
    for m in manifests:
        versions_per_connector.setdefault(m.name, []).append(m)

    for name, versions in versions_per_connector.items():
        versions.sort(key=lambda m: m.version)
        any_matched = False

        for manifest in versions:
            base_url = resolve_service_url(
                manifest,
                version_count=len(versions),
            )
            matched_instances = instance_index.get((name, manifest.version), [])
            if matched_instances:
                any_matched = True
                for inst in matched_instances:
                    targets.append(
                        VerificationTarget(
                            manifest=manifest,
                            base_url=base_url,
                            tenant_id=str(inst.tenant_id),
                        )
                    )

        if not any_matched:
            name_instances = instances_by_name.get(name, [])
            if name_instances:
                version_map = {m.version: m for m in versions}
                for inst in name_instances:
                    matched_manifest = version_map.get(inst.connector_version)
                    if matched_manifest:
                        base_url = resolve_service_url(matched_manifest, version_count=len(versions))
                        targets.append(
                            VerificationTarget(
                                manifest=matched_manifest,
                                base_url=base_url,
                                tenant_id=str(inst.tenant_id),
                            )
                        )
                    else:
                        logger.warning(
                            "Skipping %s instance (tenant=%s): instance version %s not found in available manifests %s",
                            name,
                            inst.tenant_id,
                            inst.connector_version,
                            [m.version for m in versions],
                        )
            else:
                for manifest in versions:
                    base_url = resolve_service_url(
                        manifest,
                        version_count=len(versions),
                    )
                    targets.append(
                        VerificationTarget(
                            manifest=manifest,
                            base_url=base_url,
                            tenant_id=None,
                        )
                    )
                    logger.info(
                        "Including %s v%s for Tier 1 checks (no DB instances)",
                        name,
                        manifest.version,
                    )

    return targets
