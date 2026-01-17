from pydantic import BaseModel, EmailStr
from typing import Optional


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Optional[dict] = None


class TokenData(BaseModel):
    user_id: Optional[str] = None
    email: Optional[str] = None


class RegisterResponse(BaseModel):
    user_id: str
    email: str
    role: str
    access_token: str
    token_type: str = "bearer"


class PasskeyRegisterBeginResponse(BaseModel):
    options: dict


class PasskeyRegisterCompleteRequest(BaseModel):
    credential: dict


class PasskeyRegisterCompleteResponse(BaseModel):
    success: bool
    credential_id: str


class PasskeyAuthBeginRequest(BaseModel):
    email: EmailStr


class PasskeyAuthBeginResponse(BaseModel):
    options: dict


class PasskeyAuthCompleteRequest(BaseModel):
    email: EmailStr
    credential: dict
