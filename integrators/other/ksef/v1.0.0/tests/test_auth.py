"""Tests for KSeF authentication flow."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.ksef.auth import AuthSession, _parse_datetime


class TestAuthSession:
    def test_empty_session_is_not_valid(self) -> None:
        session = AuthSession()
        assert not session.is_access_valid
        assert not session.is_refresh_valid

    def test_session_with_future_expiry_is_valid(self) -> None:
        session = AuthSession(
            access_token="token123",
            access_valid_until=datetime(2099, 1, 1, tzinfo=timezone.utc),
            refresh_token="refresh123",
            refresh_valid_until=datetime(2099, 1, 1, tzinfo=timezone.utc),
            nip="1234567890",
        )
        assert session.is_access_valid
        assert session.is_refresh_valid

    def test_session_with_past_expiry_is_not_valid(self) -> None:
        session = AuthSession(
            access_token="token123",
            access_valid_until=datetime(2020, 1, 1, tzinfo=timezone.utc),
            nip="1234567890",
        )
        assert not session.is_access_valid

    def test_bearer_headers(self) -> None:
        session = AuthSession(access_token="my_token")
        headers = session.bearer_headers
        assert headers["Authorization"] == "Bearer my_token"
        assert headers["Content-Type"] == "application/json"


class TestParseDatetime:
    def test_parse_iso_format(self) -> None:
        dt = _parse_datetime("2026-03-29T10:00:00+00:00")
        assert dt.year == 2026
        assert dt.month == 3
        assert dt.day == 29

    def test_parse_z_suffix(self) -> None:
        dt = _parse_datetime("2026-03-29T10:00:00Z")
        assert dt.year == 2026

    def test_parse_with_microseconds(self) -> None:
        dt = _parse_datetime("2026-03-29T10:00:00.123456+00:00")
        assert dt.microsecond == 123456

    def test_parse_strips_whitespace(self) -> None:
        dt = _parse_datetime("  2026-03-29T10:00:00+00:00  ")
        assert dt.year == 2026
