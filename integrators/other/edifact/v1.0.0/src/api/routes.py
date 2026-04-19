"""FastAPI routes for EDIFACT connector — all message types + raw parse/build."""

import base64
import logging
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from src.api.dependencies import app_state
from src.config import settings
from src.schemas.aperak import AperakMessage, AperakResponse
from src.schemas.baplie import BayPlan, BayPlanFilter, BayPlanResponse, PlanType
from src.schemas.coarri import CoarriMessage, CoarriResponse
from src.schemas.codeco import GateEvent, GateEventFilter, GateEventResponse, GateEventType
from src.schemas.cohaor import CohaorMessage, CohaorResponse
from src.schemas.contrl import ContrlMessage, ContrlResponse
from src.schemas.coparn import CoparnMessage, CoparnResponse
from src.schemas.coprar import CoprarMessage, CoprarResponse
from src.schemas.iftmin import (
    InstructionFunction,
    TransportInstruction,
    TransportInstructionFilter,
    TransportInstructionResponse,
)
from src.schemas.iftsta import IftstaMessage, IftstaResponse
from src.services.edifact_builder import build_edifact
from src.services.edifact_client import EdifactClientError
from src.services.edifact_parser import parse_edifact
from src.validators.edifact_validator import (
    validate_container_number,
    validate_imdg_class,
    validate_un_locode,
    validate_vessel_imo,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def _client_error_to_http(exc: EdifactClientError) -> HTTPException:
    return HTTPException(
        status_code=exc.status_code,
        detail={"error": {"code": "EXTERNAL_SYSTEM_ERROR", "message": exc.message, "details": exc.details}},
    )


def _get_client(account_name: str = "default"):  # type: ignore[no-untyped-def]
    if not app_state.account_manager:
        raise HTTPException(status_code=503, detail="Account manager not initialized")
    try:
        return app_state.account_manager.get_client(account_name)
    except KeyError as err:
        raise HTTPException(status_code=404, detail=f"Account '{account_name}' not found") from err


def _validate_gate_event(event: GateEvent) -> None:
    """Run business-rule validation on a CODECO gate event."""
    for container in event.containers:
        valid, msg = validate_container_number(container.equipment.container_id)
        if not valid:
            raise HTTPException(status_code=422, detail={"error": {"code": "INVALID_CONTAINER_ID", "message": msg}})

        for dg in container.dangerous_goods:
            valid, msg = validate_imdg_class(dg.imdg_class)
            if not valid:
                raise HTTPException(status_code=422, detail={"error": {"code": "INVALID_IMDG_CLASS", "message": msg}})

    for loc in event.locations:
        if loc.un_locode:
            valid, msg = validate_un_locode(loc.un_locode)
            if not valid:
                raise HTTPException(status_code=422, detail={"error": {"code": "INVALID_UN_LOCODE", "message": msg}})

    if event.transport and event.transport.vessel_imo:
        valid, msg = validate_vessel_imo(event.transport.vessel_imo)
        if not valid:
            raise HTTPException(status_code=422, detail={"error": {"code": "INVALID_VESSEL_IMO", "message": msg}})


def _validate_bay_plan(plan: BayPlan) -> None:
    """Run business-rule validation on a BAPLIE bay plan."""
    if plan.vessel.vessel_imo:
        valid, msg = validate_vessel_imo(plan.vessel.vessel_imo)
        if not valid:
            raise HTTPException(status_code=422, detail={"error": {"code": "INVALID_VESSEL_IMO", "message": msg}})

    for loc in plan.locations:
        if loc.equipment and loc.equipment.equipment:
            valid, msg = validate_container_number(loc.equipment.equipment.container_id)
            if not valid:
                raise HTTPException(status_code=422, detail={"error": {"code": "INVALID_CONTAINER_ID", "message": msg}})

    for port in plan.ports_of_call:
        if port.un_locode:
            valid, msg = validate_un_locode(port.un_locode)
            if not valid:
                raise HTTPException(status_code=422, detail={"error": {"code": "INVALID_UN_LOCODE", "message": msg}})


def _validate_instruction(instruction: TransportInstruction) -> None:
    """Run business-rule validation on an IFTMIN transport instruction."""
    for line in instruction.goods_lines:
        if line.equipment:
            valid, msg = validate_container_number(line.equipment.container_id)
            if not valid:
                raise HTTPException(status_code=422, detail={"error": {"code": "INVALID_CONTAINER_ID", "message": msg}})

        for dg in line.dangerous_goods:
            valid, msg = validate_imdg_class(dg.imdg_class)
            if not valid:
                raise HTTPException(status_code=422, detail={"error": {"code": "INVALID_IMDG_CLASS", "message": msg}})


# =============================================================================
# Health & readiness
# =============================================================================


@router.get("/health")
async def health() -> dict[str, Any]:
    if app_state.health_checker:
        result = await app_state.health_checker.run()
        return result.model_dump() if hasattr(result, "model_dump") else result
    return {"status": "healthy", "version": settings.app_version}


@router.get("/readiness")
async def readiness() -> dict[str, Any]:
    if app_state.health_checker:
        result = await app_state.health_checker.run()
        data = result.model_dump() if hasattr(result, "model_dump") else result
        status = result.status if hasattr(result, "status") else data.get("status")
        if status != "healthy":
            raise HTTPException(status_code=503, detail=data)
        return data
    return {"status": "ready", "version": settings.app_version}


# =============================================================================
# Account management
# =============================================================================


class AccountCreateRequest(BaseModel):
    name: str
    base_url: str = ""
    api_key: str = ""
    description: str = ""


@router.get("/accounts")
async def list_accounts() -> list[dict[str, Any]]:
    if not app_state.account_manager:
        return []
    return app_state.account_manager.list_accounts()


@router.post("/accounts", status_code=201)
async def create_account(req: AccountCreateRequest) -> dict[str, str]:
    if not app_state.account_manager:
        raise HTTPException(status_code=503, detail="Account manager not initialized")
    app_state.account_manager.add_account(req.model_dump())
    return {"status": "created", "account": req.name}


@router.delete("/accounts/{account_name}")
async def delete_account(account_name: str) -> dict[str, str]:
    if not app_state.account_manager:
        raise HTTPException(status_code=503, detail="Account manager not initialized")
    try:
        app_state.account_manager.remove_account(account_name)
    except KeyError as err:
        raise HTTPException(status_code=404, detail=f"Account '{account_name}' not found") from err
    return {"status": "deleted", "account": account_name}


# =============================================================================
# Connection validation
# =============================================================================


@router.post("/validate-connection")
async def validate_connection(account_name: str = Query("default")) -> dict[str, Any]:
    client = _get_client(account_name)
    result = await client.check_health()
    if result["status"] != "healthy":
        raise HTTPException(status_code=502, detail={"status": "unreachable", "error": result.get("error")})
    return {"status": "connected", "account": account_name}


# =============================================================================
# CODECO — Container gate-in/gate-out
# =============================================================================


@router.post("/codeco/gate-events", status_code=201, response_model=GateEventResponse)
async def create_gate_event(event: GateEvent) -> Any:
    _validate_gate_event(event)
    client = _get_client(event.account_name)
    try:
        result = await client.create_gate_event(event.model_dump(mode="json"))
        return result
    except EdifactClientError as exc:
        raise _client_error_to_http(exc) from exc


@router.get("/codeco/gate-events")
async def list_gate_events(
    account_name: str = Query("default"),
    event_type: GateEventType | None = None,
    container_id: str | None = None,
    vessel_name: str | None = None,
    un_locode: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
) -> Any:
    client = _get_client(account_name)
    params = GateEventFilter(
        event_type=event_type,
        container_id=container_id,
        vessel_name=vessel_name,
        un_locode=un_locode,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )
    try:
        return await client.list_gate_events(params.model_dump(exclude_none=True, mode="json"))
    except EdifactClientError as exc:
        raise _client_error_to_http(exc) from exc


@router.get("/codeco/gate-events/{event_id}")
async def get_gate_event(event_id: str, account_name: str = Query("default")) -> Any:
    client = _get_client(account_name)
    try:
        return await client.get_gate_event(event_id)
    except EdifactClientError as exc:
        raise _client_error_to_http(exc) from exc


@router.put("/codeco/gate-events/{event_id}", response_model=GateEventResponse)
async def update_gate_event(event_id: str, event: GateEvent) -> Any:
    _validate_gate_event(event)
    client = _get_client(event.account_name)
    try:
        return await client.update_gate_event(event_id, event.model_dump(mode="json"))
    except EdifactClientError as exc:
        raise _client_error_to_http(exc) from exc


@router.delete("/codeco/gate-events/{event_id}")
async def cancel_gate_event(event_id: str, account_name: str = Query("default")) -> Any:
    client = _get_client(account_name)
    try:
        return await client.cancel_gate_event(event_id)
    except EdifactClientError as exc:
        raise _client_error_to_http(exc) from exc


# =============================================================================
# BAPLIE — Bay plan / stowage
# =============================================================================


@router.post("/baplie/bay-plans", status_code=201, response_model=BayPlanResponse)
async def create_bay_plan(plan: BayPlan) -> Any:
    _validate_bay_plan(plan)
    client = _get_client(plan.account_name)
    try:
        return await client.create_bay_plan(plan.model_dump(mode="json"))
    except EdifactClientError as exc:
        raise _client_error_to_http(exc) from exc


@router.get("/baplie/bay-plans")
async def list_bay_plans(
    account_name: str = Query("default"),
    vessel_imo: str | None = None,
    vessel_name: str | None = None,
    voyage_number: str | None = None,
    plan_type: PlanType | None = None,
    port_un_locode: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
) -> Any:
    client = _get_client(account_name)
    params = BayPlanFilter(
        vessel_imo=vessel_imo,
        vessel_name=vessel_name,
        voyage_number=voyage_number,
        plan_type=plan_type,
        port_un_locode=port_un_locode,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )
    try:
        return await client.list_bay_plans(params.model_dump(exclude_none=True, mode="json"))
    except EdifactClientError as exc:
        raise _client_error_to_http(exc) from exc


@router.get("/baplie/bay-plans/{plan_id}")
async def get_bay_plan(plan_id: str, account_name: str = Query("default")) -> Any:
    client = _get_client(account_name)
    try:
        return await client.get_bay_plan(plan_id)
    except EdifactClientError as exc:
        raise _client_error_to_http(exc) from exc


@router.put("/baplie/bay-plans/{plan_id}", response_model=BayPlanResponse)
async def update_bay_plan(plan_id: str, plan: BayPlan) -> Any:
    _validate_bay_plan(plan)
    client = _get_client(plan.account_name)
    try:
        return await client.update_bay_plan(plan_id, plan.model_dump(mode="json"))
    except EdifactClientError as exc:
        raise _client_error_to_http(exc) from exc


@router.get("/baplie/bay-plans/{plan_id}/locations")
async def get_bay_plan_locations(
    plan_id: str,
    account_name: str = Query("default"),
    bay: str | None = None,
    row: str | None = None,
    tier: str | None = None,
    is_empty: bool | None = None,
) -> Any:
    client = _get_client(account_name)
    params: dict[str, Any] = {}
    if bay:
        params["bay"] = bay
    if row:
        params["row"] = row
    if tier:
        params["tier"] = tier
    if is_empty is not None:
        params["is_empty"] = is_empty
    try:
        return await client.get_bay_plan_locations(plan_id, params or None)
    except EdifactClientError as exc:
        raise _client_error_to_http(exc) from exc


# =============================================================================
# IFTMIN — Transport instructions
# =============================================================================


@router.post("/iftmin/instructions", status_code=201, response_model=TransportInstructionResponse)
async def create_instruction(instruction: TransportInstruction) -> Any:
    _validate_instruction(instruction)
    client = _get_client(instruction.account_name)
    try:
        return await client.create_instruction(instruction.model_dump(mode="json"))
    except EdifactClientError as exc:
        raise _client_error_to_http(exc) from exc


@router.get("/iftmin/instructions")
async def list_instructions(
    account_name: str = Query("default"),
    shipper_id: str | None = None,
    consignee_id: str | None = None,
    port_of_loading: str | None = None,
    port_of_discharge: str | None = None,
    vessel_name: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    function_code: InstructionFunction | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
) -> Any:
    client = _get_client(account_name)
    params = TransportInstructionFilter(
        shipper_id=shipper_id,
        consignee_id=consignee_id,
        port_of_loading=port_of_loading,
        port_of_discharge=port_of_discharge,
        vessel_name=vessel_name,
        date_from=date_from,
        date_to=date_to,
        function_code=function_code,
        page=page,
        page_size=page_size,
    )
    try:
        return await client.list_instructions(params.model_dump(exclude_none=True, mode="json"))
    except EdifactClientError as exc:
        raise _client_error_to_http(exc) from exc


@router.get("/iftmin/instructions/{instruction_id}")
async def get_instruction(instruction_id: str, account_name: str = Query("default")) -> Any:
    client = _get_client(account_name)
    try:
        return await client.get_instruction(instruction_id)
    except EdifactClientError as exc:
        raise _client_error_to_http(exc) from exc


@router.put("/iftmin/instructions/{instruction_id}", response_model=TransportInstructionResponse)
async def amend_instruction(instruction_id: str, instruction: TransportInstruction) -> Any:
    _validate_instruction(instruction)
    client = _get_client(instruction.account_name)
    try:
        return await client.amend_instruction(instruction_id, instruction.model_dump(mode="json"))
    except EdifactClientError as exc:
        raise _client_error_to_http(exc) from exc


@router.delete("/iftmin/instructions/{instruction_id}")
async def cancel_instruction(instruction_id: str, account_name: str = Query("default")) -> Any:
    client = _get_client(account_name)
    try:
        return await client.cancel_instruction(instruction_id)
    except EdifactClientError as exc:
        raise _client_error_to_http(exc) from exc


# =============================================================================
# COPRAR — Container Pre-Advice (rail)
# =============================================================================


@router.post("/coprar/pre-advice", status_code=201, response_model=CoprarResponse)
async def create_coprar(msg: CoprarMessage) -> Any:
    for wg in msg.wagons:
        for c in wg.containers:
            valid, err = validate_container_number(c.container_no)
            if not valid:
                raise HTTPException(status_code=422, detail={"error": {"code": "INVALID_CONTAINER_ID", "message": err}})
    return CoprarResponse(
        id=str(uuid.uuid4()),
        document_id=msg.document_id,
        function_code=msg.function_code.value,
        wagons_count=len(msg.wagons),
        containers_count=sum(len(wg.containers) for wg in msg.wagons),
        status="accepted",
    )


@router.get("/coprar/pre-advice")
async def list_coprar(
    account_name: str = Query("default"),
    function_code: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
) -> dict[str, Any]:
    return {"items": [], "total": 0, "page": page, "page_size": page_size}


@router.get("/coprar/pre-advice/{message_id}")
async def get_coprar(message_id: str, account_name: str = Query("default")) -> dict[str, Any]:
    raise HTTPException(status_code=404, detail=f"COPRAR '{message_id}' not found")


# =============================================================================
# COPARN — Container Release / Reservation Order
# =============================================================================


@router.post("/coparn/release-orders", status_code=201, response_model=CoparnResponse)
async def create_coparn(msg: CoparnMessage) -> Any:
    if msg.container_no:
        valid, err = validate_container_number(msg.container_no)
        if not valid:
            raise HTTPException(status_code=422, detail={"error": {"code": "INVALID_CONTAINER_ID", "message": err}})
    return CoparnResponse(
        id=str(uuid.uuid4()),
        document_id=msg.document_id,
        operation_type=msg.operation_type,
        container_no=msg.container_no or "",
        status="accepted",
    )


@router.get("/coparn/release-orders")
async def list_coparn(
    account_name: str = Query("default"),
    operation_type: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
) -> dict[str, Any]:
    return {"items": [], "total": 0, "page": page, "page_size": page_size}


@router.get("/coparn/release-orders/{message_id}")
async def get_coparn(message_id: str, account_name: str = Query("default")) -> dict[str, Any]:
    raise HTTPException(status_code=404, detail=f"COPARN '{message_id}' not found")


# =============================================================================
# COHAOR — Container Special Handling Order
# =============================================================================


@router.post("/cohaor/handling-orders", status_code=201, response_model=CohaorResponse)
async def create_cohaor(msg: CohaorMessage) -> Any:
    if msg.container_no:
        valid, err = validate_container_number(msg.container_no)
        if not valid:
            raise HTTPException(status_code=422, detail={"error": {"code": "INVALID_CONTAINER_ID", "message": err}})
    return CohaorResponse(
        id=str(uuid.uuid4()),
        document_id=msg.document_id,
        function_code=msg.function_code.value,
        operation_code=msg.operation_code,
        container_no=msg.container_no,
        status="accepted",
    )


@router.get("/cohaor/handling-orders")
async def list_cohaor(
    account_name: str = Query("default"),
    operation_code: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
) -> dict[str, Any]:
    return {"items": [], "total": 0, "page": page, "page_size": page_size}


@router.get("/cohaor/handling-orders/{message_id}")
async def get_cohaor(message_id: str, account_name: str = Query("default")) -> dict[str, Any]:
    raise HTTPException(status_code=404, detail=f"COHAOR '{message_id}' not found")


# =============================================================================
# COARRI — Container Discharge/Loading Report
# =============================================================================


@router.post("/coarri/reports", status_code=201, response_model=CoarriResponse)
async def create_coarri(msg: CoarriMessage) -> Any:
    for c in msg.containers:
        valid, err = validate_container_number(c.container_no)
        if not valid:
            raise HTTPException(status_code=422, detail={"error": {"code": "INVALID_CONTAINER_ID", "message": err}})
    return CoarriResponse(
        id=str(uuid.uuid4()),
        document_id=msg.document_id,
        report_type=msg.report_type,
        total_containers=len(msg.containers),
        status="accepted",
    )


@router.get("/coarri/reports")
async def list_coarri(
    account_name: str = Query("default"),
    report_type: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
) -> dict[str, Any]:
    return {"items": [], "total": 0, "page": page, "page_size": page_size}


@router.get("/coarri/reports/{message_id}")
async def get_coarri(message_id: str, account_name: str = Query("default")) -> dict[str, Any]:
    raise HTTPException(status_code=404, detail=f"COARRI '{message_id}' not found")


# =============================================================================
# IFTSTA — Multimodal Status Report
# =============================================================================


@router.post("/iftsta/status-reports", status_code=201, response_model=IftstaResponse)
async def create_iftsta(msg: IftstaMessage) -> Any:
    if msg.container_no:
        valid, err = validate_container_number(msg.container_no)
        if not valid:
            raise HTTPException(status_code=422, detail={"error": {"code": "INVALID_CONTAINER_ID", "message": err}})
    return IftstaResponse(
        id=str(uuid.uuid4()),
        document_id=msg.document_id,
        status_code=msg.status_code,
        status="accepted",
    )


@router.get("/iftsta/status-reports")
async def list_iftsta(
    account_name: str = Query("default"),
    status_code: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
) -> dict[str, Any]:
    return {"items": [], "total": 0, "page": page, "page_size": page_size}


@router.get("/iftsta/status-reports/{message_id}")
async def get_iftsta(message_id: str, account_name: str = Query("default")) -> dict[str, Any]:
    raise HTTPException(status_code=404, detail=f"IFTSTA '{message_id}' not found")


# =============================================================================
# APERAK — Application Error and Acknowledgement
# =============================================================================


@router.post("/aperak/acknowledgements", status_code=201, response_model=AperakResponse)
async def send_aperak(msg: AperakMessage) -> Any:
    try:
        raw = build_edifact(
            msg_type="APERAK",
            version="D:01B",
            sender_id="OIP",
            receiver_id="PARTNER",
            payload=msg.model_dump(mode="json"),
        )
        content_b64 = base64.b64encode(raw.encode()).decode()
    except Exception:
        content_b64 = ""

    return AperakResponse(
        id=str(uuid.uuid4()),
        document_id=msg.document_id,
        response_type=msg.response_type,
        referenced_message_ref=msg.referenced_message_ref,
        content_base64=content_b64,
    )


@router.get("/aperak/acknowledgements")
async def list_aperak(
    account_name: str = Query("default"),
    response_type: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
) -> dict[str, Any]:
    return {"items": [], "total": 0, "page": page, "page_size": page_size}


# =============================================================================
# CONTRL — Syntax Acknowledgement
# =============================================================================


@router.post("/contrl/syntax-ack", status_code=201, response_model=ContrlResponse)
async def send_contrl(msg: ContrlMessage) -> Any:
    try:
        raw = build_edifact(
            msg_type="CONTRL",
            version="D:01B",
            sender_id=msg.sender_id or "OIP",
            receiver_id=msg.receiver_id or "PARTNER",
            payload=msg.model_dump(mode="json"),
        )
        content_b64 = base64.b64encode(raw.encode()).decode()
    except Exception:
        content_b64 = ""

    return ContrlResponse(
        id=str(uuid.uuid4()),
        syntax_status=msg.syntax_status,
        referenced_interchange_ref=msg.referenced_interchange_ref,
        content_base64=content_b64,
        status="sent",
    )


@router.get("/contrl/syntax-ack")
async def list_contrl(
    account_name: str = Query("default"),
    syntax_status: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
) -> dict[str, Any]:
    return {"items": [], "total": 0, "page": page, "page_size": page_size}


# =============================================================================
# Raw EDIFACT parse / build
# =============================================================================


class EdifactParseRequest(BaseModel):
    content: str


class EdifactBuildRequest(BaseModel):
    msg_type: str
    sender_id: str
    receiver_id: str
    body: dict[str, Any]
    version: str = "D:01B"


@router.post("/edifact/parse")
async def edifact_parse(req: EdifactParseRequest) -> dict[str, Any]:
    try:
        result = parse_edifact(req.content)
        return {"status": "ok", "parsed": result}
    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail={"error": {"code": "PARSE_ERROR", "message": str(exc)}},
        ) from exc


@router.post("/edifact/build")
async def edifact_build(req: EdifactBuildRequest) -> dict[str, Any]:
    try:
        raw = build_edifact(
            msg_type=req.msg_type,
            sender_id=req.sender_id,
            receiver_id=req.receiver_id,
            payload=req.body,
            version=req.version,
        )
        return {
            "status": "ok",
            "content": raw,
            "content_base64": base64.b64encode(raw.encode()).decode(),
        }
    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail={"error": {"code": "BUILD_ERROR", "message": str(exc)}},
        ) from exc
