from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from visit_manager.app.models.user_models import UserCreate
from visit_manager.postgres_utils.models.models import User


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


async def get_or_create_user(session: AsyncSession, email: str, first_name: str, last_name: str) -> User:
    async with session.begin():
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user:
            return user
        user = User(email=email, first_name=first_name, last_name=last_name)
        session.add(user)
        await session.flush()
        return user
