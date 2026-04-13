from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.qr.models import QRTokenORM


class QRRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, token: QRTokenORM) -> QRTokenORM:
        self.session.add(token)
        self.session.commit()
        self.session.refresh(token)
        return token

    def get(self, token_id: str) -> QRTokenORM | None:
        return self.session.get(QRTokenORM, token_id)

    def get_by_booking(self, booking_id: str) -> QRTokenORM | None:
        statement = select(QRTokenORM).where(QRTokenORM.booking_id == booking_id).limit(1)
        return self.session.scalars(statement).first()
