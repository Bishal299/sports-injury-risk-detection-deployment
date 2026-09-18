from datetime import date, datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RehabilitationPlanBase(BaseModel):
    injury_context: Optional[str] = None
    start_date: Optional[date] = None
    target_date: Optional[date] = None
    current_phase: str = "ASSESSMENT"
    progress: float = Field(default=0, ge=0, le=100)
    goals: Optional[list[str]] = None
    completed_activities: Optional[list[str]] = None
    pending_activities: Optional[list[str]] = None
    recent_assessment: Optional[str] = None
    status: str = "ACTIVE"
    notes: Optional[str] = None


class RehabilitationPlanCreate(RehabilitationPlanBase):
    pass


class RehabilitationPlanUpdate(BaseModel):
    injury_context: Optional[str] = None
    start_date: Optional[date] = None
    target_date: Optional[date] = None
    current_phase: Optional[str] = None
    progress: Optional[float] = Field(default=None, ge=0, le=100)
    goals: Optional[list[str]] = None
    completed_activities: Optional[list[str]] = None
    pending_activities: Optional[list[str]] = None
    recent_assessment: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class RehabilitationActivityBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    phase: str = "ASSESSMENT"
    due_date: Optional[date] = None
    priority: str = "MEDIUM"
    status: str = "PENDING"


class RehabilitationActivityCreate(RehabilitationActivityBase):
    pass


class RehabilitationActivityUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    phase: Optional[str] = None
    due_date: Optional[date] = None
    priority: Optional[str] = None
    status: Optional[str] = None


class AthleteActivityStatusUpdate(BaseModel):
    status: str
    athlete_notes: Optional[str] = None


class RehabilitationActivityResponse(BaseModel):
    activity_id: UUID
    rehabilitation_plan_id: UUID
    title: str
    description: Optional[str] = None
    phase: str
    due_date: Optional[date] = None
    priority: str
    status: str
    completed_at: Optional[datetime] = None
    athlete_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RehabilitationPlanResponse(RehabilitationPlanBase):
    rehabilitation_plan_id: UUID
    athlete_id: UUID
    physiotherapist_user_id: UUID
    progress_available: bool = False
    calculated_progress: Optional[float] = None
    activities: list[RehabilitationActivityResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PhysiotherapistNoteCreate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=255)
    note: str = Field(min_length=1)


class PhysiotherapistNoteResponse(BaseModel):
    note_id: UUID
    athlete_id: UUID
    physiotherapist_user_id: UUID
    title: Optional[str] = None
    note: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PhysiotherapistRelationshipResponse(BaseModel):
    relationship_id: UUID
    professional_user_id: UUID
    athlete_id: UUID
    professional_role: str
    status: str
    requested_at: datetime
    responded_at: Optional[datetime] = None
    accepted_at: Optional[datetime] = None
    requested_by: Optional[UUID] = None
    requested_by_name: Optional[str] = None
    requested_by_role: Optional[str] = None
    professional_name: Optional[str] = None
    professional_email: Optional[str] = None
    physiotherapist_name: Optional[str] = None
    physiotherapist_email: Optional[str] = None
    primary_sport: Optional[str] = None
    years_of_experience: Optional[int] = None
    specialization: Optional[str] = None
    organization: Optional[str] = None
    certifications: Optional[str] = None
    professional_bio: Optional[str] = None
    athlete_name: Optional[str] = None
    athlete_sport: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PhysiotherapistDiscoveryItem(BaseModel):
    athlete_id: UUID
    name: str
    sport: Optional[str] = None
    age: Optional[int] = None
    availability: str
    latest_risk_score: Optional[float] = None
    risk_category: str
    connection_status: str
    latest_activity_at: Optional[datetime] = None


class PhysiotherapistAthleteItem(BaseModel):
    relationship_id: UUID
    athlete_id: UUID
    name: str
    sport: Optional[str] = None
    current_risk_score: Optional[float] = None
    risk_category: str
    previous_risk_score: Optional[float] = None
    risk_trend: str
    latest_analysis_at: Optional[datetime] = None
    latest_analysis_id: Optional[UUID] = None
    latest_video_id: Optional[UUID] = None
    recovery_progress: Optional[float] = None
    rehabilitation_status: str
    current_phase: Optional[str] = None
    needs_attention: bool = False


class MovementComparisonResponse(BaseModel):
    initial_assessment: Optional[dict[str, Any]] = None
    latest_assessment: Optional[dict[str, Any]] = None
    comparison: dict[str, Any] = Field(default_factory=dict)
    comparison_status: str = "Not Available"


class PhysiotherapistDashboardResponse(BaseModel):
    physiotherapist_user_id: UUID
    verification_status: str
    stats: dict[str, int]
    athletes: list[PhysiotherapistAthleteItem] = Field(default_factory=list)
    attention: list[dict[str, Any]] = Field(default_factory=list)


class PhysiotherapistAthleteDetailResponse(BaseModel):
    profile: dict[str, Any]
    risk_monitoring: dict[str, Any]
    rehabilitation_plan: Optional[RehabilitationPlanResponse] = None
    rehabilitation_monitoring: dict[str, Any] = Field(default_factory=dict)
    needs_attention: list[dict[str, Any]] = Field(default_factory=list)
    movement_comparison: MovementComparisonResponse
    latest_analysis: Optional[dict[str, Any]] = None
    videos: list[dict[str, Any]] = Field(default_factory=list)
    analyses: list[dict[str, Any]] = Field(default_factory=list)
    notes: list[PhysiotherapistNoteResponse] = Field(default_factory=list)
    timeline: list[dict[str, Any]] = Field(default_factory=list)
