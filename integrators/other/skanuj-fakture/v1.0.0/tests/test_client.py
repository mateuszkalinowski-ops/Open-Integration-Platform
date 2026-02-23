"""Tests for SkanujFakture HTTP client."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

import httpx

from src.config import SkanujFaktureAccountConfig
from src.skanuj_fakture.client import SkanujFaktureClient


@pytest.fixture
def account():
    return SkanujFaktureAccountConfig(
        name="test",
        login="test@example.com",
        password="test-password",
        api_url="https://skanujfakture.pl:8443/SFApi",
    )


@pytest.fixture
def client(account):
    return SkanujFaktureClient(account)


class TestClientInit:
    def test_creates_client_with_basic_auth(self, client: SkanujFaktureClient) -> None:
        assert client._client is not None
        auth_header = client._client.headers.get("authorization")
        assert auth_header is not None
        assert auth_header.startswith("Basic ")

    def test_base_url_set(self, client: SkanujFaktureClient) -> None:
        assert str(client._client.base_url) == "https://skanujfakture.pl:8443/SFApi"


class TestCompanyMethods:
    @pytest.mark.asyncio
    async def test_get_companies(self, client: SkanujFaktureClient) -> None:
        mock_response = MagicMock()
        mock_response.json.return_value = [{"company": {"id": 1}}]
        mock_response.raise_for_status = MagicMock()

        client._client.get = AsyncMock(return_value=mock_response)
        result = await client.get_companies()

        client._client.get.assert_called_once_with("/users/currentUser/companies")
        assert len(result) == 1
        assert result[0]["company"]["id"] == 1

    @pytest.mark.asyncio
    async def test_get_company_entities(self, client: SkanujFaktureClient) -> None:
        mock_response = MagicMock()
        mock_response.json.return_value = [{"id": 100, "status": "ACTIVE"}]
        mock_response.raise_for_status = MagicMock()

        client._client.get = AsyncMock(return_value=mock_response)
        result = await client.get_company_entities(1)

        client._client.get.assert_called_once_with("/companies/1/companyEntities")
        assert result[0]["id"] == 100


class TestDocumentMethods:
    @pytest.mark.asyncio
    async def test_upload_document(self, client: SkanujFaktureClient) -> None:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "documents": 1, "uploadedDocuments": 1, "documentsIdList": [42],
        }
        mock_response.raise_for_status = MagicMock()

        client._client.post = AsyncMock(return_value=mock_response)
        result = await client.upload_document(1, b"pdf-content", "test.pdf", True, False)

        assert result["uploadedDocuments"] == 1
        assert 42 in result["documentsIdList"]

    @pytest.mark.asyncio
    async def test_get_documents(self, client: SkanujFaktureClient) -> None:
        mock_response = MagicMock()
        mock_response.json.return_value = [{"id": 1, "number": "FV-001"}]
        mock_response.raise_for_status = MagicMock()

        client._client.get = AsyncMock(return_value=mock_response)
        result = await client.get_documents(1, document_statuses=["zeskanowany"])

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_documents_simple(self, client: SkanujFaktureClient) -> None:
        mock_response = MagicMock()
        mock_response.json.return_value = [{"id": 1, "number": "FV-001"}]
        mock_response.raise_for_status = MagicMock()

        client._client.get = AsyncMock(return_value=mock_response)
        result = await client.get_documents_simple(1)

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_update_document(self, client: SkanujFaktureClient) -> None:
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": 1, "number": "FV-UPDATED"}
        mock_response.raise_for_status = MagicMock()

        client._client.put = AsyncMock(return_value=mock_response)
        result = await client.update_document(1, 1, {"number": "FV-UPDATED"})

        assert result["number"] == "FV-UPDATED"

    @pytest.mark.asyncio
    async def test_delete_documents(self, client: SkanujFaktureClient) -> None:
        mock_response = MagicMock()
        mock_response.json.return_value = {"deleted": 1}
        mock_response.raise_for_status = MagicMock()

        client._client.delete = AsyncMock(return_value=mock_response)
        result = await client.delete_documents(1, check_document_ids=[1])

        assert result["deleted"] == 1

    @pytest.mark.asyncio
    async def test_get_document_file(self, client: SkanujFaktureClient) -> None:
        mock_response = MagicMock()
        mock_response.content = b"pdf-binary-content"
        mock_response.raise_for_status = MagicMock()

        client._client.get = AsyncMock(return_value=mock_response)
        result = await client.get_document_file(1, 42)

        assert result == b"pdf-binary-content"

    @pytest.mark.asyncio
    async def test_get_document_image(self, client: SkanujFaktureClient) -> None:
        mock_response = MagicMock()
        mock_response.content = b"image-binary-content"
        mock_response.raise_for_status = MagicMock()

        client._client.get = AsyncMock(return_value=mock_response)
        result = await client.get_document_image(1, 42)

        assert result == b"image-binary-content"


class TestAttributeMethods:
    @pytest.mark.asyncio
    async def test_edit_attributes(self, client: SkanujFaktureClient) -> None:
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok"}
        mock_response.raise_for_status = MagicMock()

        client._client.put = AsyncMock(return_value=mock_response)
        result = await client.edit_attributes(
            1, 42, [{"name": "attr1", "value": "val1"}], status_id=3,
        )

        assert result["status"] == "ok"

    @pytest.mark.asyncio
    async def test_delete_attributes(self, client: SkanujFaktureClient) -> None:
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok"}
        mock_response.raise_for_status = MagicMock()

        client._client.delete = AsyncMock(return_value=mock_response)
        result = await client.delete_attributes(1, 42)

        assert result["status"] == "ok"


class TestDictionaryMethods:
    @pytest.mark.asyncio
    async def test_get_dictionaries(self, client: SkanujFaktureClient) -> None:
        mock_response = MagicMock()
        mock_response.json.return_value = [{"id": 1, "symbol": "KS01"}]
        mock_response.raise_for_status = MagicMock()

        client._client.get = AsyncMock(return_value=mock_response)
        result = await client.get_dictionaries(1, "COST_TYPE")

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_add_dictionary_items(self, client: SkanujFaktureClient) -> None:
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok"}
        mock_response.raise_for_status = MagicMock()

        client._client.post = AsyncMock(return_value=mock_response)
        result = await client.add_dictionary_items(
            1, "COST_TYPE", [{"symbol": "KS02", "description": "Test"}],
        )

        assert result["status"] == "ok"

    @pytest.mark.asyncio
    async def test_update_dictionary_items(self, client: SkanujFaktureClient) -> None:
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok"}
        mock_response.raise_for_status = MagicMock()

        client._client.put = AsyncMock(return_value=mock_response)
        result = await client.update_dictionary_items(
            1, "COST_TYPE", [{"id": 1, "symbol": "KS01", "description": "Updated"}],
        )

        assert result["status"] == "ok"

    @pytest.mark.asyncio
    async def test_delete_dictionary_items(self, client: SkanujFaktureClient) -> None:
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok"}
        mock_response.raise_for_status = MagicMock()

        client._client.delete = AsyncMock(return_value=mock_response)
        result = await client.delete_dictionary_items(1, [1, 2])

        assert result["status"] == "ok"


class TestKsefMethods:
    @pytest.mark.asyncio
    async def test_get_ksef_xml(self, client: SkanujFaktureClient) -> None:
        mock_response = MagicMock()
        mock_response.text = "<Faktura></Faktura>"
        mock_response.raise_for_status = MagicMock()

        client._client.get = AsyncMock(return_value=mock_response)
        result = await client.get_ksef_xml(1, 42, as_json=False)

        assert "<Faktura>" in result

    @pytest.mark.asyncio
    async def test_get_ksef_xml_as_json(self, client: SkanujFaktureClient) -> None:
        mock_response = MagicMock()
        mock_response.json.return_value = {"fa": {"kodWaluty": "PLN"}}
        mock_response.raise_for_status = MagicMock()

        client._client.get = AsyncMock(return_value=mock_response)
        result = await client.get_ksef_xml(1, 42, as_json=True)

        assert result["fa"]["kodWaluty"] == "PLN"

    @pytest.mark.asyncio
    async def test_get_ksef_qr(self, client: SkanujFaktureClient) -> None:
        mock_response = MagicMock()
        mock_response.content = b"qr-code-bytes"
        mock_response.raise_for_status = MagicMock()

        client._client.get = AsyncMock(return_value=mock_response)
        result = await client.get_ksef_qr(1, 42)

        assert result == b"qr-code-bytes"

    @pytest.mark.asyncio
    async def test_send_ksef_invoice(self, client: SkanujFaktureClient) -> None:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "documentId": 15376,
            "ksefNumber": "3409269364-20251212-0100C0255A62-EA",
        }
        mock_response.raise_for_status = MagicMock()

        client._client.put = AsyncMock(return_value=mock_response)
        result = await client.send_ksef_invoice(1, {"fa": {}})

        assert result["documentId"] == 15376
        assert "ksefNumber" in result
