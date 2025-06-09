from typing import Annotated

from fastapi import APIRouter
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from visit_manager.app.models.user_models import UserSessionData, VendorCreate, VisitCreate, ClientCreate
from visit_manager.app.security.common import get_current_user
from visit_manager.postgres_utils.models.users import book_visit_in_db, get_my_visits_from_db, register_as_client, register_as_vendor, get_me_from_db
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

@router.post("/book_visit")
async def book_visit(
    visit_data: VisitCreate,
    current_user: Annotated[UserSessionData, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    async with session.begin():
        return await book_visit_in_db(session, current_user, visit_data)

@router.get("/my_visits")
async def get_my_visits(
    current_user: Annotated[UserSessionData, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    async with session.begin():
        return await get_my_visits_from_db(session, current_user)


@router.post("/register_as_client")
async def register_client(
    client_data: ClientCreate,
    current_user: Annotated[UserSessionData, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    async with session.begin():
        return await register_as_client(session, current_user, client_data)


@router.get("/me")
async def get_me(
    current_user: Annotated[UserSessionData, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    async with session.begin():
        return await get_me_from_db(session, current_user)