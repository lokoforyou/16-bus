from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.domain.organizations.models import OrganizationORM


class OrganizationRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, org_id: str) -> Optional[OrganizationORM]:
        return self.session.get(OrganizationORM, org_id)

    def get_by_name(self, name: str) -> Optional[OrganizationORM]:
        stmt = select(OrganizationORM).where(OrganizationORM.name == name)
        return self.session.execute(stmt).scalar_one_or_none()

    def list(self) -> List[OrganizationORM]:
        stmt = select(OrganizationORM)
        return list(self.session.execute(stmt).scalars().all())

    def create(self, org: OrganizationORM) -> OrganizationORM:
        self.session.add(org)
        self.session.flush()
        self.session.refresh(org)
        return org

    def update(self, org: OrganizationORM) -> OrganizationORM:
        self.session.add(org)
        self.session.flush()
        self.session.refresh(org)
        return org

    def delete(self, org: OrganizationORM) -> None:
        self.session.delete(org)
        self.session.flush()
