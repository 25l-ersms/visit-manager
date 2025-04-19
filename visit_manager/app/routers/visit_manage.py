from typing import Annotated, Sequence

from fastapi import APIRouter
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from visit_manager.app.models.models import UserCreate
from visit_manager.postgres_utils.models.users import User, add_user, read_all_users
from visit_manager.postgres_utils.utils import get_db

router = APIRouter(prefix="/user", tags=["user"], responses={404: {"description": "Not found"}})


@router.post("/add", response_model=UserCreate)  # TODO change to real response model
async def add_user_end(user: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]) -> User:
    return await add_user(db, user)


@router.get("/read", response_model=list[UserCreate])  # TODO change to real response model, add real logic
async def read_all_end(db: Annotated[AsyncSession, Depends(get_db)]) -> Sequence[User]:
    return await read_all_users(db)
