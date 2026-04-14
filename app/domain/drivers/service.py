from typing import List, Optional
from app.core.exceptions import ConflictError, NotFoundError
from app.domain.drivers.models import DriverORM
from app.domain.drivers.repository import DriverRepository
from app.domain.drivers.schemas import DriverCreate, DriverUpdate


class DriverService:
    def __init__(self, repository: DriverRepository):
        self.repository = repository

    def create_driver(self, data: DriverCreate) -> DriverORM:
        existing_phone = self.repository.get_by_phone(data.phone)
        if existing_phone:
            raise ConflictError(f"Driver with phone {data.phone} already exists")
            
        existing_user = self.repository.get_by_user_id(data.user_id)
        if existing_user:
            raise ConflictError(f"Driver for user {data.user_id} already exists")

        driver = DriverORM(
            organization_id=data.organization_id,
            user_id=data.user_id,
            full_name=data.full_name,
            phone=data.phone,
            licence_number=data.licence_number,
            pdp_verified=data.pdp_verified,
            is_active=data.is_active
        )
        return self.repository.create(driver)

    def get_driver(self, driver_id: str) -> DriverORM:
        driver = self.repository.get_by_id(driver_id)
        if not driver:
            raise NotFoundError("Driver not found")
        return driver

    def get_driver_by_user_id(self, user_id: str) -> DriverORM:
        driver = self.repository.get_by_user_id(user_id)
        if not driver:
            raise NotFoundError("Driver not found for this user")
        return driver

    def list_drivers(self, organization_id: Optional[str] = None) -> List[DriverORM]:
        if organization_id:
            return self.repository.list_by_org(organization_id)
        return self.repository.list_all()

    def update_driver(self, driver_id: str, data: DriverUpdate) -> DriverORM:
        driver = self.get_driver(driver_id)
        
        if data.phone is not None:
            existing = self.repository.get_by_phone(data.phone)
            if existing and existing.id != driver_id:
                raise ConflictError(f"Driver with phone {data.phone} already exists")
            driver.phone = data.phone
        
        if data.organization_id is not None:
            driver.organization_id = data.organization_id
        if data.full_name is not None:
            driver.full_name = data.full_name
        if data.licence_number is not None:
            driver.licence_number = data.licence_number
        if data.pdp_verified is not None:
            driver.pdp_verified = data.pdp_verified
        if data.is_active is not None:
            driver.is_active = data.is_active
            
        return self.repository.update(driver)
