from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ProfessionalAthleteRelationshipRole(str, Enum):
    COACH = "COACH"
    PHYSIOTHERAPIST = "PHYSIOTHERAPIST"
    SPORTS_SCIENTIST = "SPORTS_SCIENTIST"


class ProfessionalAthleteRelationshipStatus(str, Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    REJECTED = "REJECTED"
    REVOKED = "REVOKED"


class ProfessionalAthleteRelationshipCreate(BaseModel):
    athlete_id: UUID
    professional_role: ProfessionalAthleteRelationshipRole


class ProfessionalAthleteRelationshipResponse(BaseModel):
    relationship_id: UUID
    professional_user_id: UUID
    athlete_id: UUID
    professional_role: ProfessionalAthleteRelationshipRole
    status: ProfessionalAthleteRelationshipStatus
    requested_by: Optional[UUID] = None
    requested_at: datetime
    responded_at: Optional[datetime] = None
    accepted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
