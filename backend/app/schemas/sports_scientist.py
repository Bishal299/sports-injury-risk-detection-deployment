from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SportsScientistRiskBand(BaseModel):
    category: str
    count: int
    percentage: float


class SportsScientistMetricSummary(BaseModel):
    key: str
    label: str
    average: Optional[float] = None
    count: int = 0


class SportsScientistTrendPoint(BaseModel):
    date: datetime
    value: float
    metric: str


class SportsScientistFinding(BaseModel):
    label: str
    finding_type: str = "Movement finding"
    count: int
    latest_at: Optional[datetime] = None


class SportsScientistRecentAnalysis(BaseModel):
    analysis_id: UUID
    athlete_id: UUID
    video_id: UUID
    athlete_name: str
    sport: Optional[str] = None
    position: Optional[str] = None
    analysis_date: Optional[datetime] = None
    risk_category: str
    risk_score: Optional[float] = None
    movement_quality: Optional[float] = None
    biomechanical_efficiency: Optional[float] = None
    status: str


class SportsScientistDashboardResponse(BaseModel):
    professional_profile_id: UUID
    verification_status: str
    stats: dict
    risk_distribution: list[SportsScientistRiskBand] = Field(default_factory=list)
    biomechanical_overview: list[SportsScientistMetricSummary] = Field(default_factory=list)
    performance_trend: list[SportsScientistTrendPoint] = Field(default_factory=list)
    findings: list[SportsScientistFinding] = Field(default_factory=list)
    recent_analyses: list[SportsScientistRecentAnalysis] = Field(default_factory=list)


class SportsScientistAthleteOption(BaseModel):
    athlete_id: UUID
    name: str
    sport: Optional[str] = None
    position: Optional[str] = None


class SportsScientistRelationshipResponse(BaseModel):
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
    primary_sport: Optional[str] = None
    years_of_experience: Optional[int] = None
    specialization: Optional[str] = None
    organization: Optional[str] = None
    certifications: Optional[str] = None
    professional_bio: Optional[str] = None
    athlete_name: Optional[str] = None
    athlete_sport: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class SportsScientistDiscoveryAthlete(BaseModel):
    athlete_id: UUID
    name: str
    sport: Optional[str] = None
    position: Optional[str] = None
    age: Optional[int] = None
    connection_status: str = "NONE"
    latest_risk_score: Optional[float] = None
    risk_category: str
    analysis_count: int = 0
    latest_activity_at: Optional[datetime] = None


class SportsScientistConnectedAthlete(BaseModel):
    relationship_id: UUID
    athlete_id: UUID
    name: str
    sport: Optional[str] = None
    position: Optional[str] = None
    analysis_count: int = 0
    latest_risk_score: Optional[float] = None
    risk_category: str
    connection_status: str
    last_analysis_at: Optional[datetime] = None


class SportsScientistMetricDetail(BaseModel):
    key: str
    label: str
    value: Optional[float] = None
    unit: Optional[str] = None
    severity: Optional[str] = None
    interpretation: Optional[str] = None


class SportsScientistAnalysisDetail(SportsScientistRecentAnalysis):
    video_activity: Optional[str] = None
    video_url: Optional[str] = None
    summary: dict = Field(default_factory=dict)
    source_analysis: dict = Field(default_factory=dict)
    metrics: list[SportsScientistMetricDetail] = Field(default_factory=list)
    risk_contributions: list[dict] = Field(default_factory=list)
    biomechanical_breakdown: list[dict] = Field(default_factory=list)
    biomechanical_efficiency: dict = Field(default_factory=dict)
    symmetry: dict = Field(default_factory=dict)
    risk_factors: list[dict] = Field(default_factory=list)


class SportsScientistBiomechanicalAnalyticsResponse(BaseModel):
    athletes: list[SportsScientistAthleteOption] = Field(default_factory=list)
    sports: list[str] = Field(default_factory=list)
    analyses: list[SportsScientistAnalysisDetail] = Field(default_factory=list)


class SportsScientistRiskTrendPoint(BaseModel):
    date: str
    average_risk_score: Optional[float] = None
    analyses: int = 0


class SportsScientistRiskGroupAverage(BaseModel):
    group: str
    average_risk_score: Optional[float] = None
    analyses: int = 0


class SportsScientistRiskFactorInsight(BaseModel):
    key: str
    label: str
    frequency: int = 0
    average_risk: Optional[float] = None
    latest_at: Optional[datetime] = None
    trend: list[SportsScientistRiskTrendPoint] = Field(default_factory=list)


class SportsScientistAthleteRiskRow(BaseModel):
    athlete_id: UUID
    athlete_name: str
    sport: Optional[str] = None
    risk_category: str
    risk_score: Optional[float] = None
    movement_quality: Optional[float] = None
    main_risk_factors: list[str] = Field(default_factory=list)
    previous_injury: bool = False
    latest_analysis: Optional[datetime] = None


class SportsScientistObservedPattern(BaseModel):
    title: str
    description: str
    pattern_type: str = "Observed pattern"
    athlete_id: Optional[UUID] = None
    athlete_name: Optional[str] = None
    supporting_analyses: int = 0


class SportsScientistInjuryInsightsResponse(BaseModel):
    athletes: list[SportsScientistAthleteOption] = Field(default_factory=list)
    sports: list[str] = Field(default_factory=list)
    injury_factors: list[str] = Field(default_factory=list)
    summary: dict = Field(default_factory=dict)
    risk_distribution: list[SportsScientistRiskBand] = Field(default_factory=list)
    risk_trend: list[SportsScientistRiskTrendPoint] = Field(default_factory=list)
    average_risk_by_sport: list[SportsScientistRiskGroupAverage] = Field(default_factory=list)
    factor_analysis: list[SportsScientistRiskFactorInsight] = Field(default_factory=list)
    athlete_table: list[SportsScientistAthleteRiskRow] = Field(default_factory=list)
    observed_patterns: list[SportsScientistObservedPattern] = Field(default_factory=list)


class SportsScientistComparisonAnalysisOption(BaseModel):
    analysis_id: UUID
    athlete_id: UUID
    label: str
    analysis_date: Optional[datetime] = None
    risk_category: str
    risk_score: Optional[float] = None


class SportsScientistComparisonAthlete(SportsScientistAthleteOption):
    analyses: list[SportsScientistComparisonAnalysisOption] = Field(default_factory=list)


class SportsScientistComparisonMetricValue(BaseModel):
    athlete_id: UUID
    athlete_name: str
    analysis_id: Optional[UUID] = None
    value: Optional[float] = None
    analysis_date: Optional[datetime] = None


class SportsScientistComparisonMetricRow(BaseModel):
    key: str
    label: str
    values: list[SportsScientistComparisonMetricValue] = Field(default_factory=list)


class SportsScientistComparisonObservation(BaseModel):
    title: str
    description: str
    observation_type: str = "Data observation"
    metric: Optional[str] = None
    supporting_analyses: int = 0


class SportsScientistAthleteComparisonResponse(BaseModel):
    athletes: list[SportsScientistComparisonAthlete] = Field(default_factory=list)
    sports: list[str] = Field(default_factory=list)
    positions: list[str] = Field(default_factory=list)
    selected_athletes: list[SportsScientistComparisonAthlete] = Field(default_factory=list)
    metric_rows: list[SportsScientistComparisonMetricRow] = Field(default_factory=list)
    history: list[SportsScientistRiskTrendPoint] = Field(default_factory=list)
    observations: list[SportsScientistComparisonObservation] = Field(default_factory=list)


class SportsScientistResearchReportHistoryItem(BaseModel):
    report_id: str
    report_name: str
    scope: str
    created_date: Optional[datetime] = None
    created_by: str
    status: str
    analysis_id: Optional[UUID] = None
    athlete_id: Optional[UUID] = None
    pdf_available: bool = False


class SportsScientistResearchReportResponse(BaseModel):
    athletes: list[SportsScientistComparisonAthlete] = Field(default_factory=list)
    sports: list[str] = Field(default_factory=list)
    report: dict = Field(default_factory=dict)
    history: list[SportsScientistResearchReportHistoryItem] = Field(default_factory=list)
