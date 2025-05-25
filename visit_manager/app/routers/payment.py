import os
from typing import Annotated, Any, Sequence

import stripe
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from stripe.error import StripeError  # type: ignore[attr-defined]

from visit_manager.app.models.payment_models import ChargeRequest, ChargeResponse, RefundResponse
from visit_manager.app.models.user_models import UserSessionData
from visit_manager.app.security.common import get_current_user
from visit_manager.package_utils.logger_conf import logger
from visit_manager.postgres_utils.models.models import Payment, PaymentStatus
from visit_manager.postgres_utils.models.transaction import (
    add_payment,
    get_payment_by_stripe_charge_id,
    read_all_payments,
    update_payment_status,
)
from visit_manager.postgres_utils.utils import get_db

router = APIRouter(prefix="/payment", tags=["payment"])


async def get_stripe_client() -> Any:
    """
    Dependency that provides an async Stripe client.
    Raises 500 if API key not configured.
    """
    api_key = os.getenv("STRIPE_API_KEY")
    if not api_key:
        logger.warning("STRIPE_API_KEY is not set; payment endpoints will return 500 at runtime")
        raise HTTPException(status_code=500, detail="Stripe API key not configured")
    stripe.api_key = api_key
    return stripe


@router.post("/charge", status_code=status.HTTP_201_CREATED)
async def create_charge(
    req: ChargeRequest,
    stripe_client: Annotated[Any, Depends(get_stripe_client)],
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[UserSessionData, Depends(get_current_user)],
) -> ChargeResponse:
    """
    Creates a charge using Stripe API and stores the transaction in the database.
    If the charge creation fails, raises 400 with the error message.
    """
    charge = await stripe_client.Charge.create_async(
        amount=req.amount,
        currency=req.currency,
        source="tok_visa",
    )
    payment = await add_payment(
        session=session,
        payment=Payment(
            stripe_charge_id=charge.id,
            amount=req.amount,
            currency=req.currency,
            status=PaymentStatus.succeeded,
        ),
    )
    return ChargeResponse(
        charge_id=charge.id,
        status=charge.status,
        amount=req.amount,
        currency=req.currency,
        transaction_timestamp=payment.transaction_timestamp,
    )


@router.post(
    "/refund/last",
    status_code=status.HTTP_200_OK,
    summary="Refund the most recent charge",
    description="Issues a refund for the most recent successful charge.",
)
async def refund_last_charge(
    stripe_client: Annotated[Any, Depends(get_stripe_client)],
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[UserSessionData, Depends(get_current_user)],
) -> RefundResponse:
    """
    Issues a refund for the most recent successful charge.
    Raises:
        HTTPException(404): when there is no transactions in database.
        HTTPException(400): when last transaction has a different status than "success" or Stripe returned error when refunding.
    """
    payments = await read_all_payments(session)
    if not payments:
        print("No transactions found to refund")
        raise HTTPException(status_code=404, detail="No transactions found to refund")
    last_payment = payments[-1]
    charge_id = last_payment.stripe_charge_id
    if last_payment.status != PaymentStatus.succeeded:
        raise HTTPException(status_code=400, detail=f"Transaction {charge_id} is not eligible for refund")
    try:
        refund = await stripe_client.Refund.create_async(charge=charge_id)
    except StripeError as e:
        detail = getattr(e, "user_message", None) or str(e)
        logger.error(f"Stripe refund error for {charge_id}: {detail}")
        raise HTTPException(status_code=400, detail=detail)
    await update_payment_status(session=session, stripe_charge_id=charge_id, status=PaymentStatus.refunded)
    return RefundResponse(
        charge_id=charge_id,
        status=refund.status,
        refund_id=refund.id,
        charge_refunded=True,
    )


@router.post("/refund/{charge_id}", status_code=status.HTTP_200_OK)
async def refund_charge(
    charge_id: str,
    stripe_client: Annotated[Any, Depends(get_stripe_client)],
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[UserSessionData, Depends(get_current_user)],
) -> RefundResponse:
    """
    Issues a refund for the given charge and updates its status.
    If refund fails, transaction status is NOT updated to preserve consistency.
    If the transaction is not found or is not eligible for refund, raises 404 or 400.
    """
    payment = await get_payment_by_stripe_charge_id(session=session, stripe_charge_id=charge_id)
    if not payment:
        raise HTTPException(status_code=404, detail=f"Transaction {charge_id} not found")
    if payment.status != PaymentStatus.succeeded:
        raise HTTPException(status_code=400, detail=f"Transaction {charge_id} is not eligible for refund")
    try:
        refund = await stripe_client.Refund.create_async(charge=charge_id)
    except StripeError as e:
        detail = getattr(e, "user_message", None) or str(e)
        raise HTTPException(status_code=400, detail=detail)
    await update_payment_status(session=session, stripe_charge_id=charge_id, status=PaymentStatus.refunded)
    return RefundResponse(
        charge_id=charge_id,
        status=refund.status,
        refund_id=refund.id,
        charge_refunded=True,
    )


@router.get(
    "/charges",
    status_code=status.HTTP_200_OK,
    summary="List all charges",
    description="Returns a list of all charges made through the system.",
    dependencies=[Depends(get_current_user)],
)
async def list_charges(session: Annotated[AsyncSession, Depends(get_db)]) -> Sequence[ChargeResponse]:
    """
    Returns a list of all charges made through the system.
    Each charge is represented by a ChargeResponse object.
    """
    payments = await read_all_payments(session)
    return [
        ChargeResponse(
            charge_id=p.stripe_charge_id,
            status=p.status,
            amount=p.amount,
            currency=p.currency,
            transaction_timestamp=p.transaction_timestamp,
        )
        for p in payments
    ]
