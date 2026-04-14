from pydantic import BaseModel
from datetime import datetime

class BoardingCreate(BaseModel):
    booking_id: str
    driver_id: str
    vehicle_id: str
    stop_id: str

class Boarding(BoardingCreate):
    id: str
    boarded_at: datetime

    class Config:
        from_attributes = True
