from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.trips.models import TripORM


class TripRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_trip(self, trip_id: str) -> TripORM | None:
        return self.session.get(TripORM, trip_id)

    def get_trip_for_update(self, trip_id: str) -> TripORM | None:
        stmt = select(TripORM).where(TripORM.id == trip_id).with_for_update()
        return self.session.scalars(stmt).first()

    def list_trips(self, organization_id: str | None = None) -> list[TripORM]:
        stmt = select(TripORM)
        if organization_id:
            stmt = stmt.where(TripORM.organization_id == organization_id)
        return list(self.session.scalars(stmt).all())

    def create(self, trip: TripORM) -> TripORM:
        self.session.add(trip)
        self.session.flush()
        self.session.refresh(trip)
        return trip

    def update(self, trip: TripORM) -> TripORM:
        self.session.add(trip)
        self.session.flush()
        self.session.refresh(trip)
        return trip

    def reserve_seats(self, trip: TripORM, seats: int) -> None:
        trip.seats_free -= seats
        self.session.add(trip)
        self.session.flush()

    def release_seats(self, trip: TripORM, seats: int) -> None:
        trip.seats_free = min(trip.seats_total, trip.seats_free + seats)
        self.session.add(trip)
        self.session.flush()
