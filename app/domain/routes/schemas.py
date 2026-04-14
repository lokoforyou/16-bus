from pydantic import BaseModel

class RouteCreate(BaseModel):
    id: str
    organization_id: str
    code: str
    name: str
    direction: str

class RouteVariantCreate(BaseModel):
    id: str
    name: str

class RouteStopCreate(BaseModel):
    stop_id: str
    sequence_number: int
    dwell_time_seconds: int
