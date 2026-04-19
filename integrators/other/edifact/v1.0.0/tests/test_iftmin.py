"""Tests for IFTMIN schemas and API endpoints."""

from __future__ import annotations

import pytest
from src.schemas.common import Equipment, Location, Party, Weight
from src.schemas.iftmin import (
    DeliveryTerms,
    GoodsLine,
    InstructionFunction,
    InstructionLocations,
    InstructionParties,
    TransportInstruction,
    TransportStage,
)


class TestIftminSchemas:
    def test_transport_instruction_minimal(self):
        instruction = TransportInstruction(
            instruction_id="IFTMIN-001",
            goods_lines=[
                GoodsLine(line_number=1, description="Machine parts", packages_count=10),
            ],
        )
        assert instruction.instruction_id == "IFTMIN-001"
        assert instruction.function_code == InstructionFunction.ORIGINAL
        assert len(instruction.goods_lines) == 1

    def test_transport_instruction_full(self):
        instruction = TransportInstruction(
            instruction_id="IFTMIN-002",
            function_code=InstructionFunction.ORIGINAL,
            issue_date="2026-04-15T10:00:00Z",
            parties=InstructionParties(
                shipper=Party(role="shipper", name="ABC Export", identifier="PL1234567890"),
                consignee=Party(role="consignee", name="XYZ Import", identifier="DE987654321"),
            ),
            locations=InstructionLocations(
                port_of_loading=Location(qualifier="place_of_loading", un_locode="PLGDY"),
                port_of_discharge=Location(qualifier="place_of_discharge", un_locode="DEHAM"),
            ),
            transport_stages=[
                TransportStage(stage_number=1, mode="sea", carrier="MAEU", vessel_name="MAERSK EDINBURGH"),
            ],
            goods_lines=[
                GoodsLine(
                    line_number=1,
                    description="Industrial machinery",
                    packages_count=120,
                    package_type="CT",
                    gross_weight=Weight(value=24000.0, unit="KGM"),
                    equipment=Equipment(container_id="MSKU1234567", iso_size_type="22G1"),
                ),
            ],
            delivery_terms=DeliveryTerms.FOB,
        )
        data = instruction.model_dump(mode="json")
        assert data["parties"]["shipper"]["name"] == "ABC Export"
        assert data["locations"]["port_of_loading"]["un_locode"] == "PLGDY"
        assert data["transport_stages"][0]["carrier"] == "MAEU"
        assert data["delivery_terms"] == "FOB"

    def test_transport_instruction_requires_goods_lines(self):
        with pytest.raises(ValueError):
            TransportInstruction(
                instruction_id="IFTMIN-003",
                goods_lines=[],
            )

    def test_goods_line_with_dangerous_goods(self):
        from src.schemas.common import DangerousGoods

        line = GoodsLine(
            line_number=1,
            description="Chemicals",
            dangerous_goods=[DangerousGoods(imdg_class="8", un_number="UN2796")],
        )
        assert len(line.dangerous_goods) == 1

    def test_transport_stage_dates(self):
        stage = TransportStage(
            stage_number=1,
            mode="sea",
            departure_date="2026-04-20T06:00:00Z",
            arrival_date="2026-04-25T14:00:00Z",
            departure_location=Location(qualifier="port", un_locode="PLGDY"),
            arrival_location=Location(qualifier="port", un_locode="DEHAM"),
        )
        assert stage.departure_location.un_locode == "PLGDY"
        assert stage.arrival_location.un_locode == "DEHAM"

    def test_amendment_function(self):
        instruction = TransportInstruction(
            instruction_id="IFTMIN-004",
            function_code=InstructionFunction.AMENDMENT,
            goods_lines=[GoodsLine(line_number=1, description="Updated goods")],
        )
        assert instruction.function_code == InstructionFunction.AMENDMENT


class TestIftminApi:
    def test_create_instruction(self, client):
        response = client.post(
            "/iftmin/instructions",
            json={
                "instruction_id": "IFTMIN-2026-0001",
                "function_code": "original",
                "goods_lines": [
                    {
                        "line_number": 1,
                        "description": "Machine parts",
                        "packages_count": 120,
                        "equipment": {
                            "container_id": "MSKU1234567",
                            "iso_size_type": "22G1",
                        },
                    }
                ],
            },
        )
        assert response.status_code == 201

    def test_list_instructions(self, client):
        response = client.get("/iftmin/instructions?account_name=default")
        assert response.status_code == 200

    def test_get_instruction(self, client):
        response = client.get("/iftmin/instructions/IFTMIN-001?account_name=default")
        assert response.status_code == 200

    def test_cancel_instruction(self, client):
        response = client.delete("/iftmin/instructions/IFTMIN-001?account_name=default")
        assert response.status_code == 200

    def test_create_instruction_invalid_container(self, client):
        response = client.post(
            "/iftmin/instructions",
            json={
                "instruction_id": "IFTMIN-BAD",
                "goods_lines": [
                    {
                        "line_number": 1,
                        "description": "Stuff",
                        "equipment": {"container_id": "BAD"},
                    }
                ],
            },
        )
        assert response.status_code == 422
