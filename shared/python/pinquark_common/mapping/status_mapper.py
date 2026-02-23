import json
import logging
import pathlib
from enum import Enum

logger = logging.getLogger(__name__)

_DEFAULT_TRANSLATION_ENTITY: dict[str, object] = {"translation": "", "activated": False}

_MAPPING_FILE = pathlib.Path(__file__).parent / "status_mapping.json"


class STATUS(str, Enum):
    """Package statuses in WMS system."""

    CREATED = "CREATED"
    PAID = "PAID"
    DISPATCHED = "DISPATCHED"
    PROCESSING = "PROCESSING"
    MISSING = "MISSING"
    IN_DELIVERY = "IN_DELIVERY"
    AWAITING_PICKUP = "AWAITING_PICKUP"
    PICKUP_EXPIRED = "PICKUP_EXPIRED"
    REJECTED = "REJECTED"
    DELIVERED = "DELIVERED"
    RETURNED = "RETURNED"
    UNKNOWN = "UNKNOWN"


class StatusMapper:
    """Maps statuses between external systems and internal WMS statuses.

    Uses a JSON mapping file structured as:
        mappings -> sources[] -> targets[] -> entities[] -> map{}

    Each map entry contains a translation string and an activated flag.
    When activated is False the original status is returned unchanged.
    """

    def __init__(
        self,
        target: str = "WMS",
        entity: str = "courier_status",
        mapping_path: pathlib.Path | None = None,
    ) -> None:
        self.target = target
        self.entity = entity
        path = mapping_path or _MAPPING_FILE
        self._mappings: dict = json.loads(path.read_text(encoding="utf-8"))

    def map_status(self, source: str, status: str) -> str:
        """Translate *status* from *source* system using the loaded mapping.

        Returns the translated value when the mapping entry exists and is
        activated; otherwise returns the original *status* unchanged.
        """
        source_mappings = self._extract_source_mapping(source)
        entry = source_mappings.get(status, _DEFAULT_TRANSLATION_ENTITY)
        if entry.get("activated", False):
            return entry.get("translation", status)  # type: ignore[return-value]
        return status

    def _extract_source_mapping(self, source: str) -> dict[str, dict]:
        """Return the ``map`` dict for *source* → *self.target* → *self.entity*."""
        try:
            sources = self._mappings.get("mappings", {}).get("sources", [])
            source_entry = self._find_by_name(sources, source)
            targets = source_entry.get("targets", [])
            target_entry = self._find_by_name(targets, self.target)
            entities = target_entry.get("entities", [])
            entity_entry = self._find_by_name(entities, self.entity)
            return entity_entry.get("map", {})
        except KeyError:
            logger.warning("No status mapping found for source=%s target=%s entity=%s", source, self.target, self.entity)
            return {}

    @staticmethod
    def _find_by_name(items: list[dict], name: str) -> dict:
        """Find the first item whose ``name`` key equals *name*.

        Raises KeyError when no match is found.
        """
        for item in items:
            if item.get("name") == name:
                return item
        raise KeyError(f"Mapping does not contain entity: {name}")
