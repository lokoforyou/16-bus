from pydantic import BaseModel, ConfigDict


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


class RouteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    code: str
    name: str
    direction: str
    active: bool


class RouteStopRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    route_variant_id: str
    stop_id: str
    sequence_number: int
    dwell_time_seconds: int


class RouteListResponse(BaseModel):
    items: list[RouteRead]


class RouteStopListResponse(BaseModel):
    items: list[RouteStopRead]
