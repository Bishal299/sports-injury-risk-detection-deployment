from datetime import date, datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AthleteDiscoveryItem(BaseModel):
    athlete_id: UUID
    name: str
    sport: Optional[str] = None
    age: Optional[int] = None
    availability: str
    latest_risk_score: Optional[float] = None
    risk_category: str
    connection_status: str
    latest_activity_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class CoachRelationshipResponse(BaseModel):
    relationship_id: UUID
    coach_id: UUID
    athlete_id: UUID
    status: str
    requested_at: datetime
    responded_at: Optional[datetime] = None
    accepted_at: Optional[datetime] = None
    requested_by: Optional[UUID] = None

    coach_name: Optional[str] = None
    coach_email: Optional[str] = None
    primary_sport: Optional[str] = None
    years_of_experience: Optional[int] = None
    coaching_specialization: Optional[str] = None
    organization: Optional[str] = None
    certifications: Optional[str] = None
    professional_bio: Optional[str] = None

    athlete_name: Optional[str] = None
    athlete_sport: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CoachPrivateAthleteProfile(BaseModel):
    athlete_id: UUID
    user_id: UUID
    name: str
    email: str
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
    latest_risk_score: Optional[float] = None
    risk_category: str

    model_config = ConfigDict(from_attributes=True)


class CoachConnectedAthleteItem(BaseModel):
    relationship_id: UUID
    athlete_id: UUID
    name: str
    sport: Optional[str] = None
    status: str
    latest_risk_score: Optional[float] = None
    risk_category: str
    last_analysis_at: Optional[datetime] = None
    latest_activity_at: Optional[datetime] = None
    video_count: int = 0
    analysis_count: int = 0


class CoachDashboardAlert(BaseModel):
    athlete_id: UUID
    athlete_name: str
    type: str
    title: str
    detail: str
    severity: str
    created_at: Optional[datetime] = None


class CoachDashboardResponse(BaseModel):
    coach_id: UUID
    verification_status: str
    stats: dict
    attention: list[CoachDashboardAlert] = Field(default_factory=list)
    athletes: list[CoachConnectedAthleteItem] = Field(default_factory=list)
    recent_analyses: list[dict[str, Any]] = Field(default_factory=list)
    total_recent_analyses: int = 0
    performance_trends: list[dict[str, Any]] = Field(default_factory=list)
    requests_summary: Optional[dict[str, Any]] = None
    tasks_summary: Optional[dict[str, Any]] = None


class CoachAthleteVideoItem(BaseModel):
    video_id: UUID
    activity: Optional[str] = None
    video_url: Optional[str] = None
    uploaded_at: Optional[datetime] = None
    processing_status: Optional[str] = None
    duration: Optional[float] = None
    fps: Optional[int] = None
    resolution: Optional[str] = None
    latest_analysis_id: Optional[UUID] = None
    latest_risk_score: Optional[float] = None
    risk_category: str
    analysis_status: str


class CoachAthleteAnalysisItem(BaseModel):
    analysis_id: UUID
    video_id: UUID
    video_activity: Optional[str] = None
    analysis_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str
    algorithm_version: Optional[str] = None
    historical_score: Optional[float] = None
    biomechanical_score: Optional[float] = None
    asymmetry_score: Optional[float] = None
    training_load_score: Optional[float] = None
    composite_risk_score: Optional[float] = None
    overall_risk_score: Optional[float] = None
    risk_category: str
    knee_valgus: Optional[float] = None
    hip_stability: Optional[float] = None
    trunk_lean: Optional[float] = None
    stride_length: Optional[float] = None
    joint_alignment: Optional[float] = None
    symmetry_score: Optional[float] = None
    fatigue_score: Optional[float] = None
    movement_quality: Optional[float] = None
    summary_metrics: Optional[dict[str, Any]] = None
    time_series_data: Optional[dict[str, Any]] = None
    recommendations: Optional[list[dict[str, Any]]] = None
    risk_assessment: Optional[dict[str, Any]] = None
    skeleton_video_url: Optional[str] = None
    pdf_report_url: Optional[str] = None
    csv_report_url: Optional[str] = None
    pdf_report_available: bool = False
    csv_report_available: bool = False


class CoachAthleteDetailResponse(BaseModel):
    profile: CoachPrivateAthleteProfile
    performance_overview: dict
    risk_overview: dict = Field(default_factory=dict)
    movement_comparison: dict = Field(default_factory=dict)
    recent_activity: list[dict[str, Any]] = Field(default_factory=list)
    latest_analysis: Optional[CoachAthleteAnalysisItem] = None
    videos: list[CoachAthleteVideoItem] = Field(default_factory=list)
    analyses: list[CoachAthleteAnalysisItem] = Field(default_factory=list)


class CoachAssignablePhysiotherapist(BaseModel):
    user_id: UUID
    name: str
    professional_role: str
    verification_status: str
    primary_sport: Optional[str] = None
    years_of_experience: Optional[int] = None
    specialization: Optional[str] = None
    organization: Optional[str] = None
    professional_bio: Optional[str] = None
    relationship_status: str = "NONE"


class CoachTaskBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    due_date: Optional[date] = None
    priority: str = "MEDIUM"
    status: str = "ASSIGNED"
    analysis_id: Optional[UUID] = None
    video_id: Optional[UUID] = None


class CoachTaskCreate(CoachTaskBase):
    pass


class CoachTaskUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    due_date: Optional[date] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    analysis_id: Optional[UUID] = None
    video_id: Optional[UUID] = None


class CoachTaskResponse(BaseModel):
    task_id: UUID
    coach_id: UUID
    athlete_id: UUID
    analysis_id: Optional[UUID] = None
    video_id: Optional[UUID] = None
    title: str
    description: Optional[str] = None
    due_date: Optional[date] = None
    priority: str
    status: str
    completed_at: Optional[datetime] = None
    athlete_notes: Optional[str] = None
    coach_name: Optional[str] = None
    athlete_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
