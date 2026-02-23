"""Pinquark WMS Address DTO.

Used in contractors, documents (deliveryAddress), and other entities.
"""

from datetime import date

from pydantic import BaseModel


class Address(BaseModel):
    """WMS address structure as defined in the Pinquark Integration REST API."""

    contractor_id: str | None = None
    contractor_source: str = "ERP"
    name: str = ""
    description: str = ""
    city: str = ""
    code: str = ""
    street: str = ""
    country: str = ""
    province: str = ""
    county: str = ""
    commune: str = ""
    district: str = ""
    post_city: str = ""
    house_no: str = ""
    apartment_no: str = ""
    date_from: date | None = None
    date_to: date | None = None
    active: bool = True

    def to_api_dict(self) -> dict:
        """Serialize to Pinquark REST API format (camelCase)."""
        return {
            "contractorId": int(self.contractor_id) if self.contractor_id else 0,
            "contractorSource": self.contractor_source,
            "name": self.name,
            "description": self.description,
            "city": self.city,
            "code": self.code,
            "street": self.street,
            "country": self.country,
            "province": self.province,
            "county": self.county,
            "commune": self.commune,
            "district": self.district,
            "postCity": self.post_city,
            "houseNo": self.house_no,
            "apartmentNo": self.apartment_no,
            "dateFrom": self.date_from.isoformat() if self.date_from else None,
            "dateTo": self.date_to.isoformat() if self.date_to else None,
            "active": self.active,
        }

    @classmethod
    def from_api_dict(cls, data: dict) -> "Address":
        """Deserialize from Pinquark REST API format (camelCase)."""
        return cls(
            contractor_id=str(data.get("contractorId", "")) or None,
            contractor_source=data.get("contractorSource", "ERP"),
            name=data.get("name", ""),
            description=data.get("description", ""),
            city=data.get("city", ""),
            code=data.get("code", ""),
            street=data.get("street", ""),
            country=data.get("country", ""),
            province=data.get("province", ""),
            county=data.get("county", ""),
            commune=data.get("commune", ""),
            district=data.get("district", ""),
            post_city=data.get("postCity", ""),
            house_no=data.get("houseNo", ""),
            apartment_no=data.get("apartmentNo", ""),
            date_from=date.fromisoformat(data["dateFrom"]) if data.get("dateFrom") else None,
            date_to=date.fromisoformat(data["dateTo"]) if data.get("dateTo") else None,
            active=data.get("active", True),
        )
