"""Pinquark WMS Position DTOs.

Document positions with embedded article and optional article batch.
"""

from decimal import Decimal

from pydantic import BaseModel, Field

from pinquark_common.schemas.wms.article import (
    Article,
    ArticleBatch,
    ArticleImage,
    Provider,
    UnitOfMeasure,
)
from pinquark_common.schemas.wms.attribute import Attribute


class PositionArticle(BaseModel):
    """Inline article within a position.

    When sending positions with an existing article, only erp_id + source
    are required. Full fields are needed when creating a new article inline.
    """

    erp_id: str | None = None
    wms_id: int | None = None
    source: str = "ERP"
    symbol: str = ""
    name: str = ""
    unit: str = ""
    ean: str = ""
    group: str = ""
    type: str = ""
    state: Decimal | None = None
    units_of_measure: list[UnitOfMeasure] = Field(default_factory=list)
    images: list[ArticleImage] = Field(default_factory=list)
    providers: list[Provider] = Field(default_factory=list)
    attributes: list[Attribute] = Field(default_factory=list)

    def to_api_dict(self) -> dict:
        return {
            "erpId": int(self.erp_id) if self.erp_id else 0,
            "wmsId": self.wms_id or 0,
            "source": self.source,
            "symbol": self.symbol,
            "name": self.name,
            "unit": self.unit,
            "ean": self.ean,
            "group": self.group,
            "type": self.type,
            "state": float(self.state) if self.state is not None else None,
            "unitsOfMeasure": [u.to_api_dict() for u in self.units_of_measure],
            "images": [i.to_api_dict() for i in self.images],
            "providers": [p.to_api_dict() for p in self.providers],
            "attributes": [a.to_api_dict() for a in self.attributes],
        }

    @classmethod
    def from_api_dict(cls, data: dict) -> "PositionArticle":
        return cls(
            erp_id=str(data.get("erpId", "")) or None,
            wms_id=data.get("wmsId"),
            source=data.get("source", "ERP"),
            symbol=data.get("symbol", ""),
            name=data.get("name", ""),
            unit=data.get("unit", ""),
            ean=data.get("ean", ""),
            group=data.get("group", ""),
            type=data.get("type", ""),
            state=Decimal(str(data["state"])) if data.get("state") is not None else None,
            units_of_measure=[UnitOfMeasure.from_api_dict(u) for u in data.get("unitsOfMeasure", [])],
            images=[ArticleImage.from_api_dict(i) for i in data.get("images", [])],
            providers=[Provider.from_api_dict(p) for p in data.get("providers", [])],
            attributes=[Attribute.from_api_dict(a) for a in data.get("attributes", [])],
        )

    def to_article(self) -> Article:
        """Promote to a standalone Article."""
        return Article(
            erp_id=self.erp_id,
            wms_id=self.wms_id,
            symbol=self.symbol,
            name=self.name,
            unit=self.unit,
            ean=self.ean,
            group=self.group,
            type=self.type,
            source=self.source,
            state=self.state,
            units_of_measure=self.units_of_measure,
            images=self.images,
            providers=self.providers,
            attributes=self.attributes,
        )


class Position(BaseModel):
    """Single position (line item) within a WMS document."""

    no: int
    quantity: Decimal
    attributes: list[Attribute] = Field(default_factory=list)
    article: PositionArticle
    article_batch: ArticleBatch | None = None
    note: str = ""
    status_symbol: str = ""
    erp_id: str | None = None

    def to_api_dict(self) -> dict:
        result: dict = {
            "no": self.no,
            "quantity": float(self.quantity),
            "attributes": [a.to_api_dict() for a in self.attributes],
            "article": self.article.to_api_dict(),
            "note": self.note,
            "statusSymbol": self.status_symbol,
        }
        if self.article_batch:
            result["articleBatch"] = self.article_batch.to_api_dict()
        if self.erp_id:
            result["erpId"] = int(self.erp_id)
        return result

    @classmethod
    def from_api_dict(cls, data: dict) -> "Position":
        return cls(
            no=data["no"],
            quantity=Decimal(str(data["quantity"])),
            attributes=[Attribute.from_api_dict(a) for a in data.get("attributes", [])],
            article=PositionArticle.from_api_dict(data["article"]),
            article_batch=ArticleBatch.from_api_dict(data["articleBatch"]) if data.get("articleBatch") else None,
            note=data.get("note", ""),
            status_symbol=data.get("statusSymbol", ""),
            erp_id=str(data["erpId"]) if data.get("erpId") else None,
        )


class PositionWrapper(BaseModel):
    """Wrapper for sending positions to a specific document (POST /positions)."""

    document_id: int
    document_source: str = "ERP"
    positions: list[Position] = Field(default_factory=list)

    def to_api_dict(self) -> dict:
        return {
            "documentId": self.document_id,
            "documentSource": self.document_source,
            "positions": [p.to_api_dict() for p in self.positions],
        }

    @classmethod
    def from_api_dict(cls, data: dict) -> "PositionWrapper":
        return cls(
            document_id=data["documentId"],
            document_source=data.get("documentSource", "ERP"),
            positions=[Position.from_api_dict(p) for p in data.get("positions", [])],
        )
