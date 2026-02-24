"""HTTP client for SkanujFakture REST API."""

import base64
import logging
from typing import Any

import httpx

from src.config import SkanujFaktureAccountConfig, settings

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = httpx.Timeout(settings.api_timeout, connect=30.0)


def _safe_json(response: httpx.Response) -> dict[str, Any]:
    """Parse JSON from response, returning a status dict when body is empty."""
    if not response.content:
        return {"status": "ok", "http_status": response.status_code}
    return response.json()


class SkanujFaktureClient:
    """Async HTTP client wrapping the SkanujFakture REST API.

    All endpoints require Basic Authentication.
    Base URL: {api_url}/ (default: https://skanujfakture.pl:8443/SFApi)
    """

    def __init__(self, account: SkanujFaktureAccountConfig) -> None:
        self._account = account
        self._base_url = account.api_url.rstrip("/")
        credentials = base64.b64encode(f"{account.login}:{account.password}".encode()).decode()
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers={
                "Authorization": f"Basic {credentials}",
            },
            timeout=DEFAULT_TIMEOUT,
            verify=True,
        )

    async def close(self) -> None:
        await self._client.aclose()

    # -- Companies ---------------------------------------------------------------

    async def get_companies(self) -> list[dict[str, Any]]:
        """GET /users/currentUser/companies — list companies accessible by user."""
        response = await self._client.get("/users/currentUser/companies")
        response.raise_for_status()
        return response.json()

    # -- Company Entities --------------------------------------------------------

    async def get_company_entities(self, company_id: int) -> list[dict[str, Any]]:
        """GET /companies/{companyId}/companyEntities — list entities (subjects)."""
        response = await self._client.get(f"/companies/{company_id}/companyEntities")
        response.raise_for_status()
        return response.json()

    # -- Documents ---------------------------------------------------------------

    async def upload_document(
        self,
        company_id: int,
        file_content: bytes,
        filename: str,
        single_document: bool = True,
        sale: bool = False,
    ) -> dict[str, Any]:
        """POST /companies/{companyId}/documents — upload invoice file for OCR."""
        response = await self._client.post(
            f"/companies/{company_id}/documents",
            params={
                "singleDocument": str(single_document).lower(),
                "sale": str(sale).lower(),
            },
            files={"file": (filename, file_content)},
        )
        response.raise_for_status()
        return response.json()

    async def upload_document_v2(
        self,
        company_id: int,
        file_content: bytes,
        filename: str,
        single_document: bool = True,
        invoice_type: str = "PURCHASE",
        company_entity_id: int | None = None,
    ) -> dict[str, Any]:
        """POST /companies/{companyId}/documents/v2 — upload with document type."""
        params: dict[str, str] = {
            "singleDocument": str(single_document).lower(),
            "invoice": invoice_type,
        }
        if company_entity_id is not None:
            params["companyEntityId"] = str(company_entity_id)
        response = await self._client.post(
            f"/companies/{company_id}/documents/v2",
            params=params,
            files={"file": (filename, file_content)},
        )
        response.raise_for_status()
        return response.json()

    async def upload_document_v3(
        self,
        company_id: int,
        file_content: bytes,
        filename: str,
        single_document: bool = True,
        company_entity_id: int = 0,
    ) -> dict[str, Any]:
        """POST /companies/{companyId}/documents/v3 — upload as OTHER type."""
        response = await self._client.post(
            f"/companies/{company_id}/documents/v3",
            params={
                "singleDocument": str(single_document).lower(),
                "companyEntityId": str(company_entity_id),
            },
            files={"file": (filename, file_content)},
        )
        response.raise_for_status()
        return response.json()

    async def get_documents(
        self,
        company_id: int,
        document_statuses: list[str] | None = None,
        company_entity_id: int | None = None,
        is_sale: bool | None = None,
        contractor: list[str] | None = None,
        number: list[str] | None = None,
        check_document_ids: list[int] | None = None,
        exception_check_document_ids: list[int] | None = None,
    ) -> list[dict[str, Any]]:
        """GET /companies/{companyId}/documents — list documents with filters."""
        params: dict[str, Any] = {}
        if document_statuses:
            params["documentStatuses"] = document_statuses
        if company_entity_id is not None:
            params["companyEntityId"] = company_entity_id
        if is_sale is not None:
            params["isSale"] = is_sale
        if contractor:
            params["contractor"] = contractor
        if number:
            params["number"] = number
        if check_document_ids:
            params["checkDocumentIds"] = check_document_ids
        if exception_check_document_ids:
            params["exceptionCheckDocumentIds"] = exception_check_document_ids
        response = await self._client.get(f"/companies/{company_id}/documents", params=params)
        response.raise_for_status()
        return response.json()

    async def get_documents_simple(
        self,
        company_id: int,
        document_statuses: list[str] | None = None,
        check_document_ids: list[int] | None = None,
    ) -> list[dict[str, Any]]:
        """GET /companies/{companyId}/documents/simple — simplified document list."""
        params: dict[str, Any] = {}
        if document_statuses:
            params["documentStatuses"] = document_statuses
        if check_document_ids:
            params["checkDocumentIds"] = check_document_ids
        response = await self._client.get(f"/companies/{company_id}/documents/simple", params=params)
        response.raise_for_status()
        return response.json()

    async def update_document(
        self,
        company_id: int,
        document_id: int,
        document_data: dict[str, Any],
    ) -> dict[str, Any]:
        """PUT /companies/{companyId}/documents/{documentId} — update a document."""
        response = await self._client.put(
            f"/companies/{company_id}/documents/{document_id}",
            json=document_data,
        )
        response.raise_for_status()
        return response.json()

    async def bulk_edit_documents(
        self,
        company_id: int,
        criteria: dict[str, Any],
        description: str | None = None,
        attribute: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """PUT /companies/{companyId}/documents — bulk-edit documents."""
        body: dict[str, Any] = {"criteria": criteria}
        if description is not None:
            body["description"] = description
        if attribute is not None:
            body["attribute"] = attribute
        response = await self._client.put(f"/companies/{company_id}/documents", json=body)
        response.raise_for_status()
        return response.json()

    async def delete_documents(
        self,
        company_id: int,
        check_document_ids: list[int] | None = None,
        document_statuses: list[str] | None = None,
    ) -> dict[str, Any]:
        """DELETE /companies/{companyId}/documents — delete documents."""
        params: dict[str, Any] = {}
        if check_document_ids:
            params["checkDocumentIds"] = check_document_ids
        if document_statuses:
            params["documentStatuses"] = document_statuses
        response = await self._client.delete(f"/companies/{company_id}/documents", params=params)
        response.raise_for_status()
        return _safe_json(response)

    async def get_document_file(self, company_id: int, document_id: int) -> bytes:
        """GET /companies/{companyId}/documents/{documentId}/file — original file bytes."""
        response = await self._client.get(f"/companies/{company_id}/documents/{document_id}/file")
        response.raise_for_status()
        return response.content

    async def get_document_image(self, company_id: int, document_id: int) -> bytes:
        """GET /companies/{companyId}/documents/{documentId}/image — image blob."""
        response = await self._client.get(f"/companies/{company_id}/documents/{document_id}/image")
        response.raise_for_status()
        return response.content

    # -- Attributes --------------------------------------------------------------

    async def edit_attributes(
        self,
        company_id: int,
        document_id: int,
        attributes: list[dict[str, Any]],
        status_id: int | None = None,
    ) -> dict[str, Any]:
        """PUT /companies/{companyId}/documents/{documentId}/attributes."""
        body: dict[str, Any] = {"attributes": attributes}
        if status_id is not None:
            body["statusId"] = status_id
        response = await self._client.put(
            f"/companies/{company_id}/documents/{document_id}/attributes",
            json=body,
        )
        response.raise_for_status()
        return _safe_json(response)

    async def delete_attributes(self, company_id: int, document_id: int) -> dict[str, Any]:
        """DELETE /companies/{companyId}/documents/{documentId}/attributes."""
        response = await self._client.delete(
            f"/companies/{company_id}/documents/{document_id}/attributes",
        )
        response.raise_for_status()
        return _safe_json(response)

    # -- Dictionaries (dekretacja) -----------------------------------------------

    async def get_dictionaries(self, company_id: int, dict_type: str) -> list[dict[str, Any]]:
        """GET /companies/{companyId}/decrets?type={type}."""
        response = await self._client.get(
            f"/companies/{company_id}/decrets",
            params={"type": dict_type},
        )
        response.raise_for_status()
        return response.json()

    async def add_dictionary_items(
        self,
        company_id: int,
        dict_type: str,
        items: list[dict[str, str]],
    ) -> dict[str, Any]:
        """POST /companies/{companyId}/decrets?type={type}."""
        response = await self._client.post(
            f"/companies/{company_id}/decrets",
            params={"type": dict_type},
            json=items,
        )
        response.raise_for_status()
        return _safe_json(response)

    async def update_dictionary_items(
        self,
        company_id: int,
        dict_type: str,
        items: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """PUT /companies/{companyId}/decrets?type={type}."""
        response = await self._client.put(
            f"/companies/{company_id}/decrets",
            params={"type": dict_type},
            json=items,
        )
        response.raise_for_status()
        return _safe_json(response)

    async def delete_dictionary_items(
        self,
        company_id: int,
        item_ids: list[int],
    ) -> dict[str, Any]:
        """DELETE /companies/{companyId}/decrets."""
        response = await self._client.request(
            "DELETE",
            f"/companies/{company_id}/decrets",
            json=item_ids,
        )
        response.raise_for_status()
        return _safe_json(response)

    # -- KSeF -------------------------------------------------------------------

    async def get_ksef_xml(
        self,
        company_id: int,
        document_id: int,
        as_json: bool = False,
    ) -> str | dict[str, Any]:
        """GET /companies/{companyId}/documents/{documentId}/ksef-xml."""
        accept = "application/json" if as_json else "application/xml"
        response = await self._client.get(
            f"/companies/{company_id}/documents/{document_id}/ksef-xml",
            headers={"Accept": accept},
        )
        response.raise_for_status()
        return response.json() if as_json else response.text

    async def get_ksef_qr(self, company_id: int, document_id: int) -> bytes:
        """GET /companies/{companyId}/documents/{documentId}/ksef-qr."""
        response = await self._client.get(
            f"/companies/{company_id}/documents/{document_id}/ksef-qr",
        )
        response.raise_for_status()
        return response.content

    async def send_ksef_invoice(
        self,
        company_id: int,
        invoice_data: dict[str, Any],
    ) -> dict[str, Any]:
        """PUT /companies/{companyId}/ksef/online/FA3-1-0E — send FA3 invoice to KSeF."""
        response = await self._client.put(
            f"/companies/{company_id}/ksef/online/FA3-1-0E",
            json=invoice_data,
        )
        response.raise_for_status()
        return response.json()
