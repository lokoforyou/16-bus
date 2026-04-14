from app.domain.compliance.models import BoardingORM
from app.domain.compliance.repository import ComplianceRepository
from app.domain.compliance.schemas import BoardingCreate

class ComplianceService:
    def __init__(self, repository: ComplianceRepository):
        self.repository = repository

    def log_boarding(self, data: BoardingCreate) -> BoardingORM:
        boarding = BoardingORM(
            booking_id=data.booking_id,
            driver_id=data.driver_id,
            vehicle_id=data.vehicle_id,
            stop_id=data.stop_id,
        )
        return self.repository.record_boarding(boarding)
