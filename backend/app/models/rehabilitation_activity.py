import enum
import uuid

from sqlalchemy import CheckConstraint, Column, Date, DateTime, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class RehabilitationActivityStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    SKIPPED = "SKIPPED"


class RehabilitationActivityPriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class RehabilitationActivity(Base):
    __tablename__ = "rehabilitation_activities"
    __table_args__ = (
        CheckConstraint(
            "phase IN ('ASSESSMENT', 'MOBILITY', 'STRENGTH', 'BALANCE_STABILITY', 'MOVEMENT_CORRECTION', 'SPORT_SPECIFIC_TRAINING', 'RETURN_TO_SPORT')",
            name="ck_rehabilitation_activities_phase_valid",
        ),
        CheckConstraint(
            "priority IN ('LOW', 'MEDIUM', 'HIGH')",
            name="ck_rehabilitation_activities_priority_valid",
        ),
        CheckConstraint(
            "status IN ('PENDING', 'IN_PROGRESS', 'COMPLETED', 'SKIPPED')",
            name="ck_rehabilitation_activities_status_valid",
        ),
        Index("ix_rehabilitation_activities_plan_id", "rehabilitation_plan_id"),
        Index("ix_rehabilitation_activities_status", "status"),
        Index("ix_rehabilitation_activities_phase", "phase"),
    )

    activity_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    rehabilitation_plan_id = Column(
        UUID(as_uuid=True),
        ForeignKey("rehabilitation_plans.rehabilitation_plan_id", ondelete="CASCADE"),
        nullable=False,
    )
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    phase = Column(String(50), nullable=False)
    due_date = Column(Date, nullable=True)
    priority = Column(String(20), nullable=False, default=RehabilitationActivityPriority.MEDIUM.value, server_default=RehabilitationActivityPriority.MEDIUM.value)
    status = Column(String(20), nullable=False, default=RehabilitationActivityStatus.PENDING.value, server_default=RehabilitationActivityStatus.PENDING.value)
    completed_at = Column(DateTime, nullable=True)
    athlete_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False)
    updated_at = Column(
        DateTime,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        nullable=False,
    )

    plan = relationship("RehabilitationPlan", back_populates="activities")
