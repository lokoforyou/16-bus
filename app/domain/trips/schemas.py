from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TripCreate(BaseModel):
    id: str
    route_id: str
    route_variant_id: str
    organization_id: str
    vehicle_id: str
    driver_id: str
    trip_type: str
    planned_start_time: datetime
    state: str
    seats_total: int = Field(ge=1, le=64)
    seats_free: int = Field(ge=0, le=64)
    current_stop_id: str


class TripRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    route_id: str
    route_variant_id: str
    organization_id: str
    vehicle_id: str
    driver_id: str
    trip_type: str
    planned_start_time: datetime
    state: str
    seats_total: int
    seats_free: int
    current_stop_id: str


class TripUpdate(BaseModel):
    route_id: str | None = None
    route_variant_id: str | None = None
    organization_id: str | None = None
    vehicle_id: str | None = None
    driver_id: str | None = None
    trip_type: str | None = None
    planned_start_time: datetime | None = None
    state: str | None = None
    seats_total: int | None = Field(default=None, ge=1, le=64)
    seats_free: int | None = Field(default=None, ge=0, le=64)
    current_stop_id: str | None = None
