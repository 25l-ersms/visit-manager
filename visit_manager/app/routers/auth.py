import os
from fastapi import APIRouter, HTTPException, Depends
from google.oauth2 import id_token
from google.auth.transport import requests
from pydantic import BaseModel

router = APIRouter()

# Retrieve the Client ID and Secret from environment variables
CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
if not CLIENT_ID:
    raise RuntimeError("GOOGLE_CLIENT_ID environment variable is not set")

class Token(BaseModel):
    token: str

@router.post("/auth/google")
async def google_auth(token: Token):
    try:
        # Verify the token
        id_info = id_token.verify_oauth2_token(token.token, requests.Request(), CLIENT_ID)
        user_id = id_info["sub"]
        email = id_info["email"]
        return {"user_id": user_id, "email": email}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid token")