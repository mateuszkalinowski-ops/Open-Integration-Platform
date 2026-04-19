"""Tests for CODECO schemas and API endpoints."""

from __future__ import annotations

import pytest
from src.schemas.codeco import ContainerMovement, GateEvent, GateEventType
from src.schemas.common import Equipment, FunctionCode, Location, Seal, Transport, Weight


class TestCodecoSchemas:
    def test_gate_event_minimal(self):
        event = GateEvent(
            document_id="CODECO-001",
            event_type=GateEventType.GATE_IN,
            event_timestamp="2026-04-15T08:30:00Z",
            transport=Transport(mode="road", conveyance_id="WGM12345"),
            containers=[
                ContainerMovement(
                    equipment=Equipment(container_id="MSKU1234567", iso_size_type="22G1"),
                )
            ],
        )
        assert event.document_id == "CODECO-001"
        assert event.event_type == GateEventType.GATE_IN
        assert len(event.containers) == 1
        assert event.containers[0].equipment.container_id == "MSKU1234567"

    def test_gate_event_full(self):
        event = GateEvent(
            document_id="CODECO-002",
            event_type=GateEventType.GATE_OUT,
            function_code=FunctionCode.ORIGINAL,
            event_timestamp="2026-04-15T10:00:00Z",
            transport=Transport(
                mode="sea",
                carrier="MAEU",
                vessel_name="MAERSK EDINBURGH",
                vessel_imo="9458100",
                voyage_number="426E",
            ),
            locations=[Location(qualifier="terminal", un_locode="PLGDY", name="BCT Gdynia")],
            containers=[
                ContainerMovement(
                    equipment=Equipment(container_id="MSKU1234567", iso_size_type="22G1", full_empty="full"),
                    weights=[Weight(value=28500.0, unit="KGM", qualifier="VGM")],
                    seals=[Seal(number="SL-001", type="carrier")],
                    locations=[Location(qualifier="port", un_locode="PLGDY")],
                )
            ],
        )
        data = event.model_dump(mode="json")
        assert data["event_type"] == "gate_out"
        assert data["transport"]["vessel_name"] == "MAERSK EDINBURGH"
        assert data["containers"][0]["weights"][0]["value"] == 28500.0

    def test_gate_event_requires_containers(self):
        with pytest.raises(ValueError):
            GateEvent(
                document_id="CODECO-003",
                event_type=GateEventType.GATE_IN,
                event_timestamp="2026-04-15T08:30:00Z",
                transport=Transport(mode="road"),
                containers=[],
            )

    def test_container_movement_with_dangerous_goods(self):
        from src.schemas.common import DangerousGoods

        movement = ContainerMovement(
            equipment=Equipment(container_id="TRIU1234567"),
            dangerous_goods=[
                DangerousGoods(imdg_class="3", un_number="UN1993", proper_shipping_name="Flammable liquid")
            ],
        )
        assert len(movement.dangerous_goods) == 1
        assert movement.dangerous_goods[0].imdg_class == "3"


class TestCodecoApi:
    def test_create_gate_event(self, client):
        response = client.post(
            "/codeco/gate-events",
            json={
                "document_id": "CODECO-2026-0001",
                "event_type": "gate_in",
                "function_code": "original",
                "event_timestamp": "2026-04-15T08:30:00Z",
                "transport": {"mode": "road", "conveyance_id": "WGM12345"},
                "containers": [
                    {
                        "equipment": {
                            "container_id": "MSKU1234567",
                            "iso_size_type": "22G1",
                            "full_empty": "full",
                        }
                    }
                ],
            },
        )
        assert response.status_code == 201

    def test_list_gate_events(self, client):
        response = client.get("/codeco/gate-events?account_name=default")
        assert response.status_code == 200

    def test_get_gate_event(self, client):
        response = client.get("/codeco/gate-events/EVT-001?account_name=default")
        assert response.status_code == 200

    def test_cancel_gate_event(self, client):
        response = client.delete("/codeco/gate-events/EVT-001?account_name=default")
        assert response.status_code == 200

    def test_create_gate_event_invalid_container_format(self, client):
        response = client.post(
            "/codeco/gate-events",
            json={
                "document_id": "CODECO-BAD",
                "event_type": "gate_in",
                "event_timestamp": "2026-04-15T08:30:00Z",
                "transport": {"mode": "road"},
                "containers": [{"equipment": {"container_id": "BAD", "iso_size_type": "22G1"}}],
            },
        )
        assert response.status_code == 422
