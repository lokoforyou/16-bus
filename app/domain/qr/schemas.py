from datetime import datetime

from pydantic import BaseModel, ConfigDict


class QRTokenRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    booking_id: str
    state: str
    issued_at: datetime
    scanned_at: datetime | None = None


class BoardingScanRequest(BaseModel):
    qr_token_id: str


class BoardingScanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    booking_id: str
    trip_id: str
    booking_state: str
    qr_token_state: str
