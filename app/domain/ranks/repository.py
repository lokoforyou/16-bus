from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.ranks.models import RankQueueTicketORM


class RankQueueRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, ticket: RankQueueTicketORM) -> RankQueueTicketORM:
        self.session.add(ticket)
        self.session.flush()
        self.session.refresh(ticket)
        return ticket

    def get(self, ticket_id: str) -> RankQueueTicketORM | None:
        return self.session.get(RankQueueTicketORM, ticket_id)

    def list_for_trip(self, trip_id: str) -> list[RankQueueTicketORM]:
        stmt = select(RankQueueTicketORM).where(RankQueueTicketORM.trip_id == trip_id)
        return list(self.session.scalars(stmt).all())
