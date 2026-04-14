from typing import List, Optional
from sqlalchemy import select, and_, update
from sqlalchemy.orm import Session
from app.domain.trips.models import TripORM, TripStatus

class TripRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_trip(self, trip_id: str) -> TripORM | None:
        return self.session.get(TripORM, trip_id)

    def list_trips(self, organization_id: str | None = None) -> List[TripORM]:
        stmt = select(TripORM)
        if organization_id:
            stmt = stmt.where(TripORM.organization_id == organization_id)
        return list(self.session.scalars(stmt).all())

    def create(self, trip: TripORM) -> TripORM:
        self.session.add(trip)
        self.session.commit()
        self.session.refresh(trip)
        return trip

    def update(self, trip: TripORM) -> TripORM:
        self.session.commit()
        self.session.refresh(trip)
        return trip
