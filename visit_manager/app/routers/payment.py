import os
import stripe
from fastapi import APIRouter, HTTPException, status
from visit_manager.app.models import ChargeRequest, ChargeResponse, RefundResponse
from visit_manager.package_utils.logger_conf import logger
from visit_manager.postgres_utils.models.transaction import (
    Transaction,
    add_transaction,
    delete_transaction,
    delete_last_transaction,
)

router = APIRouter(
    prefix="/payment",
    tags=["payment"],
    responses={404: {"description": "Not found"}}
)

stripe.api_key = os.getenv("STRIPE_API_KEY")
if not stripe.api_key:
    logger.critical("STRIPE_API_KEY nie jest ustawiony!")
    raise RuntimeError("Brak STRIPE_API_KEY w środowisku")


@router.post("/charge", response_model=ChargeResponse, status_code=status.HTTP_201_CREATED)
async def create_charge(req: ChargeRequest):
    """
    Tworzy testową opłatę na Stripe (tok_visa) i dodaje ją do pliku.
    """
    try:
        charge = stripe.Charge.create(
            amount=req.amount,
            currency=req.currency,
            source="tok_visa",
        )
    except stripe.error.StripeError as e:
        detail = getattr(e, "user_message", None) or str(e)
        raise HTTPException(status_code=400, detail=detail)

    add_transaction(tx_id=charge.id, amount=charge.amount, currency=charge.currency)

    return ChargeResponse(
        charge_id=charge.id,
        status=charge.status,
        amount=charge.amount,
        currency=charge.currency,
    )


@router.delete("/charge/last", response_model=RefundResponse)
async def refund_last():
    """
    Refunduje i usuwa ostatnią transakcję z pliku.
    """
    try:
        last: Transaction = delete_last_transaction()
    except IndexError:
        raise HTTPException(status_code=404, detail="Brak transakcji do zwrotu")

    try:
        refund = stripe.Refund.create(charge=last.id)
    except stripe.error.StripeError as e:
        detail = getattr(e, "user_message", None) or str(e)
        add_transaction(tx_id=last.id, amount=last.amount, currency=last.currency)
        raise HTTPException(status_code=400, detail=detail)

    return RefundResponse(
        refund_id=refund.id,
        status=refund.status,
        charge_refunded=last.id,
    )


@router.delete("/charge/{charge_id}", response_model=RefundResponse)
async def refund_by_id(charge_id: str):
    """
    Refunduje i usuwa transakcję o konkretnym ID.
    """
    try:
        delete_transaction(tx_id=charge_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Transakcja {charge_id} nie znaleziona")

    try:
        refund = stripe.Refund.create(charge=charge_id)
    except stripe.error.StripeError as e:
        detail = getattr(e, "user_message", None) or str(e)
        raise HTTPException(status_code=400, detail=detail)

    return RefundResponse(
        refund_id=refund.id,
        status=refund.status,
        charge_refunded=charge_id,
    )