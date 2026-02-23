"""Registry for managing client-specific mapping profiles.

Profiles can be loaded from YAML/JSON files at startup or registered
programmatically. The registry resolves the correct profile for a
given (client_id, system, category, entity, direction) combination,
falling back to a default profile if no client-specific one exists.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from pinquark_common.mapping.base import BaseMapper
from pinquark_common.mapping.config import MappingDirection, MappingProfile

logger = logging.getLogger(__name__)

_DEFAULT_CLIENT = "__default__"


class MappingRegistry:
    """Central store for mapping profiles.

    Resolution order:
    1. Exact match: (client_id, system, category, entity, direction)
    2. Default: ("__default__", system, category, entity, direction)
    3. None -> MappingError
    """

    def __init__(self) -> None:
        self._profiles: dict[str, MappingProfile] = {}

    @staticmethod
    def _make_key(
        client_id: str,
        system: str,
        category: str,
        entity: str,
        direction: MappingDirection,
    ) -> str:
        return f"{client_id}::{system}::{category}::{entity}::{direction.value}"

    def register(self, profile: MappingProfile) -> None:
        key = self._make_key(
            profile.client_id,
            profile.system,
            profile.category,
            profile.entity,
            profile.direction,
        )
        self._profiles[key] = profile
        logger.info("Registered mapping profile: %s", key)

    def get_profile(
        self,
        client_id: str,
        system: str,
        category: str,
        entity: str,
        direction: MappingDirection = MappingDirection.INBOUND,
    ) -> MappingProfile | None:
        key = self._make_key(client_id, system, category, entity, direction)
        profile = self._profiles.get(key)
        if profile:
            return profile

        default_key = self._make_key(
            _DEFAULT_CLIENT, system, category, entity, direction
        )
        return self._profiles.get(default_key)

    def get_mapper(
        self,
        client_id: str,
        system: str,
        category: str,
        entity: str,
        direction: MappingDirection = MappingDirection.INBOUND,
    ) -> BaseMapper | None:
        profile = self.get_profile(
            client_id, system, category, entity, direction
        )
        if profile is None:
            return None
        return BaseMapper(profile)

    def load_from_file(self, path: str | Path) -> MappingProfile:
        """Load a single profile from a YAML or JSON file."""
        filepath = Path(path)
        raw = filepath.read_text(encoding="utf-8")

        if filepath.suffix in (".yaml", ".yml"):
            data = _parse_yaml(raw)
        else:
            data = json.loads(raw)

        profile = MappingProfile.model_validate(data)
        self.register(profile)
        return profile

    def load_from_directory(self, directory: str | Path) -> list[MappingProfile]:
        """Load all profile files (*.yaml, *.yml, *.json) from a directory."""
        dir_path = Path(directory)
        loaded: list[MappingProfile] = []

        if not dir_path.is_dir():
            logger.warning("Mapping profiles directory not found: %s", dir_path)
            return loaded

        for filepath in sorted(dir_path.rglob("*")):
            if filepath.suffix in (".yaml", ".yml", ".json") and filepath.is_file():
                try:
                    profile = self.load_from_file(filepath)
                    loaded.append(profile)
                except Exception:
                    logger.exception("Failed to load mapping profile: %s", filepath)

        logger.info("Loaded %d mapping profiles from %s", len(loaded), dir_path)
        return loaded

    def list_profiles(self) -> list[MappingProfile]:
        return list(self._profiles.values())

    def list_for_client(self, client_id: str) -> list[MappingProfile]:
        return [
            p for p in self._profiles.values() if p.client_id == client_id
        ]


def _parse_yaml(raw: str) -> dict[str, Any]:
    """Parse YAML with lazy import to avoid hard dependency."""
    try:
        import yaml  # noqa: PLC0415
    except ImportError as exc:
        raise ImportError(
            "PyYAML is required to load YAML mapping profiles. "
            "Install it with: pip install pyyaml"
        ) from exc
    return yaml.safe_load(raw)
