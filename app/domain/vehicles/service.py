from typing import List, Optional
from app.core.exceptions import ConflictError, NotFoundError
from app.domain.vehicles.models import VehicleORM
from app.domain.vehicles.repository import VehicleRepository
from app.domain.vehicles.schemas import VehicleCreate, VehicleUpdate


class VehicleService:
    def __init__(self, repository: VehicleRepository):
        self.repository = repository

    def create_vehicle(self, data: VehicleCreate) -> VehicleORM:
        existing = self.repository.get_by_plate(data.plate_number)
        if existing:
            raise ConflictError(f"Vehicle with plate {data.plate_number} already exists")

        vehicle = VehicleORM(
            organization_id=data.organization_id,
            plate_number=data.plate_number,
            capacity=data.capacity,
            permit_number=data.permit_number,
            compliance_status=data.compliance_status,
            is_active=data.is_active
        )
        return self.repository.create(vehicle)

    def get_vehicle(self, vehicle_id: str) -> VehicleORM:
        vehicle = self.repository.get_by_id(vehicle_id)
        if not vehicle:
            raise NotFoundError("Vehicle not found")
        return vehicle

    def list_vehicles(self, organization_id: Optional[str] = None) -> List[VehicleORM]:
        if organization_id:
            return self.repository.list_by_org(organization_id)
        return self.repository.list_all()

    def update_vehicle(self, vehicle_id: str, data: VehicleUpdate) -> VehicleORM:
        vehicle = self.get_vehicle(vehicle_id)
        
        if data.plate_number is not None:
            existing = self.repository.get_by_plate(data.plate_number)
            if existing and existing.id != vehicle_id:
                raise ConflictError(f"Vehicle with plate {data.plate_number} already exists")
            vehicle.plate_number = data.plate_number
        
        if data.organization_id is not None:
            vehicle.organization_id = data.organization_id
        if data.capacity is not None:
            vehicle.capacity = data.capacity
        if data.permit_number is not None:
            vehicle.permit_number = data.permit_number
        if data.compliance_status is not None:
            vehicle.compliance_status = data.compliance_status
        if data.is_active is not None:
            vehicle.is_active = data.is_active
            
        return self.repository.update(vehicle)
