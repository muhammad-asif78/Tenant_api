from pydantic import BaseModel, EmailStr
from typing import Optional

class TenantBase(BaseModel):
    name: str

class TenantCreate(TenantBase):
    pass

class TenantUpdate(TenantBase):
    name: Optional[str] = None

class TenantInDBBase(TenantBase):
    id: int
    
    class Config:
        orm_mode = True

class Tenant(TenantInDBBase):
    pass