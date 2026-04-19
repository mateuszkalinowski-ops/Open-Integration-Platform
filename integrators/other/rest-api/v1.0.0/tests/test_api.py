"""Tests for REST API Gateway routes."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_health(test_client: TestClient):
    response = test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "rest-api-connector"


def test_readiness(test_client: TestClient):
    response = test_client.get("/readiness")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["accounts_count"] == 2


def test_list_accounts(test_client: TestClient):
    response = test_client.get("/accounts")
    assert response.status_code == 200
    accounts = response.json()
    assert len(accounts) == 2
    names = {a["name"] for a in accounts}
    assert "test-pinquark" in names
    assert "test-generic" in names


def test_get_account(test_client: TestClient):
    response = test_client.get("/accounts/test-pinquark")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "test-pinquark"
    assert data["base_url"] == "https://test.pinquark.app"
    assert data["auth_type"] == "bearer_with_custom_headers"
    assert data["actions_count"] == 2


def test_get_account_not_found(test_client: TestClient):
    response = test_client.get("/accounts/nonexistent")
    assert response.status_code == 404


def test_list_account_actions(test_client: TestClient):
    response = test_client.get("/accounts/test-pinquark/actions")
    assert response.status_code == 200
    actions = response.json()
    assert "awk.create" in actions
    assert actions["awk.create"]["endpoint"] == "tos_notification_rail_save"
    assert "events.poll" in actions


def test_rest_call_missing_endpoint_and_action(test_client: TestClient):
    response = test_client.post(
        "/rest/call",
        json={
            "account": "test-pinquark",
        },
    )
    assert response.status_code == 400


def test_rest_call_account_not_found(test_client: TestClient):
    response = test_client.post(
        "/rest/call",
        json={
            "account": "nonexistent",
            "endpoint": "test",
        },
    )
    assert response.status_code == 404


def test_rest_poll_missing_endpoint(test_client: TestClient):
    response = test_client.post(
        "/rest/poll",
        json={
            "account": "test-pinquark",
        },
    )
    assert response.status_code == 400


def test_rest_health_account_not_found(test_client: TestClient):
    response = test_client.get("/rest/health/nonexistent")
    assert response.status_code == 404
