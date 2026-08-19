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
        uselist=False
    )