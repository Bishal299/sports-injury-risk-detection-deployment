import enum
import uuid

from sqlalchemy import CheckConstraint, Column, Date, DateTime, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class CoachTaskStatus(str, enum.Enum):
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    OVERDUE = "OVERDUE"
    CANCELLED = "CANCELLED"


class CoachTaskPriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class CoachTask(Base):
    __tablename__ = "coach_tasks"
    __table_args__ = (
        CheckConstraint(
            "priority IN ('LOW', 'MEDIUM', 'HIGH')",
            name="ck_coach_tasks_priority_valid",
        ),
        CheckConstraint(
            "status IN ('ASSIGNED', 'IN_PROGRESS', 'COMPLETED', 'OVERDUE', 'CANCELLED')",
            name="ck_coach_tasks_status_valid",
        ),
        CheckConstraint(
            "char_length(trim(title)) > 0",
            name="ck_coach_tasks_title_not_empty",
        ),
        Index("ix_coach_tasks_coach_id", "coach_id"),
        Index("ix_coach_tasks_athlete_id", "athlete_id"),
        Index("ix_coach_tasks_analysis_id", "analysis_id"),
        Index("ix_coach_tasks_video_id", "video_id"),
        Index("ix_coach_tasks_status", "status"),
        Index("ix_coach_tasks_due_date", "due_date"),
        Index("ix_coach_tasks_coach_athlete_status", "coach_id", "athlete_id", "status"),
    )

    task_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    coach_id = Column(
        UUID(as_uuid=True),
        ForeignKey("coach_profiles.coach_id", ondelete="CASCADE"),
        nullable=False,
    )
    athlete_id = Column(
        UUID(as_uuid=True),
        ForeignKey("athletes.athlete_id", ondelete="CASCADE"),
        nullable=False,
    )
    analysis_id = Column(
        UUID(as_uuid=True),
        ForeignKey("analysis_results.analysis_id", ondelete="SET NULL"),
        nullable=True,
    )
    video_id = Column(
        UUID(as_uuid=True),
        ForeignKey("videos.video_id", ondelete="SET NULL"),
        nullable=True,
    )
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(Date, nullable=True)
    priority = Column(
        String(20),
        nullable=False,
        default=CoachTaskPriority.MEDIUM.value,
        server_default=CoachTaskPriority.MEDIUM.value,
    )
    status = Column(
        String(20),
        nullable=False,
        default=CoachTaskStatus.ASSIGNED.value,
        server_default=CoachTaskStatus.ASSIGNED.value,
    )
    completed_at = Column(DateTime, nullable=True)
    athlete_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False)
    updated_at = Column(
        DateTime,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        nullable=False,
    )

    coach = relationship("CoachProfile", back_populates="tasks")
    athlete = relationship("Athlete", back_populates="coach_tasks")
