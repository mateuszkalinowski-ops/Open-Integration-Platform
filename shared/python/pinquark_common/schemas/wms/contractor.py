"""Pinquark WMS Contractor DTO.

Represents a customer, supplier, or business partner in the WMS.
"""

from pydantic import BaseModel, Field

from pinquark_common.schemas.wms.address import Address
from pinquark_common.schemas.wms.attribute import Attribute


class Contractor(BaseModel):
    """WMS Contractor (kontrahent)."""

    erp_id: str | None = None
    wms_id: int | None = None
    name: str = ""
    symbol: str = ""
    description: str = ""
    tax_number: str = ""
    email: str = ""
    phone: str = ""
    address: Address | None = None
    addresses: list[Address] = Field(default_factory=list)
    is_supplier: bool = False
    supplier_symbol: str = ""
    attributes: list[Attribute] = Field(default_factory=list)
    source: str = "ERP"

    def to_api_dict(self) -> dict:
        return {
            "erpId": int(self.erp_id) if self.erp_id else 0,
            "wmsId": self.wms_id or 0,
            "name": self.name,
            "symbol": self.symbol,
            "description": self.description,
            "taxNumber": self.tax_number,
            "email": self.email,
            "phone": self.phone,
            "address": self.address.to_api_dict() if self.address else None,
            "addresses": [a.to_api_dict() for a in self.addresses],
            "isSupplier": self.is_supplier,
            "supplierSymbol": self.supplier_symbol,
            "attributes": [a.to_api_dict() for a in self.attributes],
            "source": self.source,
        }

    @classmethod
    def from_api_dict(cls, data: dict) -> "Contractor":
        return cls(
            erp_id=str(data.get("erpId", "")) or None,
            wms_id=data.get("wmsId"),
            name=data.get("name", ""),
            symbol=data.get("symbol", ""),
            description=data.get("description", ""),
            tax_number=data.get("taxNumber", ""),
            email=data.get("email", ""),
            phone=data.get("phone", ""),
            address=Address.from_api_dict(data["address"]) if data.get("address") else None,
            addresses=[Address.from_api_dict(a) for a in data.get("addresses", [])],
            is_supplier=data.get("isSupplier", False),
            supplier_symbol=data.get("supplierSymbol", ""),
            attributes=[Attribute.from_api_dict(a) for a in data.get("attributes", [])],
            source=data.get("source", "ERP"),
        )
