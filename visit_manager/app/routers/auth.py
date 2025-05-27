import os
from datetime import timedelta
from typing import Annotated

import requests
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from visit_manager.app.models.user_models import UserCreate
from visit_manager.app.security.common import create_access_token, oauth
from visit_manager.postgres_utils.models.users import create_or_update_user
from visit_manager.postgres_utils.utils import get_db

router = APIRouter()


@router.get("/login")
async def login(request: Request):
    request.session.clear()
    frontend_url = os.getenv("FRONTEND_URL")
    redirect_url = os.getenv("REDIRECT_URL")
    request.session["login_redirect"] = frontend_url
    return await oauth.auth_demo.authorize_redirect(request, redirect_url, prompt="consent")


@router.get("/auth")
async def auth(request: Request, session: Annotated[AsyncSession, Depends(get_db)]):
    try:
        token = await oauth.auth_demo.authorize_access_token(request)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Google authentication failed: {str(e)}")

    try:
        user_info_endpoint = "https://www.googleapis.com/oauth2/v2/userinfo"
        headers = {"Authorization": f"Bearer {token['access_token']}"}
        google_response = requests.get(user_info_endpoint, headers=headers)
        user_info = google_response.json()
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Google userinfo failed: {str(e)}")

    user = token.get("userinfo")
    expires_in = token.get("expires_in")
    user_id = user.get("sub")
    iss = user.get("iss")
    user_email = user.get("email")

    user_name = user_info.get("name")

    if iss not in ["https://accounts.google.com", "accounts.google.com"]:
        raise HTTPException(status_code=401, detail="Google authentication failed.")

    if user_id is None:
        raise HTTPException(status_code=401, detail="Google authentication failed.")

    # Create JWT token
    access_token_expires = timedelta(seconds=expires_in)
    access_token = create_access_token(data={"sub": user_id, "email": user_email}, expires_delta=access_token_expires)

    async with session.begin():
        await create_or_update_user(session, UserCreate(email=user_email, full_name=user_name))

    redirect_url = request.session.pop("login_redirect", "")
    response = RedirectResponse(redirect_url)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,  # Set to False for HTTP, True for HTTPS
        samesite="lax",  # Changed from strict to lax for better compatibility
    )

    return response
