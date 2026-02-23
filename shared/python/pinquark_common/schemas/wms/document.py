"""Pinquark WMS Document DTO.

The central entity for warehouse operations: incoming goods (PZ),
outgoing goods (WZ), orders (ZK), internal transfers (MM), etc.
"""

from __future__ import annotations

import datetime as _dt

from pydantic import BaseModel, Field

from pinquark_common.schemas.wms.address import Address
from pinquark_common.schemas.wms.attribute import Attribute
from pinquark_common.schemas.wms.contact import Contact
from pinquark_common.schemas.wms.contractor import Contractor
from pinquark_common.schemas.wms.position import Position


class Document(BaseModel):
    """WMS Document (dokument magazynowy)."""

    erp_code: str = ""
    erp_id: str | None = None
    wms_id: int | None = None
    document_type: str = ""
    warehouse_symbol: str = ""
    delivery_method_symbol: str = ""
    recipient_id: str | None = None
    recipient_source: str = "ERP"
    delivery_address: Address | None = None
    additional_courier_info: str = ""
    commission_symbol: str = ""
    input_document_number: str = ""
    own_code: str = ""
    route: str = ""
    contact: Contact | None = None
    erp_status_symbol: str = ""
    date: _dt.date | None = None
    due_date: _dt.date | None = None
    note: str = ""
    symbol: str = ""
    contractor: Contractor | None = None
    attributes: list[Attribute] = Field(default_factory=list)
    positions: list[Position] = Field(default_factory=list)
    procedures: list[str] = Field(default_factory=list)
    priority: int | None = None
    order_type: str = ""
    connect_zk: bool = False
    delete_all_positions: bool = False
    positions_changed: bool = False
    is_new: bool = False
    source: str = "ERP"
    wms_connect_document_symbol: str = ""

    def to_api_dict(self) -> dict:
        return {
            "erpCode": self.erp_code,
            "erpId": int(self.erp_id) if self.erp_id else 0,
            "wmsId": self.wms_id or 0,
            "documentType": self.document_type,
            "warehouseSymbol": self.warehouse_symbol,
            "deliveryMethodSymbol": self.delivery_method_symbol,
            "recipientId": int(self.recipient_id) if self.recipient_id else 0,
            "recipientSource": self.recipient_source,
            "deliveryAddress": self.delivery_address.to_api_dict() if self.delivery_address else None,
            "additionalCourierInfo": self.additional_courier_info,
            "commissionSymbol": self.commission_symbol,
            "inputDocumentNumber": self.input_document_number,
            "ownCode": self.own_code,
            "route": self.route,
            "contact": self.contact.to_api_dict() if self.contact else None,
            "erpStatusSymbol": self.erp_status_symbol,
            "date": self.date.isoformat() if self.date else None,
            "dueDate": self.due_date.isoformat() if self.due_date else None,
            "note": self.note,
            "symbol": self.symbol,
            "contractor": self.contractor.to_api_dict() if self.contractor else None,
            "attributes": [a.to_api_dict() for a in self.attributes],
            "positions": [p.to_api_dict() for p in self.positions],
            "procedures": self.procedures,
            "priority": self.priority,
            "orderType": self.order_type,
            "connectZK": self.connect_zk,
            "deleteAllPositions": self.delete_all_positions,
            "positionsChanged": self.positions_changed,
            "new": self.is_new,
            "source": self.source,
            "wmsConnectDocumentSymbol": self.wms_connect_document_symbol,
        }

    @classmethod
    def from_api_dict(cls, data: dict) -> "Document":
        return cls(
            erp_code=data.get("erpCode", ""),
            erp_id=str(data.get("erpId", "")) or None,
            wms_id=data.get("wmsId"),
            document_type=data.get("documentType", ""),
            warehouse_symbol=data.get("warehouseSymbol", ""),
            delivery_method_symbol=data.get("deliveryMethodSymbol", ""),
            recipient_id=str(data.get("recipientId", "")) or None,
            recipient_source=data.get("recipientSource", "ERP"),
            delivery_address=Address.from_api_dict(data["deliveryAddress"]) if data.get("deliveryAddress") else None,
            additional_courier_info=data.get("additionalCourierInfo", ""),
            commission_symbol=data.get("commissionSymbol", ""),
            input_document_number=data.get("inputDocumentNumber", ""),
            own_code=data.get("ownCode", ""),
            route=data.get("route", ""),
            contact=Contact.from_api_dict(data["contact"]) if data.get("contact") else None,
            erp_status_symbol=data.get("erpStatusSymbol", ""),
            date=_dt.date.fromisoformat(data["date"]) if data.get("date") else None,
            due_date=_dt.date.fromisoformat(data["dueDate"]) if data.get("dueDate") else None,
            note=data.get("note", ""),
            symbol=data.get("symbol", ""),
            contractor=Contractor.from_api_dict(data["contractor"]) if data.get("contractor") else None,
            attributes=[Attribute.from_api_dict(a) for a in data.get("attributes", [])],
            positions=[Position.from_api_dict(p) for p in data.get("positions", [])],
            procedures=data.get("procedures", []),
            priority=data.get("priority"),
            order_type=data.get("orderType", ""),
            connect_zk=data.get("connectZK", False),
            delete_all_positions=data.get("deleteAllPositions", False),
            positions_changed=data.get("positionsChanged", False),
            is_new=data.get("new", False),
            source=data.get("source", "ERP"),
            wms_connect_document_symbol=data.get("wmsConnectDocumentSymbol", ""),
        )


class DocumentsWrapper(BaseModel):
    """Wrapper for batch document creation (POST /documents/wrappers).

    When continue_on_fail is True, valid documents are saved even if
    some fail validation. When False, all are rolled back on any error.
    """

    documents: list[Document] = Field(default_factory=list)
    continue_on_fail: bool = True

    def to_api_dict(self) -> dict:
        return {
            "continueOnFail": self.continue_on_fail,
            "documents": [d.to_api_dict() for d in self.documents],
        }

    @classmethod
    def from_api_dict(cls, data: dict) -> "DocumentsWrapper":
        return cls(
            continue_on_fail=data.get("continueOnFail", True),
            documents=[Document.from_api_dict(d) for d in data.get("documents", [])],
        )
