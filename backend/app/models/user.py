import enum
import uuid

from sqlalchemy import Column, String, Text, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy import Column, DateTime, func

from app.database import Base


class UserRole(str, enum.Enum):
    ATHLETE = "Athlete"
    COACH = "Coach"
    PHYSIOTHERAPIST = "Physiotherapist"
    SPORTS_SCIENTIST = "Sports Scientist"
    ADMINISTRATOR = "Administrator"


class User(Base):
    __tablename__ = "users"

    user_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    name = Column(
        String(100),
        nullable=False
    )

    email = Column(
        String(255),
        unique=True,
        nullable=False
    )

    password = Column(
        Text,
        nullable=True
    )

    role = Column(
        Enum(
            UserRole,
            name="user_role",
            create_type=False,
            values_callable=lambda enum_class: [
                member.value for member in enum_class
            ]
        ),
        nullable=False,
        default=UserRole.ATHLETE
    )

    phone = Column(String(20))

    profile_image = Column(Text)

    created_at = Column(
    DateTime,
    server_default=func.current_timestamp()
    )

    athlete = relationship(
        "Athlete",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

    coach_profile = relationship(
        "CoachProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

    professional_profiles = relationship(
        "ProfessionalProfile",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    professional_role_requests = relationship(
        "ProfessionalRoleRequest",
        foreign_keys="ProfessionalRoleRequest.user_id",
        back_populates="user",
        cascade="all, delete"
    )

    reviewed_professional_role_requests = relationship(
        "ProfessionalRoleRequest",
        foreign_keys="ProfessionalRoleRequest.reviewed_by",
        back_populates="reviewer"
    )

    requested_coach_athlete_relationships = relationship(
        "CoachAthleteRelationship",
        foreign_keys="CoachAthleteRelationship.requested_by",
        back_populates="requester"
    )

    professional_athlete_relationships = relationship(
        "ProfessionalAthleteRelationship",
        foreign_keys="ProfessionalAthleteRelationship.professional_user_id",
        back_populates="professional_user",
        cascade="all, delete"
    )

    requested_professional_athlete_relationships = relationship(
        "ProfessionalAthleteRelationship",
        foreign_keys="ProfessionalAthleteRelationship.requested_by",
        back_populates="requester"
    )

    notifications = relationship(
        "Notification",
        foreign_keys="Notification.recipient_user_id",
        back_populates="recipient",
        cascade="all, delete-orphan"
    )
