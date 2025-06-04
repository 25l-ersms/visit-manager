from typing import Annotated

from fastapi import APIRouter
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from visit_manager.app.models.user_models import UserSessionData, VendorCreate
from visit_manager.app.security.common import get_current_user
from visit_manager.postgres_utils.models.users import register_as_vendor
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
