import uuid

from sqlalchemy import Column, String, Text, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class InjuryHistory(Base):
    __tablename__ = "injury_history"

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

    injury_type = Column(
        String(100)
    )

    body_part = Column(
        String(100)
    )

    severity = Column(
        String(50)
    )

    injury_date = Column(
        Date
    )

    recovery_date = Column(
        Date
    )

    remarks = Column(
        Text
    )

    athlete = relationship(
        "Athlete",
        back_populates="injuries"
    )