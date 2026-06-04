"""Tests for KSeF client operations."""

from datetime import UTC, datetime

import pytest
from src.config import KSeFAccountConfig, KSeFEnvironment
from src.ksef.auth import AuthSession
from src.ksef.client import FA3_FORM_CODE, KSeFClient

_FAR_FUTURE = datetime(2099, 1, 1, tzinfo=UTC)


class TestKSeFClientInit:
    def test_client_initializes_with_demo_account(self) -> None:
        account = KSeFAccountConfig(
            name="test",
            nip="1234567890",
            ksef_token="test-token",
            environment=KSeFEnvironment.DEMO,
        )
        client = KSeFClient(account)
        assert client._api_url == "https://api-demo.ksef.mf.gov.pl/api/v2"
        assert not client.is_authenticated

    def test_client_initializes_with_production_account(self) -> None:
        account = KSeFAccountConfig(
            name="prod",
            nip="1234567890",
            ksef_token="prod-token",
            environment=KSeFEnvironment.PRODUCTION,
        )
        client = KSeFClient(account)
        assert client._api_url == "https://api.ksef.mf.gov.pl/api/v2"

    def test_client_initializes_with_test_account(self) -> None:
        account = KSeFAccountConfig(
            name="test-env",
            nip="1234567890",
            ksef_token="test-token",
            environment=KSeFEnvironment.TEST,
        )
        client = KSeFClient(account)
        assert client._api_url == "https://api-test.ksef.mf.gov.pl/api/v2"


class TestFA3FormCode:
    def test_form_code_structure(self) -> None:
        assert FA3_FORM_CODE["systemCode"] == "FA (3)"
        assert FA3_FORM_CODE["schemaVersion"] == "1-0E"
        assert FA3_FORM_CODE["value"] == "FA"


class TestKSeFClientValidation:
    @pytest.mark.asyncio
    async def test_send_invoice_without_session_raises(self) -> None:
        account = KSeFAccountConfig(
            name="test",
            nip="1234567890",
            ksef_token="test-token",
            environment=KSeFEnvironment.TEST,
        )
        client = KSeFClient(account)
        client._auth_session = AuthSession(
            access_token="fake",
            access_valid_until=_FAR_FUTURE,
            reference_number="",
        )
        with pytest.raises(ValueError, match="No session reference"):
            await client.send_invoice(b"<Faktura/>")

    @pytest.mark.asyncio
    async def test_close_session_without_reference_raises(self) -> None:
        account = KSeFAccountConfig(
            name="test",
            nip="1234567890",
            ksef_token="test-token",
            environment=KSeFEnvironment.TEST,
        )
        client = KSeFClient(account)
        client._auth_session = AuthSession(
            access_token="fake",
            access_valid_until=_FAR_FUTURE,
            reference_number="",
        )
        with pytest.raises(ValueError, match="No session reference"):
            await client.close_session()

    @pytest.mark.asyncio
    async def test_get_session_status_without_reference_raises(self) -> None:
        account = KSeFAccountConfig(
            name="test",
            nip="1234567890",
            ksef_token="test-token",
            environment=KSeFEnvironment.TEST,
        )
        client = KSeFClient(account)
        client._auth_session = AuthSession(
            access_token="fake",
            access_valid_until=_FAR_FUTURE,
            reference_number="",
        )
        with pytest.raises(ValueError, match="No session reference"):
            await client.get_session_status()
