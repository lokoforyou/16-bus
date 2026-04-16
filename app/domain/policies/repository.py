from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.policies.models import PolicyORM


class PolicyRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, policy: PolicyORM) -> PolicyORM:
        self.session.add(policy)
        self.session.flush()
        self.session.refresh(policy)
        return policy

    def get(self, policy_id: str) -> PolicyORM | None:
        return self.session.get(PolicyORM, policy_id)

    def get_active_for_route(self, route_id: str) -> PolicyORM | None:
        stmt = select(PolicyORM).where(PolicyORM.route_id == route_id, PolicyORM.active.is_(True))
        return self.session.scalars(stmt).first()
