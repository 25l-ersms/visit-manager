from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field

from visit_manager.postgres_utils.models.models import PaymentStatus

class ChargeRequest(BaseModel):
    amount: int = Field(..., ge=1, description="Amount in smallest currency unit (grosze; 1000 = 10.00 PLN)")
    currency: Annotated[
        str,
        Field(min_length=3, max_length=3, pattern=r"^[a-z]{3}$")
    ] = "pln"


class ChargeResponse(BaseModel):
    charge_id: str = Field(..., examples=["ch_1N2x3AbCdEfGhIjKlMnOpQrS"], description="Unikalny ID charge’a")
    status: PaymentStatus
    amount: int = Field(..., examples=[1000], description="Amount in smallest currency unit (grosze; 1000 = 10.00 PLN)")
    currency: str = Field(..., examples=["pln"], description="Currency code ISO-4217")
    transaction_timestamp: datetime = Field(..., description="Transaction timestamp")


class RefundResponse(BaseModel):
    refund_id: str = Field(..., examples=["re_1N2x3AbCdEfGhIjKlMnOpQrS"])
    charge_id: str = Field(..., examples=["ch_1N2x3AbCdEfGhIjKlMnOpQrS"])
    status: PaymentStatus
    charge_refunded: bool = Field(..., description="Whether the charge was refunded")
