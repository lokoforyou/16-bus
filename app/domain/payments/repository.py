from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.domain.payments.models import PaymentORM


class PaymentRepository:
    def __init__(self, session: Session):
        self.session = session

    def save(self, payment: PaymentORM) -> PaymentORM:
        self.session.add(payment)
        self.session.commit()
        self.session.refresh(payment)
        return payment

    def get_latest_for_booking(self, booking_id: str) -> Optional[PaymentORM]:
        stmt = select(PaymentORM).where(PaymentORM.booking_id == booking_id).order_by(PaymentORM.settled_at.desc())
        return self.session.execute(stmt).scalars().first()
