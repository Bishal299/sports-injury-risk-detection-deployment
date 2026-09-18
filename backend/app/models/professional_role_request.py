import enum
import uuid

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class ProfessionalRequestedRole(str, enum.Enum):
    COACH = "COACH"
    PHYSIOTHERAPIST = "PHYSIOTHERAPIST"
    SPORTS_SCIENTIST = "SPORTS_SCIENTIST"


class ProfessionalRoleRequestStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ProfessionalRoleRequest(Base):
    __tablename__ = "professional_role_requests"
    __table_args__ = (
        CheckConstraint(
            "requested_role IN ('COACH', 'PHYSIOTHERAPIST', 'SPORTS_SCIENTIST')",
            name="ck_professional_role_requests_requested_role_valid",
        ),
        CheckConstraint(
            "status IN ('PENDING', 'APPROVED', 'REJECTED')",
            name="ck_professional_role_requests_status_valid",
        ),
        CheckConstraint(
            "years_of_experience IS NULL OR years_of_experience >= 0",
            name="ck_professional_role_requests_experience_non_negative",
        ),
        Index("ix_professional_role_requests_user_id", "user_id"),
        Index("ix_professional_role_requests_status", "status"),
        Index("ix_professional_role_requests_requested_role_status", "requested_role", "status"),
        Index(
            "uq_professional_role_requests_user_role_pending",
            "user_id",
            "requested_role",
            unique=True,
            postgresql_where=text("status = 'PENDING'"),
        ),
    )

    request_id = Column(
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

    requested_role = Column(String(50), nullable=False)
    status = Column(
        String(20),
        nullable=False,
        default=ProfessionalRoleRequestStatus.PENDING.value,
        server_default=ProfessionalRoleRequestStatus.PENDING.value,
    )

    primary_sport = Column(String(100), nullable=True)
    organization = Column(String(255), nullable=True)
    specialization = Column(String(255), nullable=True)
    years_of_experience = Column(Integer, nullable=True)
    certifications = Column(Text, nullable=True)
    professional_bio = Column(Text, nullable=True)
    supporting_document_url = Column(Text, nullable=True)

    submitted_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False)
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True,
    )
    rejection_reason = Column(Text, nullable=True)

    created_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False)
    updated_at = Column(
        DateTime,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        nullable=False,
    )

    user = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="professional_role_requests",
    )
    reviewer = relationship(
        "User",
        foreign_keys=[reviewed_by],
        back_populates="reviewed_professional_role_requests",
    )

    @property
    def applicant_name(self):
        return self.user.name if self.user else None

    @property
    def applicant_email(self):
        return self.user.email if self.user else None

    @property
    def applicant_phone(self):
        return self.user.phone if self.user else None
