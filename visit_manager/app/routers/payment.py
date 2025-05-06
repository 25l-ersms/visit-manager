import os

import stripe
from fastapi import APIRouter, HTTPException, status
from stripe.error import StripeError  # type: ignore[attr-defined]

from visit_manager.app.models import ChargeRequest, ChargeResponse, RefundResponse
from visit_manager.package_utils.logger_conf import logger
from visit_manager.postgres_utils.models.transaction import (
    FILE_PATH,
    Transaction,
    add_transaction,
    delete_last_transaction,
    delete_transaction,
)

router = APIRouter(prefix="/payment", tags=["payment"], responses={404: {"description": "Not found"}})

stripe_api_key = os.getenv("STRIPE_API_KEY")
if stripe_api_key:
    stripe.api_key = stripe_api_key
else:
    logger.warning("STRIPE_API_KEY is not set; payment endpoints will return 500 at runtime")


@router.post("/charge", status_code=status.HTTP_201_CREATED)
async def create_charge(req: ChargeRequest) -> ChargeResponse:
    """
    Tworzy testową opłatę na Stripe (tok_visa) i dodaje ją do pliku.
    """
    if not stripe.api_key:
        raise HTTPException(status_code=500, detail="Stripe API key not configured")

    try:
        charge = stripe.Charge.create(
            amount=req.amount,
            currency=req.currency,
            source="tok_visa",
        )
    except StripeError as e:
        detail = e.user_message or str(e)
        raise HTTPException(status_code=400, detail=detail)

    add_transaction(tx_id=charge.id, amount=charge.amount, currency=charge.currency, path=FILE_PATH)

    return ChargeResponse(
        charge_id=charge.id,
        status=charge.status or "unknown",
        amount=charge.amount,
        currency=charge.currency,
    )


@router.delete("/charge/last")
async def refund_last() -> RefundResponse:
    """
    Refunduje i usuwa ostatnią transakcję z pliku.
    """
    if not stripe.api_key:
        raise HTTPException(status_code=500, detail="Stripe API key not configured")

    try:
        last: Transaction = delete_last_transaction()
    except IndexError:
        raise HTTPException(status_code=404, detail="Brak transakcji do zwrotu")

    try:
        refund = stripe.Refund.create(charge=last.id)
    except StripeError as e:
        add_transaction(tx_id=last.id, amount=last.amount, currency=last.currency, path=FILE_PATH)
        detail = e.user_message or str(e)
        raise HTTPException(status_code=400, detail=detail)

    return RefundResponse(
        refund_id=refund.id,
        status=refund.status or "unknown",
        charge_refunded=last.id,
    )


@router.delete("/charge/{charge_id}")
async def refund_by_id(charge_id: str) -> RefundResponse:
    """
    Refunduje i usuwa transakcję o konkretnym ID.
    """
    if not stripe.api_key:
        raise HTTPException(status_code=500, detail="Stripe API key not configured")

    try:
        delete_transaction(tx_id=charge_id, path=FILE_PATH)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Transakcja {charge_id} nie znaleziona")

    try:
        refund = stripe.Refund.create(charge=charge_id)
    except StripeError as e:
        detail = getattr(e, "user_message", None) or str(e)
        raise HTTPException(status_code=400, detail=detail)

    return RefundResponse(
        refund_id=refund.id,
        status=refund.status or "unknown",
        charge_refunded=charge_id,
    )
