from datetime import datetime
from uuid import UUID
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict


class AnalysisStatusResponse(BaseModel):
    analysis_id: Optional[UUID] = None
    video_id: UUID
    status: str
    progress: int
    stage: str
    error_message: Optional[str] = None
    overall_score: Optional[float] = None
    risk_level: Optional[str] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AnalysisResultResponse(BaseModel):
    analysis_id: UUID
    video_id: UUID
    athlete_id: UUID

    # Core biomechanical metrics
    knee_valgus: Optional[float] = None
    hip_stability: Optional[float] = None
    trunk_lean: Optional[float] = None
    stride_length: Optional[float] = None
    joint_alignment: Optional[float] = None
    symmetry_score: Optional[float] = None
    fatigue_score: Optional[float] = None
    movement_quality: Optional[float] = None
    overall_risk_score: Optional[float] = None
    risk_level: Optional[str] = None
    algorithm_version: Optional[str] = None
    historical_score: Optional[float] = None
    biomechanical_score: Optional[float] = None
    asymmetry_score: Optional[float] = None
    training_load_score: Optional[float] = None
    composite_risk_score: Optional[float] = None
    risk_category: Optional[str] = None

    # Status & progress
    status: str
    progress: int
    stage: str
    error_message: Optional[str] = None

    # Media & report URLs
    skeleton_video_url: Optional[str] = None
    csv_report_url: Optional[str] = None
    pdf_report_url: Optional[str] = None

    # Payloads
    summary_metrics: Optional[Dict[str, Any]] = None
    time_series_data: Optional[Dict[str, Any]] = None
    recommendations: Optional[List[Dict[str, Any]]] = None
    risk_assessment: Optional[Dict[str, Any]] = None

    created_at: datetime
    analysis_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AnalysisVideoSummary(BaseModel):
    video_id: UUID
    activity: Optional[str] = None
    video_url: Optional[str] = None
    uploaded_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AnalysisHistoryItem(BaseModel):
    analysis_id: UUID
    video_id: UUID
    athlete_id: UUID
    analysis_date: Optional[datetime] = None
    algorithm_version: Optional[str] = None
    historical_score: Optional[float] = None
    biomechanical_score: Optional[float] = None
    asymmetry_score: Optional[float] = None
    training_load_score: Optional[float] = None
    composite_risk_score: Optional[float] = None
    overall_risk_score: Optional[float] = None
    risk_category: Optional[str] = None
    risk_level: Optional[str] = None
    status: str
    completed_at: Optional[datetime] = None
    video: Optional[AnalysisVideoSummary] = None

    model_config = ConfigDict(from_attributes=True)
