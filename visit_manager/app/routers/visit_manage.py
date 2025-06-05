from typing import Annotated

from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from visit_manager.app.models.user_models import UserCreate, UserSessionData, VendorCreate
from visit_manager.app.security.common import get_current_user
from visit_manager.postgres_utils.models.users import User, create_or_update_user, register_as_vendor
from visit_manager.postgres_utils.utils import get_db

router = APIRouter(prefix="/user", tags=["user"], responses={404: {"description": "Not found"}})


@router.post("/register_as_vendor")
async def register_vendor(
    vendor_data: VendorCreate,
    current_user: Annotated[UserSessionData, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    async with session.begin():
        return await register_as_vendor(session, current_user, vendor_data)


@router.post("/add_user")  # TODO: remove
async def add_user(session: Annotated[AsyncSession, Depends(get_db)]):
    async with session.begin():
        return await create_or_update_user(session, UserCreate(email="test@test.com", full_name="test user"))


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
