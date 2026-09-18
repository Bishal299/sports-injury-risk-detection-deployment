import enum
import uuid

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Index, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class CoachAthleteRelationshipStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    REJECTED = "REJECTED"
    REVOKED = "REVOKED"


class CoachAthleteRelationship(Base):
    __tablename__ = "coach_athlete_relationships"
    __table_args__ = (
        CheckConstraint(
            "status IN ('PENDING', 'ACTIVE', 'REJECTED', 'REVOKED')",
            name="ck_coach_athlete_relationships_status_valid",
        ),
        Index(
            "uq_coach_athlete_relationships_active_pending_pair",
            "coach_id",
            "athlete_id",
            unique=True,
            postgresql_where=text("status IN ('PENDING', 'ACTIVE')"),
        ),
        Index("ix_coach_athlete_relationships_coach_id", "coach_id"),
        Index("ix_coach_athlete_relationships_athlete_id", "athlete_id"),
        Index("ix_coach_athlete_relationships_status", "status"),
        Index("ix_coach_athlete_relationships_coach_status", "coach_id", "status"),
        Index("ix_coach_athlete_relationships_athlete_status", "athlete_id", "status"),
    )

    relationship_id = Column(
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

    status = Column(
        String(20),
        nullable=False,
        default=CoachAthleteRelationshipStatus.PENDING.value,
        server_default=CoachAthleteRelationshipStatus.PENDING.value,
    )

    requested_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False)
    responded_at = Column(DateTime, nullable=True)
    accepted_at = Column(DateTime, nullable=True)
    requested_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False)
    updated_at = Column(
        DateTime,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        nullable=False,
    )

    coach = relationship(
        "CoachProfile",
        back_populates="athlete_relationships",
    )

    athlete = relationship(
        "Athlete",
        back_populates="coach_relationships",
    )

    requester = relationship(
        "User",
        foreign_keys=[requested_by],
        back_populates="requested_coach_athlete_relationships",
    )

    @property
    def coach_name(self):
        return self.coach.user.name if self.coach and self.coach.user else None

    @property
    def coach_email(self):
        return self.coach.user.email if self.coach and self.coach.user else None

    @property
    def primary_sport(self):
        return self.coach.primary_sport if self.coach else None

    @property
    def years_of_experience(self):
        return self.coach.years_of_experience if self.coach else None

    @property
    def coaching_specialization(self):
        return self.coach.coaching_specialization if self.coach else None

    @property
    def organization(self):
        return self.coach.organization if self.coach else None

    @property
    def certifications(self):
        return self.coach.certifications if self.coach else None

    @property
    def professional_bio(self):
        return self.coach.professional_bio if self.coach else None

    @property
    def athlete_name(self):
        return self.athlete.user.name if self.athlete and self.athlete.user else None

    @property
    def athlete_sport(self):
        return self.athlete.sport if self.athlete else None
