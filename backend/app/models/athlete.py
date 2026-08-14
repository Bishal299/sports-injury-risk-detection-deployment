import uuid

from sqlalchemy import Column, String, Integer, Float, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Athlete(Base):
    __tablename__ = "athletes"

    athlete_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.user_id",
            ondelete="CASCADE"
        ),
        nullable=False,
        unique=True
    )

    sport = Column(
        String(100)
    )

    position = Column(
        String(100)
    )

    age = Column(
        Integer
    )

    height = Column(
        Float
    )

    weight = Column(
        Float
    )

    training_load = Column(
        Float
    )

    flexibility = Column(
        Float
    )

    strength = Column(
        Float
    )

    balance = Column(
        Float
    )

    endurance = Column(
        Float
    )

    coach_notes = Column(
        Text
    )

    user = relationship(
        "User",
        back_populates="athlete"
    )

    injuries = relationship(
        "InjuryHistory",
        back_populates="athlete",
        cascade="all, delete"
    )

    videos = relationship(
        "Video",
        back_populates="athlete",
        cascade="all, delete"
    )