import os
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from google.auth.transport import requests
from google.oauth2 import id_token
from jose import jwt
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from visit_manager.app.models.visit_models import RegisterPayload, RegisterResponse
from visit_manager.kafka_utils.producer import KafkaProducerClient
from visit_manager.package_utils.logger_conf import logger
from visit_manager.postgres_utils.models.models import Client as ClientModel
from visit_manager.postgres_utils.models.models import User as UserModel
from visit_manager.postgres_utils.models.models import Vendor as VendorModel
from visit_manager.postgres_utils.models.users import get_or_create_user
from visit_manager.postgres_utils.utils import get_db

router = APIRouter(tags=["auth"])

# Retrieve the Client ID and Secret from environment variables
CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
if not CLIENT_ID:
    raise RuntimeError("GOOGLE_CLIENT_ID environment variable is not set")

# Secret key for JWT
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


class Token(BaseModel):
    token: str


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


@router.post("/auth/google")
async def google_auth(token: Token, db: Annotated[AsyncSession, Depends(get_db)]) -> Any:
    try:
        id_info = id_token.verify_oauth2_token(token.token, requests.Request(), CLIENT_ID)
        email = id_info["email"]
        first_name = id_info.get("given_name", "")
        last_name = id_info.get("family_name", "")
        user = await get_or_create_user(db, email, first_name, last_name)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid Google token")

    if user.vendor_profile or user.client_profile:
        role = "vendor" if user.vendor_profile else "client"
        access_token = create_access_token(data={"sub": str(user.user_id), "email": user.email, "role": role})
        return {
            "is_new": False,
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "user_id": str(user.user_id),
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": role,
            },
        }
    else:
        return {
            "is_new": True,
            "user_id": str(user.user_id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
        }


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Dokończ rejestrację: utwórz profil client/vendor i zwróć access_token",
)
async def register(
    payload: RegisterPayload,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Any:
    async with db.begin():
        user_obj = await db.get(UserModel, payload.user_id)
        if not user_obj:
            raise HTTPException(status_code=404, detail="User not found")

        if user_obj.vendor_profile or user_obj.client_profile:
            raise HTTPException(status_code=400, detail="User already has a profile")

        if payload.role == "client":
            client = ClientModel(
                client_id=payload.user_id,
                phone_number=payload.phone_number,
                is_active=True,
            )
            db.add(client)

            role = "client"

        else:  # payload.role == "vendor"
            if not payload.vendor_name or not payload.address_id:
                raise HTTPException(
                    status_code=422, detail="vendor_name i address_id muszą być podane dla roli 'vendor'"
                )

            vendor = VendorModel(
                vendor_id=payload.user_id,
                vendor_name=payload.vendor_name,
                address_id=payload.address_id,
                phone_number=payload.phone_number,
                is_active=True,
                required_deposit_gr=payload.required_deposit_gr,
            )
            db.add(vendor)

            role = "vendor"

    try:
        producer = KafkaProducerClient()
        producer.send_user_registered(str(payload.user_id), user_obj.email, role)
    except Exception as e:
        logger.error(f"Nie udało się wysłać 'users.registered' do Kafka: {e}")

    access_token = create_access_token(data={"sub": str(user_obj.user_id), "email": user_obj.email, "role": role})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "user_id": str(user_obj.user_id),
            "email": user_obj.email,
            "first_name": user_obj.first_name,
            "last_name": user_obj.last_name,
            "role": role,
        },
    }
