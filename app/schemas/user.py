# app/schemas/user.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    is_active: bool = True
    is_superuser: bool = False

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    tenant_id: int

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8)
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None

class UserInDBBase(UserBase):
    id: int
    tenant_id: int

    class Config:
        orm_mode = True

class User(UserInDBBase):
    pass

class UserInDB(UserInDBBase):
    hashed_password: str