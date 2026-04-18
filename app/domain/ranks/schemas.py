from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RankTicketIssueRequest(BaseModel):
    rank_id: str
    trip_id: str | None = None


class RankTicketAssignRequest(BaseModel):
    ticket_id: str
    trip_id: str


class RankCashAuthorizationRequest(BaseModel):
    booking_id: str
    rank_id: str


class RankQueueTicketRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    rank_id: str
    trip_id: str | None
    queue_number: int
    payment_status: str
    qr_token_id: str | None = None
    state: str
    issued_at: datetime
