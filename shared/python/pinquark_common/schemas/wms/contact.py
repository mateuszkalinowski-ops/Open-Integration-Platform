"""Pinquark WMS Contact DTO.

Used in documents to represent contact information.
"""

from pydantic import BaseModel


class Contact(BaseModel):
    """Contact information embedded in a Document."""

    contractor_id: str | None = None
    contractor_source: str = "ERP"
    name: str = ""
    description: str = ""
    email: str = ""
    email_alternative: str = ""
    phone: str = ""
    phone_alternative: str = ""
    www: str = ""
    fax: str = ""
    internet_messenger_1: str = ""
    internet_messenger_2: str = ""
    internet_messenger_3: str = ""

    def to_api_dict(self) -> dict:
        """Serialize to Pinquark REST API format (camelCase)."""
        return {
            "contractorId": int(self.contractor_id) if self.contractor_id else 0,
            "contractorSource": self.contractor_source,
            "name": self.name,
            "description": self.description,
            "email": self.email,
            "emailAlternative": self.email_alternative,
            "phone": self.phone,
            "phoneAlternative": self.phone_alternative,
            "www": self.www,
            "fax": self.fax,
            "internetMessenger1": self.internet_messenger_1,
            "internetMessenger2": self.internet_messenger_2,
            "internetMessenger3": self.internet_messenger_3,
        }

    @classmethod
    def from_api_dict(cls, data: dict) -> "Contact":
        """Deserialize from Pinquark REST API format (camelCase)."""
        return cls(
            contractor_id=str(data.get("contractorId", "")) or None,
            contractor_source=data.get("contractorSource", "ERP"),
            name=data.get("name", ""),
            description=data.get("description", ""),
            email=data.get("email", ""),
            email_alternative=data.get("emailAlternative", ""),
            phone=data.get("phone", ""),
            phone_alternative=data.get("phoneAlternative", ""),
            www=data.get("www", ""),
            fax=data.get("fax", ""),
            internet_messenger_1=data.get("internetMessenger1", ""),
            internet_messenger_2=data.get("internetMessenger2", ""),
            internet_messenger_3=data.get("internetMessenger3", ""),
        )
