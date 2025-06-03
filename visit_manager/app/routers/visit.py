from fastapi import APIRouter, Depends, Body, HTTPException, Query, status
from pydantic import BaseModel, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Annotated, Any, List, Sequence
from uuid import UUID
import hashlib

from visit_manager.app.models.visit_models import CheckCodePayload, OpinionPayload, VisitRead
from visit_manager.services.visit_service import create_visit
from visit_manager.postgres_utils.models.models import Visit
from visit_manager.postgres_utils.utils import get_db
from visit_manager.kafka_utils.producer import KafkaProducerClient
from visit_manager.app.dependencies.auth import get_current_user, UserData
from visit_manager.postgres_utils.models.misc import VisitStatus

router = APIRouter(prefix="/visit", tags=["visit"])

@router.post(
    "/register_visit",
    summary="Register a new visit (called by Visit Scheduler)",
    status_code=201
)
async def register_visit(
    db: Annotated[AsyncSession, Depends(get_db)],
    payload: dict[str, Any] = Body(
        ...,
        example={
            "visit_id": "123e4567-e89b-12d3-a456-426614174000",
            "client_id": "98080c8d-8f49-4deb-b759-682b04af142b",
            "vendor_id": "98080c8d-8f49-4deb-b759-682b04af142b",
            "start_timestamp": "2025-06-05T10:00:00",
            "end_timestamp": "2025-06-05T11:00:00",
            "description": "Przykładowa wizyta",
            "service_type_id": "111e2222-e33b-44d3-a555-426614170999",
            "address_id": "222e3333-e44b-55d3-a666-426614171111",
            "status": "pending"
        }
    )
) -> dict[str, Any]:
    """
    Creates a new visit record in the database (data comes from Visit Scheduler).
    """
    await create_visit(payload)

    try:
        producer = KafkaProducerClient()
        producer.send_visit_registered(payload["visit_id"], payload)
    except NameError:
        pass

    return {"status": "ok", "visit_id": payload["visit_id"]}


@router.get(
    "/vendor/my_visits",
    response_model=List[VisitRead],
    summary="List all visits for a given vendor"
)
async def get_vendor_visits(
    current_user: Annotated[UserData, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
) -> Sequence[Visit]:
    """
    Returns all visits assigned to the authenticated vendor.
    Only accessible for users with the 'vendor' role.
    """
    if current_user.role != "vendor":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only for vendor")

    vendor_id = current_user.user_id

    async with db.begin():
        result = await db.execute(select(Visit).where(Visit.vendor_id == vendor_id))
        visits = result.scalars().all()
    return visits


@router.get(
    "/client/my_visits",
    response_model=List[VisitRead],
    summary="List all visits for a given client"
)
async def get_client_visits(
    current_user: Annotated[UserData, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
) -> Sequence[Visit]:
    """
    Returns all visits assigned to the authenticated client.
    Only accessible for users with the 'client' role.
    """
    if current_user.role != "client":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Dostęp tylko dla klienta")

    client_id = current_user.user_id
    async with db.begin():
        result = await db.execute(
            select(Visit).where(Visit.client_id == client_id)
        )
        visits = result.scalars().all()
    return visits


@router.get(
    "/get_visit_code/{visit_id}",
    summary="Generate a one-time visit code for a given visit"
)
async def get_visit_code(
    visit_id: UUID,
    current_user: Annotated[UserData, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, str]:
    """
    Generates a one-time visit code based on the visit ID.
    Returns the first 6 characters of the SHA-256 hash of the visit ID.
    Only accessible for the vendor who owns the visit.
    """
    if current_user.role != "vendor":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only for vendor")

    visit = await db.get(Visit, visit_id)
    if not visit or visit.vendor_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visit not found")

    code = hashlib.sha256(str(visit_id).encode()).hexdigest()[:6]
    return {"visit_code": code}


@router.post(
    "/check_visit_code",
    summary="Validate a visit code provided by the vendor"
)
async def check_visit_code(
    payload: CheckCodePayload,
    current_user: Annotated[UserData, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, bool]:
    """
    Checks if the provided visit code matches the generated one.
    Only accessible for the client assigned to the visit.
    """
    if current_user.role != "client":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only for client")

    visit = await db.get(Visit, payload.visit_id)
    if not visit or visit.client_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visit not found")

    expected = hashlib.sha256(str(payload.visit_id).encode()).hexdigest()[:6]
    valid = (payload.visit_code == expected)
    return {"valid": valid}


@router.post(
    "/add_opinion",
    summary="Add a review/opinion for a completed visit"
)
async def add_opinion(
    payload: OpinionPayload,
    current_user: Annotated[UserData, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """
    Adds a score (1–5) and optional comment to a completed visit.
    Only accessible for the client assigned to the visit.

    After saving the review:
    1. Recalculates the vendor’s average score.
    2. Sends a 'vendors.rating_updated' event to Kafka.
    """
    if current_user.role != "client":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only for client")

    visit = await db.get(Visit, payload.visit_id)
    if not visit or visit.client_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visit not found")
    
    if visit.status != VisitStatus.completed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Wizyta nie została zakończona")

    async with db.begin():
        visit.review_opinion_score = payload.score
        visit.review_comment = payload.comment

    async with db.begin():
        result = await db.execute(
            select(func.avg(Visit.review_opinion_score))
            .where(Visit.vendor_id == visit.vendor_id)
            .where(Visit.review_opinion_score.isnot(None))
        )
        new_avg = result.scalar_one() or 0.0

    try:
        producer = KafkaProducerClient()
        producer.send_vendor_rating_updated(str(visit.vendor_id), float(new_avg))
    except Exception:
        pass

    return {"status": "ok", "new_avg_score": new_avg}
