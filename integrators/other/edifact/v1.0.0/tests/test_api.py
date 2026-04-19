"""Tests for general API endpoints (health, readiness, accounts, connection)."""

from __future__ import annotations


class TestHealthEndpoints:
    def test_health(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_readiness(self, client):
        response = client.get("/readiness")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"


class TestAccountEndpoints:
    def test_list_accounts(self, client):
        response = client.get("/accounts")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_create_account(self, client):
        response = client.post(
            "/accounts",
            json={
                "name": "test-terminal",
                "base_url": "https://test.example.com",
                "api_key": "test-key",
                "description": "Test terminal",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "created"
        assert data["account"] == "test-terminal"

    def test_delete_account_not_found(self, client, mock_account_manager):
        from unittest.mock import MagicMock

        mock_account_manager.remove_account = MagicMock(side_effect=KeyError("nonexistent"))
        response = client.delete("/accounts/nonexistent")
        assert response.status_code == 404


class TestConnectionValidation:
    def test_validate_connection_success(self, client):
        response = client.post("/validate-connection?account_name=default")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "connected"

    def test_validate_connection_unknown_account(self, client, mock_account_manager):
        mock_account_manager.get_client.side_effect = KeyError("unknown")
        response = client.post("/validate-connection?account_name=unknown")
        assert response.status_code == 404
