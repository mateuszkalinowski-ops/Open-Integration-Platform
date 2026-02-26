"""Warehouse document (WZ/PZ) operations via InsERT Nexo SDK."""

import logging
from typing import Any

from src.bridge.nexo_connection import NexoConnection
from src.bridge.nexo_types import nexo_warehouse_document_to_model, _iterate_net_collection
from src.models.document import DocumentCreate, DocumentResponse, DocumentType

logger = logging.getLogger(__name__)


class WarehouseDocumentService:
    def __init__(self, connection: NexoConnection):
        self._conn = connection

    def _get_wydania(self) -> Any:
        from InsERT.Moria.ModelDanych import IWydaniaZewnetrzne  # type: ignore[import-not-found]
        return self._conn.get_typed_object(IWydaniaZewnetrzne)

    def _get_przyjecia(self) -> Any:
        from InsERT.Moria.ModelDanych import IPrzyjeciaZewnetrzne  # type: ignore[import-not-found]
        return self._conn.get_typed_object(IPrzyjeciaZewnetrzne)

    def list_issues(self, page: int = 1, page_size: int = 50) -> dict[str, Any]:
        wydania = self._get_wydania()
        all_items = _iterate_net_collection(wydania.Dane.Wszystkie())

        total = len(all_items)
        start = (page - 1) * page_size
        end = start + page_size
        page_items = all_items[start:end]

        results = []
        for d in page_items:
            doc = nexo_warehouse_document_to_model(d)
            doc.document_type = DocumentType.WAREHOUSE_ISSUE
            results.append(doc)

        return {
            "items": [r.model_dump() for r in results],
            "page": page,
            "page_size": page_size,
            "total": total,
            "has_next": end < total,
        }

    def list_receipts(self, page: int = 1, page_size: int = 50) -> dict[str, Any]:
        przyjecia = self._get_przyjecia()
        all_items = _iterate_net_collection(przyjecia.Dane.Wszystkie())

        total = len(all_items)
        start = (page - 1) * page_size
        end = start + page_size
        page_items = all_items[start:end]

        results = []
        for d in page_items:
            doc = nexo_warehouse_document_to_model(d)
            doc.document_type = DocumentType.WAREHOUSE_RECEIPT
            results.append(doc)

        return {
            "items": [r.model_dump() for r in results],
            "page": page,
            "page_size": page_size,
            "total": total,
            "has_next": end < total,
        }

    def create_issue(self, data: DocumentCreate) -> DocumentResponse:
        """Create a WZ (warehouse issue / external release)."""
        wydania = self._get_wydania()
        wydanie = wydania.UtworzWydanieZewnetrzne()

        with self._conn.entity_scope(wydanie):
            wydanie.PodmiotyDokumentu.UstawOdbiorceWedlugSymbolu(data.buyer_symbol)

            for pos in data.positions:
                try:
                    wydanie.Pozycje.Dodaj(pos.product_symbol)
                except Exception:
                    logger.warning("Failed to add WZ position: %s", pos.product_symbol)

            wydanie.Przelicz()

            if not wydanie.Zapisz():
                errors = self._extract_errors(wydanie)
                raise ValueError(f"Failed to create warehouse issue: {errors}")

            doc = nexo_warehouse_document_to_model(wydanie.Dane)
            doc.document_type = DocumentType.WAREHOUSE_ISSUE
            return doc

    def create_receipt(self, data: DocumentCreate) -> DocumentResponse:
        """Create a PZ (warehouse receipt / external acceptance)."""
        przyjecia = self._get_przyjecia()
        przyjecie = przyjecia.UtworzPrzyjecieZewnetrzne()

        with self._conn.entity_scope(przyjecie):
            przyjecie.PodmiotyDokumentu.UstawDostawceWedlugSymbolu(data.buyer_symbol)

            for pos in data.positions:
                try:
                    przyjecie.Pozycje.Dodaj(pos.product_symbol)
                except Exception:
                    logger.warning("Failed to add PZ position: %s", pos.product_symbol)

            przyjecie.Przelicz()

            if not przyjecie.Zapisz():
                errors = self._extract_errors(przyjecie)
                raise ValueError(f"Failed to create warehouse receipt: {errors}")

            doc = nexo_warehouse_document_to_model(przyjecie.Dane)
            doc.document_type = DocumentType.WAREHOUSE_RECEIPT
            return doc

    @staticmethod
    def _extract_errors(entity: Any) -> str:
        try:
            errors = []
            if hasattr(entity, "Bledy"):
                for err in _iterate_net_collection(entity.Bledy):
                    errors.append(str(err))
            return "; ".join(errors) if errors else "Unknown error"
        except Exception:
            return "Could not extract error details"
