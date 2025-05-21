from typing import Annotated, Sequence

from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from visit_manager.app.models.user_models import UserCreate
from visit_manager.postgres_utils.models.users import User, add_user, read_all_users
from visit_manager.postgres_utils.utils import get_db

router = APIRouter(prefix="/user", tags=["user"], responses={404: {"description": "Not found"}})


@router.post("/add", response_model=UserCreate)  # TODO change to real response model
async def add_user_end(user: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]) -> User:
    return await add_user(db, user)


@router.get("/read", response_model=list[UserCreate])  # TODO change to real response model, add real logic
async def read_all_end(db: Annotated[AsyncSession, Depends(get_db)]) -> Sequence[User]:
    return await read_all_users(db)


@router.get("/test/{vendor_id}")
async def test(vendor_id: str, session: Annotated[AsyncSession, Depends(get_db)]) -> str:
    """Example how to query async attributes"""
    async with session.begin():
        user = await session.get_one(User, vendor_id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        if user.vendor_profile is None:
            raise HTTPException(status_code=400, detail="User is not a vendor")
        # note `awaitable_attrs` here!
        service_types = await user.vendor_profile.awaitable_attrs.offered_service_types
        return repr([vars(st) for st in service_types])
