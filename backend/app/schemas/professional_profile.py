from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProfessionalProfileRole(str, Enum):
    COACH = "COACH"
    PHYSIOTHERAPIST = "PHYSIOTHERAPIST"
    SPORTS_SCIENTIST = "SPORTS_SCIENTIST"


class ProfessionalVerificationStatus(str, Enum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


class ProfessionalProfileBase(BaseModel):
    professional_role: ProfessionalProfileRole
    primary_sport: Optional[str] = Field(default=None, max_length=100)
    other_sports: Optional[str] = None
    years_of_experience: Optional[int] = Field(default=None, ge=0)
    specialization: Optional[str] = Field(default=None, max_length=255)
    organization: Optional[str] = Field(default=None, max_length=255)
    certifications: Optional[str] = None
    professional_bio: Optional[str] = None
    profile_photo_url: Optional[str] = None
    profile_completion: Optional[float] = Field(default=0, ge=0, le=100)


class ProfessionalProfileCreate(ProfessionalProfileBase):
    pass


class ProfessionalProfileUpdate(BaseModel):
    primary_sport: Optional[str] = Field(default=None, max_length=100)
    other_sports: Optional[str] = None
    years_of_experience: Optional[int] = Field(default=None, ge=0)
    specialization: Optional[str] = Field(default=None, max_length=255)
    organization: Optional[str] = Field(default=None, max_length=255)
    certifications: Optional[str] = None
    professional_bio: Optional[str] = None
    profile_photo_url: Optional[str] = None


class ProfessionalProfileResponse(ProfessionalProfileBase):
    professional_profile_id: UUID
    user_id: UUID
    verification_status: ProfessionalVerificationStatus
    profile_completion: float
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
