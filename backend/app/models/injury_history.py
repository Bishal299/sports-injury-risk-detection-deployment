import uuid
import enum

from sqlalchemy import CheckConstraint, Column, DateTime, Index, String, Text, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class InjuryAffectedSide(str, enum.Enum):
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    BILATERAL = "BILATERAL"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class InjurySeverity(str, enum.Enum):
    MILD = "MILD"
    MODERATE = "MODERATE"
    SEVERE = "SEVERE"


class InjuryStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    RECOVERED = "RECOVERED"
    CHRONIC = "CHRONIC"
    UNKNOWN = "UNKNOWN"


class InjuryHistory(Base):
    __tablename__ = "injury_history"
    __table_args__ = (
        CheckConstraint("char_length(trim(injury_type)) > 0", name="ck_injury_history_injury_type_not_empty"),
        CheckConstraint("char_length(trim(body_part)) > 0", name="ck_injury_history_body_part_not_empty"),
        CheckConstraint(
            "affected_side IN ('LEFT', 'RIGHT', 'BILATERAL', 'NOT_APPLICABLE')",
            name="ck_injury_history_affected_side_valid",
        ),
        CheckConstraint(
            "severity IN ('MILD', 'MODERATE', 'SEVERE')",
            name="ck_injury_history_severity_valid",
        ),
        CheckConstraint(
            "status IN ('ACTIVE', 'RECOVERED', 'CHRONIC', 'UNKNOWN')",
            name="ck_injury_history_status_valid",
        ),
        CheckConstraint(
            "recovery_date IS NULL OR recovery_date >= injury_date",
            name="ck_injury_history_recovery_after_injury",
        ),
        Index("ix_injury_history_athlete_id", "athlete_id"),
        Index("ix_injury_history_athlete_injury_date", "athlete_id", "injury_date"),
    )

    injury_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    athlete_id = Column(
        UUID(as_uuid=True),
        ForeignKey(
            "athletes.athlete_id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    injury_type = Column(String(100), nullable=False)

    body_part = Column(String(100), nullable=False)

    affected_side = Column(String(20), nullable=False, default=InjuryAffectedSide.NOT_APPLICABLE.value)

    severity = Column(String(50), nullable=False)

    status = Column(String(50), nullable=False, default=InjuryStatus.UNKNOWN.value)

    injury_date = Column(Date, nullable=False)

    recovery_date = Column(
        Date
    )

    remarks = Column(
        Text
    )

    created_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False)
    updated_at = Column(
        DateTime,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        nullable=False,
    )

    athlete = relationship(
        "Athlete",
        back_populates="injuries"
    )
