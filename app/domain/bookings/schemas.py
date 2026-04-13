from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.trips.schemas import TripRead


class BookingQuoteRequest(BaseModel):
    route_id: str
    origin_stop_id: str
    destination_stop_id: str
    party_size: int = Field(ge=1, le=16)


class BookingCandidateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    trip: TripRead
    eta_minutes: int
    estimated_fare: float


class BookingQuoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    candidates: list[BookingCandidateRead]


class CreateBookingRequest(BaseModel):
    passenger_id: str
    route_id: str
    origin_stop_id: str
    destination_stop_id: str
    party_size: int = Field(ge=1, le=16)
    booking_channel: str = "app"


class BookingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    trip_id: str
    passenger_id: str
    origin_stop_id: str
    destination_stop_id: str
    party_size: int
    fare_amount: float
    hold_expires_at: datetime
    payment_status: str
    booking_state: str
    forfeiture_fee_amount: float
    booking_channel: str
    qr_token_id: str | None = None


class BookingCreatedResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    booking: BookingRead


class BookingDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    booking: BookingRead


class BookingPaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    booking: BookingRead
    payment_id: str


class BookingCancelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    booking: BookingRead
