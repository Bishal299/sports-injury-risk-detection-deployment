from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CoachVerificationStatus(str, Enum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


class CoachProfileBase(BaseModel):
    primary_sport: Optional[str] = Field(default=None, max_length=100)
    other_sports: Optional[str] = None
    years_of_experience: Optional[int] = Field(default=None, ge=0)
    coaching_specialization: Optional[str] = Field(default=None, max_length=255)
    organization: Optional[str] = Field(default=None, max_length=255)
    certifications: Optional[str] = None
    professional_bio: Optional[str] = None
    profile_photo_url: Optional[str] = None
    profile_completion: Optional[float] = Field(default=0, ge=0, le=100)


class CoachProfileCreate(CoachProfileBase):
    pass


class CoachProfileUpdate(BaseModel):
    primary_sport: Optional[str] = Field(default=None, max_length=100)
    other_sports: Optional[str] = None
    years_of_experience: Optional[int] = Field(default=None, ge=0)
    coaching_specialization: Optional[str] = Field(default=None, max_length=255)
    organization: Optional[str] = Field(default=None, max_length=255)
    certifications: Optional[str] = None
    professional_bio: Optional[str] = None
    profile_photo_url: Optional[str] = None


class CoachProfileResponse(CoachProfileBase):
    coach_id: UUID
    user_id: UUID
    verification_status: CoachVerificationStatus
    profile_completion: float
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
