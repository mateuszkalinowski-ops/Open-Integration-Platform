"""Tests for SkanujFakture integrator API routes."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from src.api.dependencies import app_state
from src.config import SkanujFaktureAccountConfig
from src.main import create_app
from src.services.account_manager import AccountManager
from src.skanuj_fakture.integration import SkanujFaktureIntegration
from src.skanuj_fakture.schemas import AuthStatusResponse, ConnectionStatus


@pytest.fixture
def client():
    application = create_app()
    with TestClient(application, raise_server_exceptions=False) as c:
        account_manager = AccountManager()
        account_manager.add_account(
            SkanujFaktureAccountConfig(
                name="test",
                login="test@example.com",
                password="pass",
                api_url="https://skanujfakture.pl:8443/SFApi",
            )
        )
        app_state.account_manager = account_manager

        integration = MagicMock(spec=SkanujFaktureIntegration)
        integration.get_auth_status.return_value = AuthStatusResponse(
            account_name="test",
            authenticated=True,
        )
        app_state.integration = integration

        yield c


class TestHealthEndpoints:
    def test_health_returns_ok(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.status_code == 200

    def test_readiness_returns_ok(self, client: TestClient) -> None:
        response = client.get("/readiness")
        assert response.status_code == 200


class TestAccountEndpoints:
    def test_list_accounts(self, client: TestClient) -> None:
        response = client.get("/accounts")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "test"

    def test_add_account(self, client: TestClient) -> None:
        response = client.post(
            "/accounts",
            json={
                "name": "new-account",
                "login": "new@example.com",
                "password": "secret",
                "api_url": "https://skanujfakture.pl:8443/SFApi",
            },
        )
        assert response.status_code == 201
        assert response.json()["name"] == "new-account"

    def test_remove_account(self, client: TestClient) -> None:
        client.post(
            "/accounts",
            json={
                "name": "to-remove",
                "login": "remove@example.com",
                "password": "secret",
                "api_url": "https://skanujfakture.pl:8443/SFApi",
            },
        )
        response = client.delete("/accounts/to-remove")
        assert response.status_code == 200

    def test_remove_nonexistent_account(self, client: TestClient) -> None:
        response = client.delete("/accounts/nonexistent")
        assert response.status_code == 404


class TestAuthEndpoints:
    def test_auth_status(self, client: TestClient) -> None:
        response = client.get("/auth/test/status")
        assert response.status_code == 200
        data = response.json()
        assert data["account_name"] == "test"
        assert data["authenticated"]

    def test_auth_status_unknown_account(self, client: TestClient) -> None:
        response = client.get("/auth/nonexistent/status")
        assert response.status_code == 404

    def test_all_auth_statuses(self, client: TestClient) -> None:
        response = client.get("/auth/status")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1


class TestConnectionEndpoint:
    def test_connection_status(self, client: TestClient) -> None:
        app_state.integration.get_connection_status = AsyncMock(
            return_value=ConnectionStatus(
                account_name="test",
                connected=True,
                companies_count=2,
            ),
        )
        response = client.get("/connection/test/status")
        assert response.status_code == 200
        data = response.json()
        assert data["connected"]
        assert data["companies_count"] == 2

    def test_connection_status_unknown_account(self, client: TestClient) -> None:
        response = client.get("/connection/nonexistent/status")
        assert response.status_code == 404


class TestCompanyEndpoints:
    def test_list_companies(self, client: TestClient) -> None:
        app_state.integration.get_companies = AsyncMock(
            return_value=[
                {"company": {"id": 1, "contractor": {"name": "Firma A"}}},
            ]
        )
        response = client.get("/companies?account_name=test")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    def test_list_companies_unknown_account(self, client: TestClient) -> None:
        response = client.get("/companies?account_name=nonexistent")
        assert response.status_code == 404

    def test_list_company_entities(self, client: TestClient) -> None:
        app_state.integration.get_company_entities = AsyncMock(
            return_value=[
                {"id": 100, "contractorDTO": {"name": "Podmiot A"}},
            ]
        )
        response = client.get("/companies/1/entities?account_name=test")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1


class TestDocumentEndpoints:
    def test_upload_document(self, client: TestClient) -> None:
        app_state.integration.upload_document = AsyncMock(
            return_value={
                "documents": 1,
                "uploadedDocuments": 1,
                "documentsIdList": [123],
            }
        )
        response = client.post(
            "/companies/1/documents?account_name=test",
            files={"file": ("invoice.pdf", b"fake-pdf-content", "application/pdf")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["uploadedDocuments"] == 1

    def test_upload_document_unknown_account(self, client: TestClient) -> None:
        response = client.post(
            "/companies/1/documents?account_name=nonexistent",
            files={"file": ("invoice.pdf", b"fake-pdf-content", "application/pdf")},
        )
        assert response.status_code == 404

    def test_list_documents(self, client: TestClient) -> None:
        app_state.integration.get_documents = AsyncMock(
            return_value=[
                {"id": 1, "number": "FV-001", "netto": 100.0},
            ]
        )
        response = client.get("/companies/1/documents?account_name=test")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["number"] == "FV-001"

    def test_list_documents_with_filters(self, client: TestClient) -> None:
        app_state.integration.get_documents = AsyncMock(return_value=[])
        response = client.get(
            "/companies/1/documents?account_name=test&document_statuses=zeskanowany&is_sale=false",
        )
        assert response.status_code == 200

    def test_list_documents_simple(self, client: TestClient) -> None:
        app_state.integration.get_documents_simple = AsyncMock(
            return_value=[
                {"id": 1, "number": "FV-001", "date": "2026-01-01"},
            ]
        )
        response = client.get("/companies/1/documents/simple?account_name=test")
        assert response.status_code == 200

    def test_update_document(self, client: TestClient) -> None:
        app_state.integration.update_document = AsyncMock(
            return_value={
                "id": 1,
                "number": "FV-001-UPDATED",
            }
        )
        response = client.put(
            "/companies/1/documents/1?account_name=test",
            json={"data": {"number": "FV-001-UPDATED"}},
        )
        assert response.status_code == 200

    def test_delete_documents(self, client: TestClient) -> None:
        app_state.integration.delete_documents = AsyncMock(return_value={"deleted": 1})
        response = client.request(
            "DELETE",
            "/companies/1/documents?account_name=test",
            json={"checkDocumentIds": [1, 2]},
        )
        assert response.status_code == 200

    def test_get_document_file(self, client: TestClient) -> None:
        app_state.integration.get_document_file = AsyncMock(return_value=b"pdf-bytes")
        response = client.get("/companies/1/documents/1/file?account_name=test")
        assert response.status_code == 200
        data = response.json()
        assert "content_base64" in data

    def test_get_document_image(self, client: TestClient) -> None:
        app_state.integration.get_document_image = AsyncMock(return_value=b"image-bytes")
        response = client.get("/companies/1/documents/1/image?account_name=test")
        assert response.status_code == 200
        data = response.json()
        assert "content_base64" in data


class TestAttributeEndpoints:
    def test_edit_attributes(self, client: TestClient) -> None:
        app_state.integration.edit_attributes = AsyncMock(return_value={"status": "ok"})
        response = client.put(
            "/companies/1/documents/1/attributes?account_name=test",
            json={"attributes": [{"name": "test_attr", "value": "test_val"}]},
        )
        assert response.status_code == 200

    def test_edit_attributes_with_status(self, client: TestClient) -> None:
        app_state.integration.edit_attributes = AsyncMock(return_value={"status": "ok"})
        response = client.put(
            "/companies/1/documents/1/attributes?account_name=test",
            json={
                "statusId": 3,
                "attributes": [{"name": "attr1", "value": "val1"}],
            },
        )
        assert response.status_code == 200

    def test_delete_attributes(self, client: TestClient) -> None:
        app_state.integration.delete_attributes = AsyncMock(return_value={"status": "ok"})
        response = client.delete("/companies/1/documents/1/attributes?account_name=test")
        assert response.status_code == 200


class TestDictionaryEndpoints:
    def test_list_dictionaries(self, client: TestClient) -> None:
        app_state.integration.get_dictionaries = AsyncMock(
            return_value=[
                {"id": 1, "symbol": "KS01", "description": "Koszt biurowy"},
            ]
        )
        response = client.get("/companies/1/dictionaries?type=COST_TYPE&account_name=test")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    def test_add_dictionary_items(self, client: TestClient) -> None:
        app_state.integration.add_dictionary_items = AsyncMock(return_value={"status": "ok"})
        response = client.post(
            "/companies/1/dictionaries?type=COST_TYPE&account_name=test",
            json={"items": [{"symbol": "KS02", "description": "Koszt marketingowy"}]},
        )
        assert response.status_code == 200


class TestKsefEndpoints:
    def test_get_ksef_xml(self, client: TestClient) -> None:
        app_state.integration.get_ksef_xml = AsyncMock(return_value="<Faktura>...</Faktura>")
        response = client.get("/companies/1/documents/1/ksef-xml?account_name=test")
        assert response.status_code == 200

    def test_get_ksef_xml_as_json(self, client: TestClient) -> None:
        app_state.integration.get_ksef_xml = AsyncMock(return_value={"fa": {}})
        response = client.get("/companies/1/documents/1/ksef-xml?account_name=test&as_json=true")
        assert response.status_code == 200

    def test_get_ksef_qr(self, client: TestClient) -> None:
        app_state.integration.get_ksef_qr = AsyncMock(return_value=b"qr-image-bytes")
        response = client.get("/companies/1/documents/1/ksef-qr?account_name=test")
        assert response.status_code == 200
        data = response.json()
        assert "content_base64" in data

    def test_send_ksef_invoice(self, client: TestClient) -> None:
        app_state.integration.send_ksef_invoice = AsyncMock(
            return_value={
                "documentId": 15376,
                "ksefNumber": "3409269364-20251212-0100C0255A62-EA",
            }
        )
        response = client.put(
            "/companies/1/ksef/invoice?account_name=test",
            json={"invoice_data": {"fa": {"kodWaluty": "PLN"}}},
        )
        assert response.status_code == 200
        data = response.json()
        assert "ksefNumber" in data
