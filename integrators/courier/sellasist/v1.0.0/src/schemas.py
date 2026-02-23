from pydantic import BaseModel, Field


class SellAsistCredentials(BaseModel):
    login: str = Field(..., description="SellAsist account login used in the API URL")
    api_key: str = Field(..., description="SellAsist API key for authentication")


class LabelRequest(BaseModel):
    credentials: SellAsistCredentials
    waybill_numbers: list[str] = Field(..., min_length=1)
    external_id: str = Field(..., description="Order external ID in SellAsist")


class ErrorResponse(BaseModel):
    error: dict
