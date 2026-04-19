"""Shared test fixtures for EDIFACT connector tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from src.api.dependencies import app_state
from src.main import create_app
from src.services.account_manager import AccountManager


@pytest.fixture()
def mock_account_manager():
    manager = MagicMock(spec=AccountManager)
    manager.list_accounts.return_value = [
        {"name": "default", "base_url": "http://test:9000", "description": "test", "has_api_key": True}
    ]

    mock_client = AsyncMock()
    mock_client.check_health.return_value = {"status": "healthy"}
    mock_client.create_gate_event.return_value = {
        "event_id": "EVT-001",
        "document_id": "CODECO-2026-0001",
        "status": "accepted",
    }
    mock_client.list_gate_events.return_value = {"items": [], "total": 0}
    mock_client.get_gate_event.return_value = {"event_id": "EVT-001", "document_id": "CODECO-2026-0001"}
    mock_client.update_gate_event.return_value = {
        "event_id": "EVT-001",
        "document_id": "CODECO-2026-0001",
        "status": "updated",
    }
    mock_client.cancel_gate_event.return_value = {"status": "cancelled"}

    mock_client.create_bay_plan.return_value = {
        "plan_id": "BP-001",
        "document_id": "BAPLIE-2026-0001",
        "status": "accepted",
        "total_locations": 1,
    }
    mock_client.list_bay_plans.return_value = {"items": [], "total": 0}
    mock_client.get_bay_plan.return_value = {"plan_id": "BP-001", "document_id": "BAPLIE-2026-0001"}
    mock_client.update_bay_plan.return_value = {
        "plan_id": "BP-001",
        "document_id": "BAPLIE-2026-0001",
        "status": "updated",
        "total_locations": 1,
    }
    mock_client.get_bay_plan_locations.return_value = {"locations": []}

    mock_client.create_instruction.return_value = {
        "instruction_id": "IFTMIN-2026-0001",
        "status": "accepted",
    }
    mock_client.list_instructions.return_value = {"items": [], "total": 0}
    mock_client.get_instruction.return_value = {"instruction_id": "IFTMIN-2026-0001"}
    mock_client.amend_instruction.return_value = {
        "instruction_id": "IFTMIN-2026-0001",
        "status": "amended",
    }
    mock_client.cancel_instruction.return_value = {"status": "cancelled"}

    manager.get_client.return_value = mock_client
    return manager


@pytest.fixture()
def client(mock_account_manager):
    application = create_app()
    with TestClient(application, raise_server_exceptions=False) as c:
        app_state.account_manager = mock_account_manager
        app_state.health_checker = None
        yield c
    app_state.account_manager = None
    app_state.health_checker = None
