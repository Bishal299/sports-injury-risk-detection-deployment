from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, ConfigDict, Field

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


class AdminUserSummary(BaseModel):
    user_id: UUID
    name: str
    email: EmailStr
    role: UserRole
    status: str
    created_at: datetime
    professional_status: str | None = None


class AdminUserListResponse(BaseModel):
    users: list[AdminUserSummary]
    total: int
    limit: int
    offset: int
    supported_statuses: list[str] = Field(default_factory=lambda: ["ACTIVE"])


class AdminUserDetail(AdminUserSummary):
    phone: str | None = None
    profile_image: str | None = None
    athlete_profile: dict | None = None
    professional_profiles: list[dict] = Field(default_factory=list)
    professional_requests: list[dict] = Field(default_factory=list)


class AdminCreateAdministrator(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8)
    confirm_password: str = Field(min_length=8)


class AdminSelfProfileResponse(BaseModel):
    user_id: UUID
    name: str
    email: EmailStr
    role: UserRole
    phone: str | None = None
    profile_image: str | None = None
    created_at: datetime
    status: str
    last_login: datetime | None = None
    has_local_password: bool


class AdminSelfProfileUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    phone: str | None = Field(default=None, max_length=30)
    profile_image: str | None = None


class AdminPasswordChange(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8)
    confirm_password: str = Field(min_length=8)


class UserUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    profile_image: str | None = None



class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse | None = None


class AuthMeResponse(BaseModel):
    id: str
    user_id: str
    name: str
    email: EmailStr
    role: str
    phone: str | None = None
    profile_image: str | None = None


class GoogleLoginRequest(BaseModel):
    credential: str


class VerifyPortalRequest(BaseModel):
    portal_role: str


class VerifyPortalResponse(BaseModel):
    authorized: bool
    portal_role: str
    user_role: str
    headline: str | None = None
    message: str | None = None
    secondary_message: str | None = None
    default_route: str
    can_continue_as_athlete: bool = False
    request_role_url: str | None = None
