import os
from typing import Annotated, Literal
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel

# Te same wartości, co w auth.py
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-key")
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/google")


class UserData(BaseModel):
    user_id: UUID
    email: str
    role: Literal["client", "vendor"]


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> UserData:
    """
    Dekoduje JWT i zwraca dane o użytkowniku (user_id, email, role).
    Jeśli token jest niepoprawny / przeterminowany → raise 401.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Nieprawidłowy lub przeterminowany token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        email = payload.get("email")
        role = payload.get("role")
        if sub is None or email is None or role is None:
            raise credentials_exception
        # Zamieniamy sub (string) na UUID
        user_id = UUID(sub)
    except (JWTError, ValueError):
        raise credentials_exception

    return UserData(user_id=user_id, email=email, role=role)
