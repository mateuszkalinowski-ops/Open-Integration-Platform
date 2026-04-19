"""Tests for BAPLIE schemas and API endpoints."""

from __future__ import annotations

from src.schemas.baplie import BayPlan, PlanType, StowageLocation, StowedEquipment
from src.schemas.common import Equipment, Location, Transport, Weight


class TestBaplieSchemas:
    def test_bay_plan_minimal(self):
        plan = BayPlan(
            document_id="BAPLIE-001",
            plan_type=PlanType.PROVISIONAL,
            vessel=Transport(mode="sea", vessel_name="EVER GIVEN", vessel_imo="9811000"),
        )
        assert plan.document_id == "BAPLIE-001"
        assert plan.plan_type == PlanType.PROVISIONAL
        assert plan.vessel.vessel_name == "EVER GIVEN"

    def test_bay_plan_with_locations(self):
        plan = BayPlan(
            document_id="BAPLIE-002",
            plan_type=PlanType.FINAL,
            vessel=Transport(mode="sea", carrier="MAEU", vessel_name="MAERSK EDINBURGH", voyage_number="426E"),
            ports_of_call=[Location(qualifier="port", un_locode="PLGDY", name="Gdynia")],
            locations=[
                StowageLocation(
                    bay="01",
                    row="02",
                    tier="82",
                    position_code="010282",
                    is_empty=False,
                    equipment=StowedEquipment(
                        equipment=Equipment(container_id="MSKU1234567", iso_size_type="22G1", full_empty="full"),
                        weight=Weight(value=28500.0, unit="KGM", qualifier="G"),
                        port_of_loading=Location(qualifier="port", un_locode="DEHAM"),
                        port_of_discharge=Location(qualifier="port", un_locode="PLGDY"),
                    ),
                ),
                StowageLocation(bay="01", row="04", tier="82", is_empty=True),
            ],
        )
        data = plan.model_dump(mode="json")
        assert len(data["locations"]) == 2
        assert data["locations"][0]["is_empty"] is False
        assert data["locations"][1]["is_empty"] is True

    def test_stowage_location_defaults(self):
        loc = StowageLocation(bay="05", row="01", tier="02")
        assert loc.is_empty is True
        assert loc.equipment is None
        assert loc.cell_type == "standard"

    def test_stowed_equipment_with_reefer(self):
        from src.schemas.common import ReeferSettings

        equip = StowedEquipment(
            equipment=Equipment(container_id="RUKU1234567", iso_size_type="45R1"),
            reefer_settings=ReeferSettings(set_temperature=-18.0, unit="CEL", min_temperature=-20.0),
        )
        assert equip.reefer_settings is not None
        assert equip.reefer_settings.set_temperature == -18.0


class TestBaplieApi:
    def test_create_bay_plan(self, client):
        response = client.post(
            "/baplie/bay-plans",
            json={
                "document_id": "BAPLIE-2026-0001",
                "plan_type": "provisional",
                "vessel": {"mode": "sea", "vessel_name": "TEST VESSEL", "vessel_imo": "9811000"},
                "locations": [{"bay": "01", "row": "02", "tier": "82", "is_empty": True}],
            },
        )
        assert response.status_code == 201

    def test_list_bay_plans(self, client):
        response = client.get("/baplie/bay-plans?account_name=default")
        assert response.status_code == 200

    def test_get_bay_plan(self, client):
        response = client.get("/baplie/bay-plans/BP-001?account_name=default")
        assert response.status_code == 200

    def test_get_bay_plan_locations(self, client):
        response = client.get("/baplie/bay-plans/BP-001/locations?account_name=default")
        assert response.status_code == 200

    def test_get_bay_plan_locations_with_filters(self, client):
        response = client.get("/baplie/bay-plans/BP-001/locations?account_name=default&bay=01&tier=82")
        assert response.status_code == 200
