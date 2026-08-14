from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class InjuryHistoryCreate(BaseModel):
    injury_type: str | None = None
    body_part: str | None = None
    severity: str | None = None

    injury_date: date | None = None
    recovery_date: date | None = None

    remarks: str | None = None


class InjuryHistoryResponse(BaseModel):
    injury_id: UUID
    athlete_id: UUID

    injury_type: str | None = None
    body_part: str | None = None
    severity: str | None = None

    injury_date: date | None = None
    recovery_date: date | None = None

    remarks: str | None = None

    model_config = ConfigDict(from_attributes=True)