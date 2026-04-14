from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.bookings.models import BookingORM


class BookingRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, booking: BookingORM) -> BookingORM:
        self.session.add(booking)
        self.session.flush()
        self.session.refresh(booking)
        return booking

    def get(self, booking_id: str) -> BookingORM | None:
        return self.session.get(BookingORM, booking_id)

    def get_for_update(self, booking_id: str) -> BookingORM | None:
        stmt = select(BookingORM).where(BookingORM.id == booking_id).with_for_update()
        return self.session.scalars(stmt).first()

    def all(self) -> list[BookingORM]:
        return list(self.session.query(BookingORM).all())

    def list_expired_holds(self, now: datetime | None = None) -> list[BookingORM]:
        moment = now or datetime.now(UTC)
        stmt = select(BookingORM).where(
            BookingORM.booking_state == "held",
            BookingORM.hold_expires_at <= moment,
        )
        return list(self.session.scalars(stmt).all())

    def update(self, booking: BookingORM) -> BookingORM:
        self.session.add(booking)
        self.session.flush()
        self.session.refresh(booking)
        return booking
