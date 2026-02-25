"""Sales document (DokumentySprzedazy) operations via InsERT Nexo SDK."""

import logging
from typing import Any

from src.bridge.nexo_connection import NexoConnection
from src.bridge.nexo_types import nexo_sales_document_to_model, _iterate_net_collection
from src.models.document import DocumentCreate, DocumentResponse, DocumentType

logger = logging.getLogger(__name__)


class SalesDocumentService:
    def __init__(self, connection: NexoConnection):
        self._conn = connection

    def _get_dokumenty_sprzedazy(self) -> Any:
        from InsERT.Moria.ModelDanych import IDokumentySprzedazy  # type: ignore[import-not-found]
        return self._conn.get_typed_object(IDokumentySprzedazy)

    def list_documents(
        self,
        page: int = 1,
        page_size: int = 50,
        document_type: DocumentType | None = None,
    ) -> dict[str, Any]:
        dokumenty = self._get_dokumenty_sprzedazy()
        all_items = _iterate_net_collection(dokumenty.Dane.Wszystkie())

        total = len(all_items)
        start = (page - 1) * page_size
        end = start + page_size
        page_items = all_items[start:end]

        results = [nexo_sales_document_to_model(d) for d in page_items]

        return {
            "items": [r.model_dump() for r in results],
            "page": page,
            "page_size": page_size,
            "total": total,
            "has_next": end < total,
        }

    def get_document(self, doc_id: int) -> DocumentResponse | None:
        dokumenty = self._get_dokumenty_sprzedazy()
        for d in _iterate_net_collection(dokumenty.Dane.Wszystkie()):
            if getattr(d, "Id", None) == doc_id:
                return nexo_sales_document_to_model(d)
        return None

    def get_document_by_number(self, number: str) -> DocumentResponse | None:
        dokumenty = self._get_dokumenty_sprzedazy()
        for d in _iterate_net_collection(dokumenty.Dane.Wszystkie()):
            num_obj = getattr(d, "NumerWewnetrzny", None)
            full_num = str(getattr(num_obj, "PelnaSygnatura", "")) if num_obj else ""
            if full_num == number:
                return nexo_sales_document_to_model(d)
        return None

    def create_invoice(self, data: DocumentCreate) -> DocumentResponse:
        dokumenty = self._get_dokumenty_sprzedazy()

        create_methods = {
            DocumentType.SALES_INVOICE: dokumenty.UtworzFaktureSprzedazy,
            DocumentType.SALES_RECEIPT: dokumenty.UtworzParagon,
            DocumentType.PROFORMA: dokumenty.UtworzFaktureProforma,
        }
        create_fn = create_methods.get(data.document_type, dokumenty.UtworzFaktureSprzedazy)
        faktura = create_fn()

        with self._conn.entity_scope(faktura):
            faktura.PodmiotyDokumentu.UstawZamawiajacegoWedlugSymbolu(data.buyer_symbol)

            if data.receiver_symbol:
                try:
                    faktura.PodmiotyDokumentu.UstawOdbiorceWedlugSymbolu(data.receiver_symbol)
                except Exception:
                    pass

            for pos in data.positions:
                try:
                    faktura.Pozycje.Dodaj(pos.product_symbol)
                except Exception:
                    logger.warning("Failed to add position: %s", pos.product_symbol)

            faktura.Przelicz()

            if data.payments:
                for pay in data.payments:
                    try:
                        if pay.payment_form.lower() in ("gotówka", "gotowka", "cash"):
                            faktura.Platnosci.DodajDomyslnaPlatnoscNatychmiastowaNaKwoteDokumentu()
                        # Deferred payment is added by default based on contractor settings
                    except Exception:
                        logger.warning("Failed to add payment")
            else:
                try:
                    faktura.Platnosci.DodajDomyslnaPlatnoscNatychmiastowaNaKwoteDokumentu()
                except Exception:
                    pass

            if not faktura.Zapisz():
                errors = self._extract_errors(faktura)
                raise ValueError(f"Failed to create sales document: {errors}")

            return nexo_sales_document_to_model(faktura.Dane)

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
