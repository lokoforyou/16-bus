from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.domain.drivers.models import DriverORM


class DriverRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, driver_id: str) -> Optional[DriverORM]:
        return self.session.get(DriverORM, driver_id)

    def get_by_phone(self, phone: str) -> Optional[DriverORM]:
        stmt = select(DriverORM).where(DriverORM.phone == phone)
        return self.session.execute(stmt).scalar_one_or_none()

    def get_by_user_id(self, user_id: str) -> Optional[DriverORM]:
        stmt = select(DriverORM).where(DriverORM.user_id == user_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def list_by_org(self, organization_id: str) -> List[DriverORM]:
        stmt = select(DriverORM).where(DriverORM.organization_id == organization_id)
        return list(self.session.execute(stmt).scalars().all())

    def list_all(self) -> List[DriverORM]:
        stmt = select(DriverORM)
        return list(self.session.execute(stmt).scalars().all())

    def create(self, driver: DriverORM) -> DriverORM:
        self.session.add(driver)
        self.session.commit()
        self.session.refresh(driver)
        return driver

    def update(self, driver: DriverORM) -> DriverORM:
        self.session.commit()
        self.session.refresh(driver)
        return driver
