from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, ConfigDict

from app.models.user import UserRole


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.ATHLETE
    phone: str | None = None
    profile_image: str | None = None


class UserResponse(BaseModel):
    user_id: UUID
    name: str
    email: EmailStr
    role: UserRole
    phone: str | None = None
    profile_image: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str