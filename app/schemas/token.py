from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: str | None = None
    tenant_id: int | None = None

class UserLogin(BaseModel):
    email: str
    password: str
