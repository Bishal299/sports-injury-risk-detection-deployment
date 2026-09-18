import enum
import uuid

from sqlalchemy import CheckConstraint, Column, DateTime, Float, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class ProfessionalProfileRole(str, enum.Enum):
    COACH = "COACH"
    PHYSIOTHERAPIST = "PHYSIOTHERAPIST"
    SPORTS_SCIENTIST = "SPORTS_SCIENTIST"


class ProfessionalVerificationStatus(str, enum.Enum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


class ProfessionalProfile(Base):
    __tablename__ = "professional_profiles"
    __table_args__ = (
        CheckConstraint(
            "professional_role IN ('COACH', 'PHYSIOTHERAPIST', 'SPORTS_SCIENTIST')",
            name="ck_professional_profiles_role_valid",
        ),
        CheckConstraint(
            "verification_status IN ('PENDING', 'VERIFIED', 'REJECTED')",
            name="ck_professional_profiles_verification_status_valid",
        ),
        CheckConstraint(
            "years_of_experience IS NULL OR years_of_experience >= 0",
            name="ck_professional_profiles_experience_non_negative",
        ),
        CheckConstraint(
            "profile_completion IS NULL OR (profile_completion >= 0 AND profile_completion <= 100)",
            name="ck_professional_profiles_completion_range",
        ),
        Index(
            "uq_professional_profiles_user_role",
            "user_id",
            "professional_role",
            unique=True,
        ),
        Index("ix_professional_profiles_user_id", "user_id"),
        Index("ix_professional_profiles_professional_role", "professional_role"),
        Index("ix_professional_profiles_verification_status", "verification_status"),
        Index(
            "ix_professional_profiles_role_status",
            "professional_role",
            "verification_status",
        ),
    )

    professional_profile_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )

    professional_role = Column(String(50), nullable=False)
    verification_status = Column(
        String(20),
        nullable=False,
        default=ProfessionalVerificationStatus.PENDING.value,
        server_default=ProfessionalVerificationStatus.PENDING.value,
    )

    primary_sport = Column(String(100), nullable=True)
    other_sports = Column(Text, nullable=True)
    years_of_experience = Column(Integer, nullable=True)
    specialization = Column(String(255), nullable=True)
    organization = Column(String(255), nullable=True)
    certifications = Column(Text, nullable=True)
    professional_bio = Column(Text, nullable=True)
    profile_photo_url = Column(Text, nullable=True)
    profile_completion = Column(Float, nullable=False, default=0, server_default="0")

    created_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False)
    updated_at = Column(
        DateTime,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        nullable=False,
    )

    user = relationship(
        "User",
        back_populates="professional_profiles",
    )
