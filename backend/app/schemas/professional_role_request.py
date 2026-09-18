from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RequestedProfessionalRole(str, Enum):
    COACH = "COACH"
    PHYSIOTHERAPIST = "PHYSIOTHERAPIST"
    SPORTS_SCIENTIST = "SPORTS_SCIENTIST"


class ProfessionalRoleRequestStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ProfessionalRoleRequestBase(BaseModel):
    requested_role: RequestedProfessionalRole
    primary_sport: Optional[str] = Field(default=None, max_length=100)
    organization: Optional[str] = Field(default=None, max_length=255)
    specialization: Optional[str] = Field(default=None, max_length=255)
    years_of_experience: Optional[int] = Field(default=None, ge=0)
    certifications: Optional[str] = None
    professional_bio: Optional[str] = None
    supporting_document_url: Optional[str] = None


class ProfessionalRoleRequestCreate(ProfessionalRoleRequestBase):
    pass


class ProfessionalRoleRequestReview(BaseModel):
    status: ProfessionalRoleRequestStatus
    rejection_reason: Optional[str] = None


class ProfessionalRoleRequestReject(BaseModel):
    rejection_reason: Optional[str] = None


class ProfessionalRoleRequestResponse(ProfessionalRoleRequestBase):
    request_id: UUID
    user_id: UUID
    applicant_name: Optional[str] = None
    applicant_email: Optional[str] = None
    applicant_phone: Optional[str] = None
    status: ProfessionalRoleRequestStatus
    submitted_at: datetime
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[UUID] = None
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
