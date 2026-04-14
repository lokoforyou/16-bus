from app.domain.telemetry.models import VehicleLocationORM
from app.domain.telemetry.repository import TelemetryRepository
from app.domain.telemetry.schemas import LocationUpdate

class TelemetryService:
    def __init__(self, repository: TelemetryRepository):
        self.repository = repository

    def process_location(self, data: LocationUpdate) -> VehicleLocationORM:
        location = VehicleLocationORM(
            vehicle_id=data.vehicle_id,
            lat=data.lat,
            lon=data.lon,
        )
        return self.repository.add_location(location)
