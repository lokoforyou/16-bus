from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.domain.vehicles.models import VehicleORM


class VehicleRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, vehicle_id: str) -> Optional[VehicleORM]:
        return self.session.get(VehicleORM, vehicle_id)

    def get_by_plate(self, plate: str) -> Optional[VehicleORM]:
        stmt = select(VehicleORM).where(VehicleORM.plate_number == plate)
        return self.session.execute(stmt).scalar_one_or_none()

    def list_by_org(self, organization_id: str) -> List[VehicleORM]:
        stmt = select(VehicleORM).where(VehicleORM.organization_id == organization_id)
        return list(self.session.execute(stmt).scalars().all())

    def list_all(self) -> List[VehicleORM]:
        stmt = select(VehicleORM)
        return list(self.session.execute(stmt).scalars().all())

    def create(self, vehicle: VehicleORM) -> VehicleORM:
        self.session.add(vehicle)
        self.session.flush()
        self.session.refresh(vehicle)
        return vehicle

    def update(self, vehicle: VehicleORM) -> VehicleORM:
        self.session.add(vehicle)
        self.session.flush()
        self.session.refresh(vehicle)
        return vehicle
