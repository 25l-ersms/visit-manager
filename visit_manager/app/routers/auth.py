import os
from fastapi import APIRouter, HTTPException, Depends
from google.oauth2 import id_token
from google.auth.transport import requests
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from jose import jwt

from visit_manager.postgres_utils.utils import get_db
from visit_manager.postgres_utils.models.users import get_or_create_user

router = APIRouter()

# Retrieve the Client ID and Secret from environment variables
CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
if not CLIENT_ID:
    raise RuntimeError("GOOGLE_CLIENT_ID environment variable is not set")

# Secret key for JWT
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

class Token(BaseModel):
    token: str

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@router.post("/auth/google")
async def google_auth(token: Token, db: AsyncSession = Depends(get_db)):
    try:
        # Verify the token
        id_info = id_token.verify_oauth2_token(token.token, requests.Request(), CLIENT_ID)
        email = id_info["email"]
        first_name = id_info.get("given_name", "")
        last_name = id_info.get("family_name", "")
        user = await get_or_create_user(db, email, first_name, last_name)

        # Determine user role
        if user.admin_profile:
            role = "admin"
        elif user.vendor_profile:
            role = "vendor"
        elif user.client_profile:
            role = "client"
        else:
            role = "user"

        # Issue JWT token
        access_token = create_access_token(
            data={"sub": str(user.user_id), "email": user.email, "role": role}
        )

        return {
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
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid token")