from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.domain.auth.models import UserORM


class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, user_id: str) -> Optional[UserORM]:
        return self.session.get(UserORM, user_id)

    def get_by_phone(self, phone: str) -> Optional[UserORM]:
        stmt = select(UserORM).where(UserORM.phone == phone)
        return self.session.execute(stmt).scalar_one_or_none()

    def create(self, user: UserORM) -> UserORM:
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def update(self, user: UserORM) -> UserORM:
        self.session.commit()
        self.session.refresh(user)
        return user
