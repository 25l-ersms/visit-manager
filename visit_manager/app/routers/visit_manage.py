from typing import Annotated, List

from fastapi import APIRouter
from fastapi.params import Depends
from sqlalchemy.orm import Session

from visit_manager.app.models.models import UserCreate
from visit_manager.postgres_utils.models.users import User, add_user, read_all_users
from visit_manager.postgres_utils.utils import get_db

router = APIRouter(prefix="/user", tags=["user"], responses={404: {"description": "Not found"}})


@router.post("/add", response_model=UserCreate)  # TODO change to real response model
async def add_user_end(user: UserCreate, db: Annotated[Session, Depends(get_db)]) -> User:
    return add_user(db, user)


@router.get("/read", response_model=List[UserCreate])  # TODO change to real response model, add real logic
async def read_all_end(db: Annotated[Session, Depends(get_db)]) -> list[User]:
    return read_all_users(db)
