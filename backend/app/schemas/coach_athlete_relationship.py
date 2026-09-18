from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CoachAthleteRelationshipStatus(str, Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    REJECTED = "REJECTED"
    REVOKED = "REVOKED"


class CoachAthleteRelationshipCreate(BaseModel):
    coach_id: UUID
    athlete_id: UUID


class CoachAthleteRelationshipResponse(BaseModel):
    relationship_id: UUID
    coach_id: UUID
    athlete_id: UUID
    status: CoachAthleteRelationshipStatus
    requested_at: datetime
    responded_at: Optional[datetime] = None
    accepted_at: Optional[datetime] = None
    requested_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
