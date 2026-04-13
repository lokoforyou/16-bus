from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PaymentRequest(BaseModel):
    method: str = Field(pattern="^(wallet|card|eft)$")


class PaymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    booking_id: str
    method: str
    amount: float
    status: str
    reference: str
    settled_at: datetime | None = None


class PaymentDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    payment: PaymentRead
