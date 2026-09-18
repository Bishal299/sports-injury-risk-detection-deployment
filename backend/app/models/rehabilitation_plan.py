import enum
import uuid

from sqlalchemy import CheckConstraint, Column, Date, DateTime, Float, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import JSON

from app.database import Base


class RehabilitationPlanStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class RehabilitationPlanPhase(str, enum.Enum):
    ASSESSMENT = "ASSESSMENT"
    MOBILITY = "MOBILITY"
    STRENGTH = "STRENGTH"
    BALANCE_STABILITY = "BALANCE_STABILITY"
    MOVEMENT_CORRECTION = "MOVEMENT_CORRECTION"
    SPORT_SPECIFIC_TRAINING = "SPORT_SPECIFIC_TRAINING"
    RETURN_TO_SPORT = "RETURN_TO_SPORT"


class RehabilitationPlan(Base):
    __tablename__ = "rehabilitation_plans"
    __table_args__ = (
        CheckConstraint(
            "status IN ('ACTIVE', 'PAUSED', 'COMPLETED', 'CANCELLED')",
            name="ck_rehabilitation_plans_status_valid",
        ),
        CheckConstraint(
            "current_phase IN ('ASSESSMENT', 'MOBILITY', 'STRENGTH', 'BALANCE_STABILITY', 'MOVEMENT_CORRECTION', 'SPORT_SPECIFIC_TRAINING', 'RETURN_TO_SPORT')",
            name="ck_rehabilitation_plans_phase_valid",
        ),
        CheckConstraint(
            "progress IS NULL OR (progress >= 0 AND progress <= 100)",
            name="ck_rehabilitation_plans_progress_range",
        ),
        Index("ix_rehabilitation_plans_athlete_id", "athlete_id"),
        Index("ix_rehabilitation_plans_physiotherapist_user_id", "physiotherapist_user_id"),
        Index("ix_rehabilitation_plans_status", "status"),
        Index(
            "ix_rehabilitation_plans_physio_athlete_status",
            "physiotherapist_user_id",
            "athlete_id",
            "status",
        ),
    )

    rehabilitation_plan_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    athlete_id = Column(
        UUID(as_uuid=True),
        ForeignKey("athletes.athlete_id", ondelete="CASCADE"),
        nullable=False,
    )
    physiotherapist_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    injury_context = Column(Text, nullable=True)
    start_date = Column(Date, nullable=True)
    target_date = Column(Date, nullable=True)
    current_phase = Column(
        String(50),
        nullable=False,
        default=RehabilitationPlanPhase.ASSESSMENT.value,
        server_default=RehabilitationPlanPhase.ASSESSMENT.value,
    )
    progress = Column(Float, nullable=False, default=0, server_default="0")
    goals = Column(JSON, nullable=True)
    completed_activities = Column(JSON, nullable=True)
    pending_activities = Column(JSON, nullable=True)
    recent_assessment = Column(Text, nullable=True)
    status = Column(
        String(20),
        nullable=False,
        default=RehabilitationPlanStatus.ACTIVE.value,
        server_default=RehabilitationPlanStatus.ACTIVE.value,
    )
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False)
    updated_at = Column(
        DateTime,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        nullable=False,
    )

    athlete = relationship("Athlete", back_populates="rehabilitation_plans")
    physiotherapist = relationship("User", foreign_keys=[physiotherapist_user_id])
    activities = relationship(
        "RehabilitationActivity",
        back_populates="plan",
        cascade="all, delete-orphan",
        order_by="RehabilitationActivity.created_at",
    )
