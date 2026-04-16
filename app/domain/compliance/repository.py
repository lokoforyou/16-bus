from sqlalchemy.orm import Session
from app.domain.compliance.models import BoardingORM

class ComplianceRepository:
    def __init__(self, session: Session):
        self.session = session

    def record_boarding(self, boarding: BoardingORM) -> BoardingORM:
        self.session.add(boarding)
        self.session.flush()
        self.session.refresh(boarding)
        return boarding
