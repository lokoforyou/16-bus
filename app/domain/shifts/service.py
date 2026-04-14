from datetime import UTC, datetime

from app.core.exceptions import ConflictError, DomainRuleViolationError, NotFoundError, PermissionDeniedError
from app.domain.drivers.repository import DriverRepository
from app.domain.shifts.models import DriverShiftORM, ShiftStatus
from app.domain.shifts.repository import ShiftRepository
from app.domain.shifts.schemas import ShiftCreate
from app.domain.vehicles.repository import VehicleRepository


class ShiftService:
    def __init__(
        self,
        repository: ShiftRepository,
        driver_repository: DriverRepository,
        vehicle_repository: VehicleRepository,
    ):
        self.repository = repository
        self.driver_repository = driver_repository
        self.vehicle_repository = vehicle_repository

    def start_shift(self, data: ShiftCreate, actor_user_id: str | None = None) -> DriverShiftORM:
        driver = self.driver_repository.get_by_id(data.driver_id)
        if not driver:
            raise NotFoundError("Driver not found")
        if actor_user_id and driver.user_id != actor_user_id:
            raise PermissionDeniedError("Drivers can only start their own shifts")
        if not driver.is_active:
            raise DomainRuleViolationError("Inactive driver cannot start a shift")

        vehicle = self.vehicle_repository.get_by_id(data.vehicle_id)
        if not vehicle:
            raise NotFoundError("Vehicle not found")
        if not vehicle.is_active:
            raise DomainRuleViolationError("Inactive vehicle cannot start a shift")

        if driver.organization_id != vehicle.organization_id:
            raise DomainRuleViolationError("Driver and vehicle must belong to the same organization")

        existing_driver_shift = self.repository.get_active_by_driver(data.driver_id)
        if existing_driver_shift:
            raise ConflictError("Driver already has an active shift")

        existing_vehicle_shift = self.repository.get_active_by_vehicle(data.vehicle_id)
        if existing_vehicle_shift:
            raise ConflictError("Vehicle already has an active shift")

        shift = DriverShiftORM(
            driver_id=data.driver_id,
            vehicle_id=data.vehicle_id,
            organization_id=driver.organization_id,
            status=ShiftStatus.ACTIVE,
        )
        return self.repository.create(shift)

    def end_shift(self, shift_id: str, actor_user_id: str | None = None) -> DriverShiftORM:
        shift = self.repository.get_by_id(shift_id)
        if not shift:
            raise NotFoundError("Shift not found")

        driver = self.driver_repository.get_by_id(shift.driver_id)
        if actor_user_id and driver and driver.user_id != actor_user_id:
            raise PermissionDeniedError("Drivers can only end their own shifts")

        if shift.status != ShiftStatus.ACTIVE:
            raise DomainRuleViolationError("Only active shifts can be ended")

        shift.status = ShiftStatus.COMPLETED
        shift.end_time = datetime.now(UTC)
        return self.repository.update(shift)

    def get_active_shift_for_driver(self, driver_user_id: str) -> DriverShiftORM:
        driver = self.driver_repository.get_by_user_id(driver_user_id)
        if not driver:
            raise NotFoundError("Driver not found for current user")
        shift = self.repository.get_active_by_driver(driver.id)
        if not shift:
            raise NotFoundError("No active shift found for this driver")
        return shift

    def list_organization_shifts(self, organization_id: str) -> list[DriverShiftORM]:
        return self.repository.list_by_org(organization_id)
