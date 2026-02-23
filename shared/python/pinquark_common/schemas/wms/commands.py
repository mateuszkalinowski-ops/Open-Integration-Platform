"""Pinquark WMS Delete Command DTOs.

Used to request deletion of articles, contractors, documents, and positions.
"""

from pydantic import BaseModel


class DeleteArticleCommand(BaseModel):
    unique_code: str

    def to_api_dict(self) -> dict:
        return {"uniqueCode": self.unique_code}

    @classmethod
    def from_api_dict(cls, data: dict) -> "DeleteArticleCommand":
        return cls(unique_code=data["uniqueCode"])


class DeleteContractorCommand(BaseModel):
    unique_code: str
    source: str = "ERP"

    def to_api_dict(self) -> dict:
        return {"uniqueCode": self.unique_code, "source": self.source}

    @classmethod
    def from_api_dict(cls, data: dict) -> "DeleteContractorCommand":
        return cls(unique_code=data["uniqueCode"], source=data.get("source", "ERP"))


class DeleteDocumentCommand(BaseModel):
    unique_code: str
    source: str = "ERP"

    def to_api_dict(self) -> dict:
        return {"uniqueCode": self.unique_code, "source": self.source}

    @classmethod
    def from_api_dict(cls, data: dict) -> "DeleteDocumentCommand":
        return cls(unique_code=data["uniqueCode"], source=data.get("source", "ERP"))


class DeletePositionCommand(BaseModel):
    unique_code: str
    document_id: int
    source: str = "ERP"

    def to_api_dict(self) -> dict:
        return {
            "uniqueCode": self.unique_code,
            "documentId": self.document_id,
            "source": self.source,
        }

    @classmethod
    def from_api_dict(cls, data: dict) -> "DeletePositionCommand":
        return cls(
            unique_code=data["uniqueCode"],
            document_id=data["documentId"],
            source=data.get("source", "ERP"),
        )
