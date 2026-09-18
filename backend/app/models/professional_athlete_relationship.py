import enum
import uuid

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Index, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class ProfessionalAthleteRelationshipRole(str, enum.Enum):
    COACH = "COACH"
    PHYSIOTHERAPIST = "PHYSIOTHERAPIST"
    SPORTS_SCIENTIST = "SPORTS_SCIENTIST"


class ProfessionalAthleteRelationshipStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    REJECTED = "REJECTED"
    REVOKED = "REVOKED"


class ProfessionalAthleteRelationship(Base):
    __tablename__ = "professional_athlete_relationships"
    __table_args__ = (
        CheckConstraint(
            "professional_role IN ('COACH', 'PHYSIOTHERAPIST', 'SPORTS_SCIENTIST')",
            name="ck_professional_athlete_relationships_role_valid",
        ),
        CheckConstraint(
            "status IN ('PENDING', 'ACTIVE', 'REJECTED', 'REVOKED')",
            name="ck_professional_athlete_relationships_status_valid",
        ),
        Index(
            "uq_professional_athlete_relationships_active_pending_pair",
            "professional_user_id",
            "athlete_id",
            "professional_role",
            unique=True,
            postgresql_where=text("status IN ('PENDING', 'ACTIVE')"),
        ),
        Index(
            "ix_professional_athlete_relationships_professional_user_id",
            "professional_user_id",
        ),
        Index("ix_professional_athlete_relationships_athlete_id", "athlete_id"),
        Index("ix_professional_athlete_relationships_professional_role", "professional_role"),
        Index("ix_professional_athlete_relationships_status", "status"),
        Index(
            "ix_professional_athlete_relationships_professional_status",
            "professional_user_id",
            "status",
        ),
        Index(
            "ix_professional_athlete_relationships_athlete_status",
            "athlete_id",
            "status",
        ),
        Index(
            "ix_professional_athlete_relationships_role_status",
            "professional_role",
            "status",
        ),
    )

    relationship_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )

    professional_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )

    athlete_id = Column(
        UUID(as_uuid=True),
        ForeignKey("athletes.athlete_id", ondelete="CASCADE"),
        nullable=False,
    )

    professional_role = Column(String(50), nullable=False)
    status = Column(
        String(20),
        nullable=False,
        default=ProfessionalAthleteRelationshipStatus.PENDING.value,
        server_default=ProfessionalAthleteRelationshipStatus.PENDING.value,
    )

    requested_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True,
    )
    requested_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False)
    responded_at = Column(DateTime, nullable=True)
    accepted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False)
    updated_at = Column(
        DateTime,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        nullable=False,
    )

    professional_user = relationship(
        "User",
        foreign_keys=[professional_user_id],
        back_populates="professional_athlete_relationships",
    )

    athlete = relationship(
        "Athlete",
        back_populates="professional_relationships",
    )

    requester = relationship(
        "User",
        foreign_keys=[requested_by],
        back_populates="requested_professional_athlete_relationships",
    )

    @property
    def coach_id(self):
        return self.professional_user_id

    @property
    def coach_name(self):
        return self.professional_user.name if self.professional_user else None

    @property
    def coach_email(self):
        return self.professional_user.email if self.professional_user else None

    @property
    def professional_name(self):
        return self.professional_user.name if self.professional_user else None

    @property
    def professional_email(self):
        return self.professional_user.email if self.professional_user else None

    @property
    def physiotherapist_name(self):
        return self.professional_name

    @property
    def physiotherapist_email(self):
        return self.professional_email

    @property
    def athlete_name(self):
        return self.athlete.user.name if self.athlete and self.athlete.user else None

    @property
    def athlete_sport(self):
        return self.athlete.sport if self.athlete else None

    @property
    def requested_by_name(self):
        return self.requester.name if self.requester else None

    @property
    def requested_by_role(self):
        return self.requester.role.value if self.requester and self.requester.role else None

    def _professional_profile(self):
        if not self.professional_user:
            return None

        for profile in self.professional_user.professional_profiles:
            if profile.professional_role == self.professional_role:
                return profile

        return None

    @property
    def primary_sport(self):
        profile = self._professional_profile()
        return profile.primary_sport if profile else None

    @property
    def years_of_experience(self):
        profile = self._professional_profile()
        return profile.years_of_experience if profile else None

    @property
    def coaching_specialization(self):
        profile = self._professional_profile()
        return profile.specialization if profile else None

    @property
    def specialization(self):
        profile = self._professional_profile()
        return profile.specialization if profile else None

    @property
    def organization(self):
        profile = self._professional_profile()
        return profile.organization if profile else None

    @property
    def certifications(self):
        profile = self._professional_profile()
        return profile.certifications if profile else None

    @property
    def professional_bio(self):
        profile = self._professional_profile()
        return profile.professional_bio if profile else None
