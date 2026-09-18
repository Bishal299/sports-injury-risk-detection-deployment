from datetime import date, datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AffectedSide(str, Enum):
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    BILATERAL = "BILATERAL"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class InjurySeverity(str, Enum):
    MILD = "MILD"
    MODERATE = "MODERATE"
    SEVERE = "SEVERE"


class InjuryStatus(str, Enum):
    ACTIVE = "ACTIVE"
    RECOVERED = "RECOVERED"
    CHRONIC = "CHRONIC"
    UNKNOWN = "UNKNOWN"


class InjuryHistoryBase(BaseModel):
    injury_type: Optional[str] = Field(default=None, min_length=1, max_length=100)
    body_part: Optional[str] = Field(default=None, min_length=1, max_length=100)
    affected_side: Optional[AffectedSide] = AffectedSide.NOT_APPLICABLE
    severity: Optional[InjurySeverity] = None
    status: Optional[InjuryStatus] = InjuryStatus.UNKNOWN
    injury_date: Optional[date] = None
    recovery_date: Optional[date] = None
    remarks: Optional[str] = None

    @model_validator(mode="after")
    def validate_dates_and_status(self):
        if self.recovery_date and self.injury_date and self.recovery_date < self.injury_date:
            raise ValueError("recovery_date cannot be earlier than injury_date")

        if self.status == InjuryStatus.ACTIVE and self.recovery_date is not None:
            raise ValueError("recovery_date should be empty for ACTIVE injuries")

        return self


class InjuryHistoryCreate(InjuryHistoryBase):
    injury_type: str = Field(min_length=1, max_length=100)
    body_part: str = Field(min_length=1, max_length=100)
    severity: InjurySeverity
    status: InjuryStatus = InjuryStatus.UNKNOWN
    injury_date: date


class InjuryHistoryUpdate(InjuryHistoryBase):
    pass


class InjuryHistoryResponse(BaseModel):
    injury_id: UUID
    athlete_id: UUID

    injury_type: str
    body_part: str
    affected_side: AffectedSide
    severity: InjurySeverity
    status: InjuryStatus

    injury_date: date
    recovery_date: Optional[date] = None

    remarks: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
