from pydantic import BaseModel, ConfigDict


class StopRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    type: str
    lat: float
    lon: float
    cash_allowed: bool
    sequence_number: int
    dwell_time_seconds: int


class RouteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    code: str
    name: str
    direction: str
    active: bool


class RouteListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: list[RouteRead]


class RouteStopListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    route_id: str
    items: list[StopRead]
