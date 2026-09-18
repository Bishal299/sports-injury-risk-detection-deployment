from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from typing import Optional

class AthleteCreate(BaseModel):
    sport: str | None = None
    position: str | None = None
    age: int | None = None
    height: float | None = None
    weight: float | None = None

    training_load: float | None = None
    flexibility: float | None = None
    strength: float | None = None
    balance: float | None = None
    endurance: float | None = None

    coach_notes: str | None = None


class AthleteRead(BaseModel):
    athlete_id: UUID
    user_id: UUID

    sport: str | None = None
    position: str | None = None
    age: int | None = None
    height: float | None = None
    weight: float | None = None

    training_load: float | None = None
    flexibility: float | None = None
    strength: float | None = None
    balance: float | None = None
    endurance: float | None = None

    coach_notes: str | None = None

    model_config = ConfigDict(from_attributes=True)





class AthleteUpdate(BaseModel):
    sport: Optional[str] = None
    position: Optional[str] = None
    age: Optional[int] = None
    height: Optional[float] = None
    weight: Optional[float] = None

    training_load: Optional[float] = None
    flexibility: Optional[float] = None
    strength: Optional[float] = None
    balance: Optional[float] = None
    endurance: Optional[float] = None

    coach_notes: Optional[str] = None


class AthleteRehabilitationActivityRead(BaseModel):
    activity_id: UUID
    rehabilitation_plan_id: UUID
    title: str
    description: str | None = None
    phase: str
    due_date: date | None = None
    priority: str
    status: str
    completed_at: datetime | None = None
    athlete_notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AthleteRehabilitationActivityUpdate(BaseModel):
    status: str
    athlete_notes: str | None = None


class AthleteRehabilitationPlanRead(BaseModel):
    rehabilitation_plan_id: UUID
    athlete_id: UUID
    physiotherapist_user_id: UUID
    physiotherapist_name: str | None = None
    title: str | None = None
    description: str | None = None
    current_phase: str
    start_date: date | None = None
    target_date: date | None = None
    goals: list[str] | None = None
    status: str
    notes: str | None = None
    progress_available: bool = False
    calculated_progress: float | None = None
    activities: list[AthleteRehabilitationActivityRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class AthleteCoachTaskRead(BaseModel):
    task_id: UUID
    coach_id: UUID
    athlete_id: UUID
    analysis_id: UUID | None = None
    video_id: UUID | None = None
    title: str
    description: str | None = None
    due_date: date | None = None
    priority: str
    status: str
    completed_at: datetime | None = None
    athlete_notes: str | None = None
    coach_name: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AthleteCoachTaskUpdate(BaseModel):
    status: str
    athlete_notes: str | None = None
