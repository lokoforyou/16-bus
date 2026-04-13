from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.payments.models import PaymentORM


class PaymentRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, payment: PaymentORM) -> PaymentORM:
        self.session.add(payment)
        self.session.commit()
        self.session.refresh(payment)
        return payment

    def get(self, payment_id: str) -> PaymentORM | None:
        return self.session.get(PaymentORM, payment_id)

    def get_latest_for_booking(self, booking_id: str) -> PaymentORM | None:
        statement = (
            select(PaymentORM)
            .where(PaymentORM.booking_id == booking_id)
            .order_by(PaymentORM.settled_at.desc().nullslast(), PaymentORM.id.desc())
            .limit(1)
        )
        return self.session.scalars(statement).first()
