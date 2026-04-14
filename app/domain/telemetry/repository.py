from sqlalchemy.orm import Session
from app.domain.telemetry.models import VehicleLocationORM

class TelemetryRepository:
    def __init__(self, session: Session):
        self.session = session

    def add_location(self, location: VehicleLocationORM) -> VehicleLocationORM:
        self.session.add(location)
        self.session.commit()
        self.session.refresh(location)
        return location
