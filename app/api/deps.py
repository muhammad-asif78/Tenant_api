from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    get_current_user as _get_current_user,
    get_current_active_user as _get_current_active_user,
    get_current_active_superuser as _get_current_active_superuser,
)


def get_db_session() -> Annotated[Session, Depends(get_db)]:
    return Depends(get_db)


async def get_current_user(current_user=Depends(_get_current_user)):
    return current_user


async def get_current_active_user(current_user=Depends(_get_current_active_user)):
    return current_user


async def get_current_active_superuser(current_user=Depends(_get_current_active_superuser)):
    return current_user
