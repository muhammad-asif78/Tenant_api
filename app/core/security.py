# app/core/security.py
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User
from app.core.database import get_db

# Use HTTP Bearer for token extraction
security = HTTPBearer()


def _truncate_password_to_72(password: str) -> str:
    """Truncate a password to 72 bytes safely (UTF-8 aware).

    Bcrypt has a 72-byte limit. We encode to UTF-8, truncate bytes, then decode
    using 'ignore' to avoid breaking multibyte characters. This keeps behavior
    deterministic between hash and verify.
    """
    if password is None:
        raise ValueError("Password cannot be None")
    pw_bytes = password.encode("utf-8")[:72]
    return pw_bytes.decode("utf-8", errors="ignore")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not plain_password or not hashed_password:
        return False
    plain_trunc = _truncate_password_to_72(plain_password).encode("utf-8")
    hp = hashed_password.encode("utf-8") if isinstance(hashed_password, str) else hashed_password
    return bcrypt.checkpw(plain_trunc, hp)


def get_password_hash(password: str) -> str:
    pw = _truncate_password_to_72(password).encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pw, salt).decode("utf-8")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # Default to minutes configured in settings (fallback to 24h)
        minutes = getattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES", 1440)
        expire = datetime.utcnow() + timedelta(minutes=minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db),
) -> User:
    """Dependency that returns the current user and enforces tenant binding.

    The JWT must contain `sub` (email) and `tenant_id`. We verify the token,
    fetch the user from DB, and ensure the `tenant_id` in the token matches the
    user's tenant_id to prevent cross-tenant token reuse.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials
    try:
        payload = decode_access_token(token)
        email: Optional[str] = payload.get("sub")
        token_tenant_id: Optional[int] = payload.get("tenant_id")
        if email is None or token_tenant_id is None:
            raise credentials_exception
    except HTTPException:
        raise
    except Exception:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception

    if int(user.tenant_id) != int(token_tenant_id):
        # Token's tenant_id doesn't match the user's tenant -> invalid
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid tenant for token")

    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_active_superuser(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    return current_user