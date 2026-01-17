from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class PasskeyCredential(BaseModel):
    credential_id: str
    public_key: str
    sign_count: int
    created_at: datetime = Field(default_factory=datetime.utcnow)


class UserBase(BaseModel):
    email: EmailStr
    display_name: str
    role: str = Field(pattern="^(candidate|recruiter)$")


class UserCreate(UserBase):
    password: str = Field(min_length=8)


class User(UserBase):
    user_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    skill_vector: Optional[list[float]] = None
    archetype: Optional[str] = None
    integrity_score: Optional[float] = None
    avatar_url: Optional[str] = None


class UserInDB(UserBase):
    id: str = Field(alias="_id")
    password_hash: str
    created_at: datetime
    passkey_credentials: list[PasskeyCredential] = []
    skill_vector: Optional[list[float]] = None
    archetype: Optional[str] = None
    integrity_score: Optional[float] = None
    avatar_url: Optional[str] = None

    class Config:
        populate_by_name = True
