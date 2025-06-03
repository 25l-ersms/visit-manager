from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, EmailStr
from typing import Any, Optional, Literal

from visit_manager.postgres_utils.models.misc import VisitStatus

class Token(BaseModel):
    token: str


class GoogleAuthResponse(BaseModel):
    is_new: bool
    access_token: Optional[str]
    token_type: Optional[str]
    user: Optional[dict[str, Any]]
    user_id: Optional[str]

    email: Optional[EmailStr]
    first_name: Optional[str]
    last_name: Optional[str]


class RegisterPayload(BaseModel):
    user_id: UUID = Field(..., description="UUID użytkownika zwrócony przez /auth/google")
    role: Literal["client", "vendor"] = Field(..., description="Rola (client lub vendor)")
    phone_number: str = Field(..., description="Numer telefonu w formacie E.164 lub podobnym")
    vendor_name: Optional[str] = Field(None, description="Nazwa vendor'a (tylko, jeśli role='vendor')")
    address_id: Optional[UUID] = Field(
        None, description="UUID istniejącego Address (tylko, jeśli role='vendor')"
    )
    required_deposit_gr: Optional[int] = Field(
        None, description="Wymagany depozyt w gramach (opcjonalne, tylko dla vendor)"
    )


class RegisterResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict[str, Any]


class CheckCodePayload(BaseModel):
    visit_id: UUID
    visit_code: str


class OpinionPayload(BaseModel):
    visit_id: UUID
    score: int
    comment: str | None = None

    @field_validator("score")
    @classmethod
    def score_in_range(cls, v: int) -> int:
        if v < 1 or v > 5:
            raise ValueError("Score must be between 1 and 5")
        return v


class VisitRead(BaseModel):
    visit_id: UUID
    client_id: UUID
    vendor_id: UUID
    start_timestamp: datetime
    end_timestamp: datetime
    description: str
    service_type_id: UUID
    address_id: UUID
    status: VisitStatus

    class Config:
        orm_mode = True