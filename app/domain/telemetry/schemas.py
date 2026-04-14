from pydantic import BaseModel
from datetime import datetime

class LocationUpdate(BaseModel):
    vehicle_id: str
    lat: float
    lon: float

class VehicleLocation(LocationUpdate):
    id: str
    recorded_at: datetime

    class Config:
        from_attributes = True
