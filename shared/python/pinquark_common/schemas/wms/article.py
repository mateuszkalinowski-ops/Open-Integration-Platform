"""Pinquark WMS Article DTOs.

Covers: Article, ArticleImage, UnitOfMeasure, Provider, ArticleBatch.
Matches the Pinquark Integration REST API specification.
"""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from pinquark_common.schemas.wms.attribute import Attribute


class ArticleImage(BaseModel):
    path: str = ""
    is_default: bool = False
    created_date: datetime | None = None

    def to_api_dict(self) -> dict:
        return {
            "path": self.path,
            "default": self.is_default,
            "createdDate": self.created_date.isoformat() if self.created_date else None,
        }

    @classmethod
    def from_api_dict(cls, data: dict) -> "ArticleImage":
        return cls(
            path=data.get("path", ""),
            is_default=data.get("default", False),
            created_date=datetime.fromisoformat(data["createdDate"]) if data.get("createdDate") else None,
        )


class UnitOfMeasure(BaseModel):
    unit: str = ""
    eans: list[str] = Field(default_factory=list)
    length: Decimal | None = None
    width: Decimal | None = None
    height: Decimal | None = None
    weight: Decimal | None = None
    converter_to_main_unit: Decimal | None = None
    is_default: bool = False

    def to_api_dict(self) -> dict:
        def _dec(v: Decimal | None) -> float | None:
            return float(v) if v is not None else None

        return {
            "unit": self.unit,
            "eans": self.eans,
            "length": _dec(self.length),
            "width": _dec(self.width),
            "height": _dec(self.height),
            "weight": _dec(self.weight),
            "converterToMainUnit": _dec(self.converter_to_main_unit),
            "default": self.is_default,
        }

    @classmethod
    def from_api_dict(cls, data: dict) -> "UnitOfMeasure":
        def _dec(v: float | int | None) -> Decimal | None:
            return Decimal(str(v)) if v is not None else None

        return cls(
            unit=data.get("unit", ""),
            eans=data.get("eans", []),
            length=_dec(data.get("length")),
            width=_dec(data.get("width")),
            height=_dec(data.get("height")),
            weight=_dec(data.get("weight")),
            converter_to_main_unit=_dec(data.get("converterToMainUnit")),
            is_default=data.get("default", False),
        )


class Provider(BaseModel):
    contractor_id: str | None = None
    contractor_source: str = "ERP"
    symbol: str = ""
    code: str = ""
    ean_code: str = ""
    name: str = ""
    unit: str = ""
    created_date: datetime | None = None

    def to_api_dict(self) -> dict:
        return {
            "contractorId": int(self.contractor_id) if self.contractor_id else 0,
            "contractorSource": self.contractor_source,
            "symbol": self.symbol,
            "code": self.code,
            "eanCode": self.ean_code,
            "name": self.name,
            "unit": self.unit,
            "createdDate": self.created_date.isoformat() if self.created_date else None,
        }

    @classmethod
    def from_api_dict(cls, data: dict) -> "Provider":
        return cls(
            contractor_id=str(data.get("contractorId", "")) or None,
            contractor_source=data.get("contractorSource", "ERP"),
            symbol=data.get("symbol", ""),
            code=data.get("code", ""),
            ean_code=data.get("eanCode", ""),
            name=data.get("name", ""),
            unit=data.get("unit", ""),
            created_date=datetime.fromisoformat(data["createdDate"]) if data.get("createdDate") else None,
        )


class Article(BaseModel):
    """WMS Article (towar/artykul)."""

    erp_id: str | None = None
    wms_id: int | None = None
    symbol: str = ""
    name: str = ""
    unit: str = ""
    units_of_measure: list[UnitOfMeasure] = Field(default_factory=list)
    ean: str = ""
    group: str = ""
    type: str = ""
    source: str = "ERP"
    images: list[ArticleImage] = Field(default_factory=list)
    providers: list[Provider] = Field(default_factory=list)
    attributes: list[Attribute] = Field(default_factory=list)
    state: Decimal | None = None

    def to_api_dict(self) -> dict:
        return {
            "erpId": int(self.erp_id) if self.erp_id else 0,
            "wmsId": self.wms_id or 0,
            "symbol": self.symbol,
            "name": self.name,
            "unit": self.unit,
            "unitsOfMeasure": [u.to_api_dict() for u in self.units_of_measure],
            "ean": self.ean,
            "group": self.group,
            "type": self.type,
            "source": self.source,
            "images": [i.to_api_dict() for i in self.images],
            "providers": [p.to_api_dict() for p in self.providers],
            "attributes": [a.to_api_dict() for a in self.attributes],
            "state": float(self.state) if self.state is not None else None,
        }

    @classmethod
    def from_api_dict(cls, data: dict) -> "Article":
        return cls(
            erp_id=str(data.get("erpId", "")) or None,
            wms_id=data.get("wmsId"),
            symbol=data.get("symbol", ""),
            name=data.get("name", ""),
            unit=data.get("unit", ""),
            units_of_measure=[UnitOfMeasure.from_api_dict(u) for u in data.get("unitsOfMeasure", [])],
            ean=data.get("ean", ""),
            group=data.get("group", ""),
            type=data.get("type", ""),
            source=data.get("source", "ERP"),
            images=[ArticleImage.from_api_dict(i) for i in data.get("images", [])],
            providers=[Provider.from_api_dict(p) for p in data.get("providers", [])],
            attributes=[Attribute.from_api_dict(a) for a in data.get("attributes", [])],
            state=Decimal(str(data["state"])) if data.get("state") is not None else None,
        )


class ArticleBatch(BaseModel):
    """WMS Article Batch (partia artykulu)."""

    batch_number: str = ""
    ean_code: str = ""
    erp_article_id: str | None = None
    batch_owner: str = ""
    batch_owner_id: int | None = None
    term_validity: date | None = None
    attributes: list[Attribute] = Field(default_factory=list)

    def to_api_dict(self) -> dict:
        return {
            "batchNumber": self.batch_number,
            "eanCode": self.ean_code,
            "erpArticleId": int(self.erp_article_id) if self.erp_article_id else 0,
            "batchOwner": self.batch_owner,
            "batchOwnerId": self.batch_owner_id or 0,
            "termValidity": self.term_validity.isoformat() if self.term_validity else None,
            "attributes": [a.to_api_dict() for a in self.attributes],
        }

    @classmethod
    def from_api_dict(cls, data: dict) -> "ArticleBatch":
        return cls(
            batch_number=data.get("batchNumber", ""),
            ean_code=data.get("eanCode", ""),
            erp_article_id=str(data.get("erpArticleId", "")) or None,
            batch_owner=data.get("batchOwner", ""),
            batch_owner_id=data.get("batchOwnerId"),
            term_validity=date.fromisoformat(data["termValidity"]) if data.get("termValidity") else None,
            attributes=[Attribute.from_api_dict(a) for a in data.get("attributes", [])],
        )
