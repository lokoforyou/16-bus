from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.domain.bookings.models import BookingORM
from app.domain.bookings.policy import BookingPolicy
from app.domain.trips.repository import TripRepository


class BookingRepository:
    def __init__(self, session: Session, trip_repository: TripRepository) -> None:
        self.session = session
        self.trip_repository = trip_repository

    def save(self, booking: BookingORM) -> BookingORM:
        self.session.add(booking)
        self.session.commit()
        self.session.refresh(booking)
        return booking

    def get(self, booking_id: str) -> BookingORM | None:
        booking = self.session.get(BookingORM, booking_id)
        if booking is None:
            return None

        previous_state = booking.booking_state
        booking = BookingPolicy.ensure_booking_is_active(booking)
        if previous_state != booking.booking_state:
            self.session.add(booking)
            self.session.commit()
            if booking.booking_state == "expired":
                self.trip_repository.release_seats(booking.trip_id, booking.party_size)
            self.session.refresh(booking)
        return booking

    def all(self) -> list[BookingORM]:
        now = datetime.now(UTC)
        return list(
            self.session.query(BookingORM)
            .filter(
                (BookingORM.hold_expires_at >= now)
                | (BookingORM.booking_state != "expired")
            )
            .all()
        )

    def update(self, booking: BookingORM) -> BookingORM:
        self.session.add(booking)
        self.session.commit()
        self.session.refresh(booking)
        return booking
