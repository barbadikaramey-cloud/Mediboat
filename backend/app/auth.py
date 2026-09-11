"""JWT authentication and demo-user management."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Annotated

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from app.config import Settings, get_settings

# ── Demo users (hashed passwords generated once at module load) ───────────────
# Passwords match the spec: the plain-text password equals the role name.
_PLAIN_PASSWORDS: dict[str, str] = {
    "dr.mehta":     "doctor",
    "nurse.priya":  "nurse",
    "billing.ravi": "billing_executive",
    "tech.anand":   "technician",
    "admin.sys":    "admin",
}


def _hash(plain: str) -> bytes:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt())


# Pre-hash at startup (acceptable for demo; in prod you'd pull from DB)
USERS: dict[str, dict] = {
    username: {"hashed_password": _hash(role), "role": role}
    for username, role in _PLAIN_PASSWORDS.items()
}


# ── Token models ──────────────────────────────────────────────────────────────
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: str
    role: str


# ── Helpers ───────────────────────────────────────────────────────────────────
def verify_password(plain: str, hashed: bytes) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed)


def authenticate_user(username: str, password: str) -> dict | None:
    user = USERS.get(username)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return user


def create_access_token(username: str, role: str, settings: Settings) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": username, "role": role, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


# ── FastAPI dependency ─────────────────────────────────────────────────────────
bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> TokenData:
    """Decode and validate JWT; return TokenData with username + role.

    **Role is extracted from the signed token only** — never from the request body.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        username: str = payload.get("sub", "")
        role: str = payload.get("role", "")
        if not username or not role:
            raise credentials_exception
        return TokenData(username=username, role=role)
    except JWTError:
        raise credentials_exception

