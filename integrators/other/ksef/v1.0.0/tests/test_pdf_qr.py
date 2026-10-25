"""PDF as base64 for workflows and the official KSeF verification QR (KOD I)."""

import base64
import hashlib
from typing import Any

import pytest
from fastapi.testclient import TestClient
from src.api.dependencies import app_state
from src.ksef import pdf_renderer
from src.ksef.pdf_renderer import build_verification_url, render_invoice_pdf
from src.ksef.xml_builder import build_invoice_xml
from src.main import create_app
from src.services.account_manager import AccountManager

from tests.test_xml_builder import SAMPLE_INVOICE_DATA

KSEF_NUMBER = "1234567890-20260329-0100A0B1C2D3-4E"


@pytest.fixture
def invoice_xml() -> bytes:
    return build_invoice_xml(SAMPLE_INVOICE_DATA)


def _b64url_sha256(data: bytes) -> str:
    return base64.urlsafe_b64encode(hashlib.sha256(data).digest()).decode().rstrip("=")


class TestVerificationUrl:
    def test_official_format_with_computed_hash(self, invoice_xml: bytes) -> None:
        url = build_verification_url(invoice_xml, "production")
        assert url == f"https://qr.ksef.mf.gov.pl/invoice/1234567890/29-03-2026/{_b64url_sha256(invoice_xml)}"

    @pytest.mark.parametrize(
        ("env", "host"),
        [("test", "https://qr-test.ksef.mf.gov.pl"), ("demo", "https://qr-demo.ksef.mf.gov.pl")],
    )
    def test_host_per_environment(self, invoice_xml: bytes, env: str, host: str) -> None:
        assert build_verification_url(invoice_xml, env).startswith(f"{host}/invoice/")

    def test_hash_from_ksef_is_converted_to_base64url(self, invoice_xml: bytes) -> None:
        digest = hashlib.sha256(b"original file").digest()
        std_b64 = base64.b64encode(digest).decode()
        url = build_verification_url(invoice_xml, "production", invoice_hash=std_b64)
        assert url.endswith("/" + base64.urlsafe_b64encode(digest).decode().rstrip("="))
        assert "+" not in url.split("/")[-1] and "=" not in url

    def test_missing_seller_nip_gives_no_url(self) -> None:
        data = {**SAMPLE_INVOICE_DATA, "seller": {**SAMPLE_INVOICE_DATA["seller"], "nip": ""}}
        assert build_verification_url(build_invoice_xml(data), "production") == ""


class TestPdfQr:
    def test_pdf_qr_encodes_official_url(self, invoice_xml: bytes, monkeypatch: pytest.MonkeyPatch) -> None:
        seen: list[str] = []
        original = pdf_renderer._make_qr_drawing

        def spy(data: str, *args: Any, **kwargs: Any) -> Any:
            seen.append(data)
            return original(data, *args, **kwargs)

        monkeypatch.setattr(pdf_renderer, "_make_qr_drawing", spy)
        pdf = render_invoice_pdf(invoice_xml, ksef_number=KSEF_NUMBER, environment="production")
        assert pdf.startswith(b"%PDF")
        assert seen == [build_verification_url(invoice_xml, "production")]


class FakeClient:
    def __init__(self, xml: bytes) -> None:
        self._xml = xml

    async def get_invoice(self, ksef_number: str) -> dict[str, str]:
        return {"invoice_xml": self._xml.decode("utf-8"), "ksef_reference_number": ksef_number}


@pytest.fixture
def client(invoice_xml: bytes) -> TestClient:
    mgr = AccountManager()
    mgr.add_account({"name": "acc", "nip": "1234567890", "ksef_token": "t", "environment": "production"})
    mgr._clients["acc"] = FakeClient(invoice_xml)  # type: ignore[assignment]
    app = create_app()
    app_state.account_manager = mgr
    app_state.health_checker = None
    return TestClient(app, raise_server_exceptions=False)


class TestPdfBase64Endpoint:
    def test_returns_pdf_as_base64(self, client: TestClient, invoice_xml: bytes) -> None:
        resp = client.get(f"/invoices/{KSEF_NUMBER}/pdf/base64", params={"account_name": "acc"})
        assert resp.status_code == 200
        body = resp.json()
        assert base64.b64decode(body["pdf_base64"]).startswith(b"%PDF")
        assert body["pdf_filename"] == f"faktura_{KSEF_NUMBER}.pdf"
        assert body["ksef_number"] == KSEF_NUMBER
        assert body["verification_url"] == build_verification_url(invoice_xml, "production")

    def test_unknown_account_returns_404(self, client: TestClient) -> None:
        resp = client.get(f"/invoices/{KSEF_NUMBER}/pdf/base64", params={"account_name": "nope"})
        assert resp.status_code == 404

    def test_binary_pdf_endpoint_still_works(self, client: TestClient) -> None:
        resp = client.get(f"/invoices/{KSEF_NUMBER}/pdf", params={"account_name": "acc"})
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"
        assert resp.content.startswith(b"%PDF")
