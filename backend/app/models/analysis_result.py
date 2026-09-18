import uuid
from sqlalchemy import Column, String, Text, Float, Integer, DateTime, ForeignKey, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy import func
from app.database import Base


class AnalysisResult(Base):
    __tablename__ = "analysis_results"
    __table_args__ = (
        Index("ix_analysis_results_athlete_date", "athlete_id", "analysis_date"),
        Index("ix_analysis_results_video_date", "video_id", "analysis_date"),
    )

    analysis_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    video_id = Column(
        UUID(as_uuid=True),
        ForeignKey(
            "videos.video_id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    athlete_id = Column(
        UUID(as_uuid=True),
        ForeignKey(
            "athletes.athlete_id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    # Core biomechanical measurements
    knee_valgus = Column(Float, nullable=True)
    hip_stability = Column(Float, nullable=True)
    trunk_lean = Column(Float, nullable=True)
    stride_length = Column(Float, nullable=True)
    joint_alignment = Column(Float, nullable=True)
    symmetry_score = Column(Float, nullable=True)
    fatigue_score = Column(Float, nullable=True)
    movement_quality = Column(Float, nullable=True)
    overall_risk_score = Column(Float, nullable=True)
    risk_level = Column(String(50), nullable=True)

    algorithm_version = Column(String(50), nullable=False, default="1.0-phase1-filtered")
    historical_score = Column(Float, nullable=True)
    biomechanical_score = Column(Float, nullable=True)
    asymmetry_score = Column(Float, nullable=True)
    training_load_score = Column(Float, nullable=True)
    composite_risk_score = Column(Float, nullable=True)
    risk_category = Column(String(50), nullable=True)

    # Processing state
    status = Column(String(50), default="pending", nullable=False)
    progress = Column(Integer, default=0, nullable=False)
    stage = Column(String(255), default="Preparing video...", nullable=False)
    error_message = Column(Text, nullable=True)

    # Generated asset URLs
    skeleton_video_url = Column(Text, nullable=True)
    csv_report_url = Column(Text, nullable=True)
    pdf_report_url = Column(Text, nullable=True)

    # Detailed metrics & time series payloads
    summary_metrics = Column(JSON, nullable=True)
    time_series_data = Column(JSON, nullable=True)
    recommendations = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(
        DateTime,
        server_default=func.current_timestamp(),
        nullable=False
    )
    analysis_date = Column(
        DateTime,
        server_default=func.current_timestamp(),
        nullable=False
    )
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    video = relationship(
        "Video",
        back_populates="analyses"
    )

    athlete = relationship(
        "Athlete",
        back_populates="analyses"
    )
