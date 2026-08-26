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

    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
