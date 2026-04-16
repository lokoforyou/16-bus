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


class StopCreate(BaseModel):
    id: str
    name: str
    type: str
    lat: float
    lon: float
    cash_allowed: bool = False
    active: bool = True


class StopUpdate(BaseModel):
    name: str | None = None
    type: str | None = None
    lat: float | None = None
    lon: float | None = None
    cash_allowed: bool | None = None
    active: bool | None = None


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


class StopRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    type: str
    lat: float
    lon: float
    cash_allowed: bool
    active: bool


class RouteListResponse(BaseModel):
    items: list[RouteRead]


class RouteStopListResponse(BaseModel):
    items: list[RouteStopRead]


class StopListResponse(BaseModel):
    items: list[StopRead]
