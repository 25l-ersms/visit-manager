from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, EmailStr, Field

from visit_manager.postgres_utils.models.models import PaymentStatus


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
