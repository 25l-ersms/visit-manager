from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from visit_manager.postgres_utils.models.models import Payment, PaymentStatus


async def add_payment(session: AsyncSession, payment: Payment) -> Payment:
    async with session.begin():
        session.add(payment)
    await session.refresh(payment)
    return payment


async def read_all_payments(session: AsyncSession) -> Sequence[Payment]:
    async with session.begin():
        result = await session.execute(select(Payment))
        payments = result.scalars().all()
        return payments


async def update_payment_status(
    session: AsyncSession,
    stripe_charge_id: str,
    status: PaymentStatus,
) -> Optional[Payment]:
    async with session.begin():
        result = await session.execute(select(Payment).where(Payment.stripe_charge_id == stripe_charge_id))
        payment = result.scalars().first()
        if not payment:
            return None
        payment.status = status
        return payment


async def get_payment_by_stripe_charge_id(session: AsyncSession, stripe_charge_id: str) -> Optional[Payment]:
    async with session.begin():
        result = await session.execute(select(Payment).where(Payment.stripe_charge_id == stripe_charge_id))
        return result.scalars().first()
