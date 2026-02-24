"""DHL Express — Pydantic request/response schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Shared address / party schemas
# ---------------------------------------------------------------------------

class Address(BaseModel):
    street_line1: str = Field(..., alias="streetLine1", max_length=45)
    street_line2: str = Field("", alias="streetLine2", max_length=45)
    street_line3: str = Field("", alias="streetLine3", max_length=45)
    city: str = Field(..., max_length=45)
    postal_code: str = Field("", alias="postalCode", max_length=12)
    province_code: str = Field("", alias="provinceCode", max_length=35)
    country_code: str = Field(..., alias="countryCode", min_length=2, max_length=2)

    model_config = {"populate_by_name": True}


class Contact(BaseModel):
    company_name: str = Field(..., alias="companyName", max_length=80)
    full_name: str = Field(..., alias="fullName", max_length=45)
    phone: str = Field(..., max_length=25)
    email: str = Field("", max_length=50)

    model_config = {"populate_by_name": True}


class Party(BaseModel):
    address: Address
    contact: Contact


class RegistrationNumber(BaseModel):
    type_code: str = Field(..., alias="typeCode")
    number: str
    issuer_country_code: str = Field(..., alias="issuerCountryCode")

    model_config = {"populate_by_name": True}


# ---------------------------------------------------------------------------
# Parcel / package
# ---------------------------------------------------------------------------

class Dimensions(BaseModel):
    length: float
    width: float
    height: float


class Package(BaseModel):
    weight: float
    dimensions: Dimensions | None = None
    description: str = ""


# ---------------------------------------------------------------------------
# Export declaration / customs
# ---------------------------------------------------------------------------

class LineItem(BaseModel):
    number: int = 1
    description: str
    price: float
    quantity: int = 1
    quantity_type: str = Field("PCS", alias="quantityType")
    manufacturing_country_code: str = Field("PL", alias="manufacturingCountryCode")
    weight: float = 0.0
    hs_code: str = Field("", alias="hsCode")

    model_config = {"populate_by_name": True}


class ExportDeclaration(BaseModel):
    line_items: list[LineItem] = Field(default_factory=list, alias="lineItems")
    invoice_number: str = Field("", alias="invoiceNumber")
    invoice_date: str = Field("", alias="invoiceDate")
    export_reason: str = Field("SALE", alias="exportReason")
    export_reason_type: str = Field("permanent", alias="exportReasonType")

    model_config = {"populate_by_name": True}


# ---------------------------------------------------------------------------
# Value-added services
# ---------------------------------------------------------------------------

class ValueAddedService(BaseModel):
    service_code: str = Field(..., alias="serviceCode")
    value: float | None = None
    currency: str | None = None

    model_config = {"populate_by_name": True}


# ---------------------------------------------------------------------------
# Shipment creation request
# ---------------------------------------------------------------------------

class ShipmentContent(BaseModel):
    packages: list[Package]
    is_custom_declarable: bool = Field(True, alias="isCustomsDeclarable")
    declared_value: float = Field(0, alias="declaredValue")
    declared_value_currency: str = Field("EUR", alias="declaredValueCurrency")
    description: str = ""
    incoterm_code: str = Field("DAP", alias="incotermCode")
    unit_of_measurement: str = Field("metric", alias="unitOfMeasurement")
    export_declaration: ExportDeclaration | None = Field(None, alias="exportDeclaration")

    model_config = {"populate_by_name": True}


class ShipmentOutput(BaseModel):
    dhl_custom_invoice: bool = Field(False, alias="dhlCustomsInvoice")
    image_format: str = Field("PDF", alias="imageFormat")
    label_type: str = Field("PDF", alias="labelType")

    model_config = {"populate_by_name": True}


class CreateShipmentRequest(BaseModel):
    planned_shipping_date_and_time: str = Field(..., alias="plannedShippingDateAndTime")
    product_code: str = Field("P", alias="productCode")
    accounts: list[dict] = Field(default_factory=list)
    shipper: Party
    receiver: Party
    content: ShipmentContent
    output_image_properties: ShipmentOutput = Field(
        default_factory=ShipmentOutput, alias="outputImageProperties",
    )
    value_added_services: list[ValueAddedService] = Field(
        default_factory=list, alias="valueAddedServices",
    )
    pickup: dict = Field(default_factory=dict)
    customer_references: list[dict] = Field(default_factory=list, alias="customerReferences")

    model_config = {"populate_by_name": True}


# ---------------------------------------------------------------------------
# Rate request
# ---------------------------------------------------------------------------

class RateRequest(BaseModel):
    shipper_country_code: str = Field("PL", alias="shipperCountryCode")
    shipper_postal_code: str = Field("", alias="shipperPostalCode")
    shipper_city: str = Field("", alias="shipperCity")
    receiver_country_code: str = Field("PL", alias="receiverCountryCode")
    receiver_postal_code: str = Field("", alias="receiverPostalCode")
    receiver_city: str = Field("", alias="receiverCity")
    planned_shipping_date: str = Field("", alias="plannedShippingDate")
    weight: float = 0
    length: float = 0
    width: float = 0
    height: float = 0
    unit_of_measurement: str = Field("metric", alias="unitOfMeasurement")
    is_customs_declarable: bool = Field(False, alias="isCustomsDeclarable")

    model_config = {"populate_by_name": True}


# ---------------------------------------------------------------------------
# Pickup request
# ---------------------------------------------------------------------------

class PickupRequest(BaseModel):
    planned_pickup_date_and_time: str = Field(..., alias="plannedPickupDateAndTime")
    close_time: str = Field(..., alias="closeTime")
    location: str = ""
    location_type: str = Field("business", alias="locationType")
    accounts: list[dict] = Field(default_factory=list)
    special_instructions: list[str] = Field(default_factory=list, alias="specialInstructions")
    customer_details: Party | None = Field(None, alias="customerDetails")
    shipment_info: list[dict] = Field(default_factory=list, alias="shipmentInfo")

    model_config = {"populate_by_name": True}


# ---------------------------------------------------------------------------
# Tracking request
# ---------------------------------------------------------------------------

class TrackingQuery(BaseModel):
    tracking_number: str
    tracking_view: str = "all-checkpoints"
    level_of_detail: str = "all"


# ---------------------------------------------------------------------------
# Standardized rate response (used by shipping price comparison workflow)
# ---------------------------------------------------------------------------

class RateProduct(BaseModel):
    name: str
    price: float
    currency: str = "PLN"
    delivery_days: int | None = None
    delivery_date: str = ""
    attributes: dict = Field(default_factory=dict)


class StandardizedRateResponse(BaseModel):
    products: list[RateProduct] = Field(default_factory=list)
    source: str = ""
    raw: dict = Field(default_factory=dict)
