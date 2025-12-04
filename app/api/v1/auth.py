# app/api/v1/auth.py
from datetime import timedelta
from typing import Optional
from pydantic import BaseModel, EmailStr, Field

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core import security
from app.api.deps import get_current_active_user
from app.core.database import get_db
from app.core.config import settings
from app.schemas.token import Token
from app.models.user import User
from app.models.tenant import Tenant

router = APIRouter(prefix="/auth", tags=["Authentication"])

def create_tenant(db: Session, name: str):
    db_tenant = db.query(Tenant).filter(Tenant.name == name).first()
    if db_tenant:
        return db_tenant
    db_tenant = Tenant(name=name)
    db.add(db_tenant)
    db.commit()
    db.refresh(db_tenant)
    return db_tenant

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(..., min_length=8)
    tenant_name: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = db.query(User).filter(User.email == email).first()
    if not user or not security.verify_password(password, user.hashed_password):
        return None
    return user

@router.post("/login", response_model=Token)
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Get access token by providing email and password
    """
    user = authenticate_user(db, email=request.email, password=request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.email, "tenant_id": user.tenant_id},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(
    user_in: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new user account
    """
    # Check if user already exists
    db_user = db.query(User).filter(User.email == user_in.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create or get tenant
    tenant = create_tenant(db, user_in.tenant_name)
    
    # Create new user
    hashed_password = security.get_password_hash(user_in.password)

    # Determine role: if there are no users in the DB yet, make this first user an admin
    existing_users = db.query(User).count()
    role = "admin" if existing_users == 0 else "user"
    is_super = True if role == "admin" else False

    db_user = User(
        name=user_in.name,
        email=user_in.email,
        hashed_password=hashed_password,
        tenant_id=tenant.id,
        role=role,
        is_superuser=is_super,
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Do NOT return token on signup; require explicit login
    return {"message": "User created successfully"}

@router.get("/me")
async def read_users_me(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user information
    """
    return current_user