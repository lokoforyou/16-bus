from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from app.domain.shifts.models import DriverShiftORM, ShiftStatus


class ShiftRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, shift_id: str) -> Optional[DriverShiftORM]:
        return self.session.get(DriverShiftORM, shift_id)

    def get_active_by_driver(self, driver_id: str) -> Optional[DriverShiftORM]:
        stmt = select(DriverShiftORM).where(
            and_(
                DriverShiftORM.driver_id == driver_id,
                DriverShiftORM.status == ShiftStatus.ACTIVE
            )
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def get_active_by_vehicle(self, vehicle_id: str) -> Optional[DriverShiftORM]:
        stmt = select(DriverShiftORM).where(
            and_(
                DriverShiftORM.vehicle_id == vehicle_id,
                DriverShiftORM.status == ShiftStatus.ACTIVE
            )
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def list_by_org(self, organization_id: str) -> List[DriverShiftORM]:
        stmt = select(DriverShiftORM).where(DriverShiftORM.organization_id == organization_id)
        return list(self.session.execute(stmt).scalars().all())

    def create(self, shift: DriverShiftORM) -> DriverShiftORM:
        self.session.add(shift)
        self.session.commit()
        self.session.refresh(shift)
        return shift

    def update(self, shift: DriverShiftORM) -> DriverShiftORM:
        self.session.commit()
        self.session.refresh(shift)
        return shift
