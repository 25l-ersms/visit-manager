from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str


class ChargeRequest(BaseModel):
    amount: int = Field(
        ..., ge=1, description="Kwota w najmniejszych jednostkach (dla PLN: grosze; np. 1000 = 10,00 PLN)"
    )
    currency: str = Field("pln", pattern="^[a-z]{3}$", description="Trzy-literowy kod waluty ISO (domyślnie 'pln')")


class ChargeResponse(BaseModel):
    charge_id: str
    status: str
    amount: int
    currency: str


class RefundResponse(BaseModel):
    refund_id: str
    status: str
    charge_refunded: str
