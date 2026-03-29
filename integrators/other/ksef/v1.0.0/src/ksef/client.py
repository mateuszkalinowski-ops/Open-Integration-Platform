"""KSeF 2.0 API client — sessions, invoice sending, querying, UPO retrieval.

Handles the full lifecycle:
1. Authentication (via KSeFAuthenticator)
2. Session management (open/close online and batch sessions)
3. Invoice encryption and sending
4. Invoice retrieval and status checks
5. UPO (Urzędowe Poświadczenie Odbioru) download
"""

from __future__ import annotations

import base64
import logging
from datetime import datetime
from typing import Any

import httpx

from src.config import KSeFAccountConfig
from src.ksef.auth import AuthSession, KSeFAuthenticator
from src.ksef.crypto import (
    generate_aes_key,
    sha256_base64,
    wrap_key_rsa_oaep,
)
from src.ksef.schemas import (
    InvoiceQueryResponse,
    SendInvoiceResponse,
    SessionOpenResponse,
)

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = httpx.Timeout(60.0, connect=30.0)

FA3_FORM_CODE = {
    "systemCode": "FA (3)",
    "schemaVersion": "1-0E",
    "value": "FA",
}


class KSeFClient:
    """Async client for KSeF 2.0 API operations."""

    def __init__(self, account: KSeFAccountConfig) -> None:
        self._account = account
        self._api_url = account.api_url.rstrip("/")
        self._client = httpx.AsyncClient(timeout=DEFAULT_TIMEOUT)
        self._authenticator = KSeFAuthenticator(
            api_url=self._api_url,
            client=self._client,
        )
        self._auth_session: AuthSession | None = None
        self._session_aes_key: bytes | None = None
        self._session_iv: bytes | None = None
        self._session_reference: str | None = None

    async def close(self) -> None:
        await self._client.aclose()

    @property
    def is_authenticated(self) -> bool:
        return self._auth_session is not None and self._auth_session.is_access_valid

    # -- Authentication --

    async def authenticate(self) -> AuthSession:
        """Authenticate with KSeF using the account's token."""
        if not self._account.ksef_token:
            raise ValueError(
                f"ksef_token is required for account '{self._account.name}'"
            )

        self._auth_session = await self._authenticator.authenticate_with_token(
            nip=self._account.nip,
            ksef_token=self._account.ksef_token,
        )
        return self._auth_session

    async def ensure_authenticated(self) -> AuthSession:
        """Ensure we have a valid auth session, refreshing or re-authenticating as needed."""
        if self._auth_session is None:
            return await self.authenticate()

        self._auth_session = await self._authenticator.ensure_valid_session(
            session=self._auth_session,
            nip=self._account.nip,
            ksef_token=self._account.ksef_token,
        )
        return self._auth_session

    # -- Sessions --

    async def open_session(
        self,
        session_type: str = "online",
        form_code: dict[str, str] | None = None,
    ) -> SessionOpenResponse:
        """Open an interactive or batch session for invoice sending."""
        from .crypto import generate_iv

        session = await self.ensure_authenticated()

        self._session_aes_key = generate_aes_key()
        self._session_iv = generate_iv()

        public_key, _ = await self._authenticator.get_public_key(usage="SymmetricKeyEncryption")
        wrapped_key = wrap_key_rsa_oaep(self._session_aes_key, public_key)  # type: ignore[arg-type]
        wrapped_key_b64 = base64.b64encode(wrapped_key).decode("ascii")
        iv_b64 = base64.b64encode(self._session_iv).decode("ascii")

        body = {
            "formCode": form_code or FA3_FORM_CODE,
            "encryption": {
                "encryptedSymmetricKey": wrapped_key_b64,
                "initializationVector": iv_b64,
            },
        }

        endpoint = "online" if session_type == "online" else "batch"
        response = await self._client.post(
            f"{self._api_url}/sessions/{endpoint}",
            json=body,
            headers=session.bearer_headers,
        )
        response.raise_for_status()

        result = SessionOpenResponse.model_validate(response.json())
        self._session_reference = result.reference_number
        logger.info(
            "Opened %s session ref=%s",
            session_type,
            result.reference_number,
        )
        return result

    async def close_session(
        self,
        reference_number: str | None = None,
        session_type: str = "online",
    ) -> dict[str, Any]:
        """Close an active session."""
        session = await self.ensure_authenticated()
        ref = reference_number or self._session_reference
        if not ref:
            raise ValueError("No session reference number provided or stored")

        endpoint = "online" if session_type == "online" else "batch"
        response = await self._client.post(
            f"{self._api_url}/sessions/{endpoint}/{ref}/close",
            headers=session.bearer_headers,
        )
        response.raise_for_status()

        logger.info("Closed %s session ref=%s", session_type, ref)
        if ref == self._session_reference:
            self._session_reference = None
            self._session_aes_key = None

        if response.status_code == 204 or not response.content:
            return {"status": "closed", "reference_number": ref}
        return response.json()

    async def get_session_status(
        self,
        reference_number: str | None = None,
        session_type: str = "online",
    ) -> dict[str, Any]:
        """Get the status of a session (v2: /sessions/{referenceNumber})."""
        session = await self.ensure_authenticated()
        ref = reference_number or self._session_reference
        if not ref:
            raise ValueError("No session reference number provided")

        response = await self._client.get(
            f"{self._api_url}/sessions/{ref}",
            headers=session.bearer_headers,
        )
        response.raise_for_status()
        return response.json()

    async def get_session_invoices(
        self,
        reference_number: str | None = None,
    ) -> list[dict[str, Any]]:
        """List invoices in a session (v2: /sessions/{ref}/invoices)."""
        session = await self.ensure_authenticated()
        ref = reference_number or self._session_reference
        if not ref:
            raise ValueError("No session reference number provided")

        response = await self._client.get(
            f"{self._api_url}/sessions/{ref}/invoices",
            headers=session.bearer_headers,
        )
        response.raise_for_status()
        return response.json()

    async def get_session_failed_invoices(
        self,
        reference_number: str | None = None,
    ) -> list[dict[str, Any]]:
        """List failed invoices in a session (v2: /sessions/{ref}/invoices/failed)."""
        session = await self.ensure_authenticated()
        ref = reference_number or self._session_reference
        if not ref:
            raise ValueError("No session reference number provided")

        response = await self._client.get(
            f"{self._api_url}/sessions/{ref}/invoices/failed",
            headers=session.bearer_headers,
        )
        response.raise_for_status()
        return response.json()

    async def get_invoice_in_session(
        self,
        invoice_reference_number: str,
        session_reference_number: str | None = None,
    ) -> dict[str, Any]:
        """Get single invoice status within a session."""
        session = await self.ensure_authenticated()
        ref = session_reference_number or self._session_reference
        if not ref:
            raise ValueError("No session reference number provided")

        response = await self._client.get(
            f"{self._api_url}/sessions/{ref}/invoices/{invoice_reference_number}",
            headers=session.bearer_headers,
        )
        response.raise_for_status()
        return response.json()

    # -- Invoices --

    async def send_invoice(
        self,
        invoice_xml: bytes,
        reference_number: str | None = None,
        session_type: str = "online",
    ) -> SendInvoiceResponse:
        """Encrypt and send an invoice in the current session (KSeF v2 format)."""
        from .crypto import encrypt_aes_cbc, generate_iv

        session = await self.ensure_authenticated()
        ref = reference_number or self._session_reference
        if not ref:
            raise ValueError("No session reference. Open a session first.")
        if not self._session_aes_key:
            raise ValueError("No session encryption key. Open a session first.")

        plain_hash = sha256_base64(invoice_xml)
        plain_size = len(invoice_xml)

        iv = self._session_iv or generate_iv()
        encrypted_data = encrypt_aes_cbc(invoice_xml, self._session_aes_key, iv)
        encrypted_hash = sha256_base64(encrypted_data)
        encrypted_size = len(encrypted_data)
        encrypted_b64 = base64.b64encode(encrypted_data).decode("ascii")

        body = {
            "invoiceHash": plain_hash,
            "invoiceSize": plain_size,
            "encryptedInvoiceHash": encrypted_hash,
            "encryptedInvoiceSize": encrypted_size,
            "encryptedInvoiceContent": encrypted_b64,
        }

        endpoint = "online" if session_type == "online" else "batch"
        response = await self._client.post(
            f"{self._api_url}/sessions/{endpoint}/{ref}/invoices",
            json=body,
            headers=session.bearer_headers,
        )
        response.raise_for_status()

        result = SendInvoiceResponse.model_validate(response.json())
        logger.info("Invoice sent, doc ref=%s", result.reference_number)
        return result

    async def get_invoice(
        self,
        ksef_reference_number: str,
    ) -> dict[str, Any]:
        """Retrieve an invoice XML by its KSeF number (v2: /invoices/ksef/{ksefNumber})."""
        session = await self.ensure_authenticated()
        response = await self._client.get(
            f"{self._api_url}/invoices/ksef/{ksef_reference_number}",
            headers=session.bearer_headers,
        )
        response.raise_for_status()
        content_type = response.headers.get("content-type", "")
        if "xml" in content_type:
            return {"invoice_xml": response.text, "ksef_reference_number": ksef_reference_number}
        return response.json()

    async def query_invoices(
        self,
        date_from: str | None = None,
        date_to: str | None = None,
        subject_nip: str | None = None,
        page_size: int = 10,
        page_offset: int = 0,
        subject_type: str = "Subject1",
        date_type: str = "Issue",
    ) -> InvoiceQueryResponse:
        """Query invoice metadata using KSeF v2 /invoices/query/metadata."""
        session = await self.ensure_authenticated()

        now = datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%S.000+00:00")
        body: dict[str, Any] = {
            "subjectType": subject_type,
            "dateRange": {
                "dateType": date_type,
                "from": date_from or "2026-01-01T00:00:00.000+00:00",
                "to": date_to or now,
            },
        }

        params: dict[str, Any] = {"pageSize": page_size, "pageOffset": page_offset, "sortOrder": "Desc"}

        response = await self._client.post(
            f"{self._api_url}/invoices/query/metadata",
            json=body,
            params=params,
            headers=session.bearer_headers,
        )
        response.raise_for_status()
        return InvoiceQueryResponse.model_validate(response.json())

    # -- UPO --

    async def get_upo(
        self,
        reference_number: str | None = None,
        session_type: str = "online",
    ) -> bytes:
        """Download UPO (Urzędowe Poświadczenie Odbioru) for a closed session."""
        session = await self.ensure_authenticated()
        ref = reference_number or self._session_reference
        if not ref:
            raise ValueError("No session reference number provided")

        endpoint = "online" if session_type == "online" else "batch"
        response = await self._client.get(
            f"{self._api_url}/sessions/{endpoint}/{ref}/upo",
            headers=session.bearer_headers,
        )
        response.raise_for_status()
        return response.content

    # -- Health --

    async def check_health(self) -> dict[str, Any]:
        """Check connectivity to KSeF API."""
        try:
            response = await self._client.get(
                f"{self._api_url}/security/public-key-certificates",
            )
            return {
                "status": "healthy" if response.status_code == 200 else "degraded",
                "api_url": self._api_url,
                "environment": self._account.environment.value,
                "status_code": response.status_code,
            }
        except (httpx.HTTPError, OSError) as exc:
            return {
                "status": "unhealthy",
                "api_url": self._api_url,
                "environment": self._account.environment.value,
                "error": str(exc),
            }
