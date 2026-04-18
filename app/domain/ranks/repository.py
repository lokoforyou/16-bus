from sqlalchemy import func, select
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

    def get_for_update(self, ticket_id: str) -> RankQueueTicketORM | None:
        stmt = select(RankQueueTicketORM).where(RankQueueTicketORM.id == ticket_id).with_for_update()
        return self.session.scalars(stmt).first()

    def list_by_rank(self, rank_id: str) -> list[RankQueueTicketORM]:
        stmt = (
            select(RankQueueTicketORM)
            .where(RankQueueTicketORM.rank_id == rank_id)
            .order_by(RankQueueTicketORM.queue_number.asc())
        )
        return list(self.session.scalars(stmt).all())

    def get_earliest_pending(self, rank_id: str) -> RankQueueTicketORM | None:
        stmt = (
            select(RankQueueTicketORM)
            .where(
                RankQueueTicketORM.rank_id == rank_id,
                RankQueueTicketORM.state.in_(("issued", "assigned")),
            )
            .order_by(RankQueueTicketORM.queue_number.asc())
            .limit(1)
        )
        return self.session.scalars(stmt).first()

    def next_queue_number(self, rank_id: str) -> int:
        stmt = select(func.coalesce(func.max(RankQueueTicketORM.queue_number), 0)).where(
            RankQueueTicketORM.rank_id == rank_id
        )
        return int(self.session.execute(stmt).scalar_one()) + 1

    def list_for_trip(self, trip_id: str) -> list[RankQueueTicketORM]:
        stmt = select(RankQueueTicketORM).where(RankQueueTicketORM.trip_id == trip_id)
        return list(self.session.scalars(stmt).all())
