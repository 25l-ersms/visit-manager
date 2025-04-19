import uuid
from typing import Sequence

from sqlalchemy import UUID, Column, String, select
from sqlalchemy.ext.asyncio import AsyncSession

from visit_manager.app.models.models import UserCreate
from visit_manager.postgres_utils.models.common import Base


# TODO its just an example
class User(Base):
    __tablename__ = "users"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)


async def add_user(session: AsyncSession, user: UserCreate) -> User:
    async with session.begin():
        db_user = User(email=str(user.email), full_name=user.full_name)
        session.add(db_user)
        return db_user


async def read_all_users(session: AsyncSession) -> Sequence[User]:
    async with session.begin():
        result = await session.execute(select(User))
        users = result.scalars().all()
        return users
