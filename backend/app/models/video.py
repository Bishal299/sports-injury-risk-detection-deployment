import uuid

from sqlalchemy import Column, String, Text, Float, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy import Column, DateTime, func

from app.database import Base


class Video(Base):
    __tablename__ = "videos"

    video_id = Column(
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

    activity = Column(
        String
    )

    video_url = Column(
        Text
    )

    duration = Column(
        Float
    )

    fps = Column(
        Integer
    )

    resolution = Column(
        String
    )

    quality_score = Column(
        Float
    )

    processing_status = Column(
        String
    )

    uploaded_at = Column(
        DateTime,
        server_default=func.current_timestamp()
    )

    athlete = relationship(
        "Athlete",
        back_populates="videos"
    )

    analysis = relationship(
        "AnalysisResult",
        back_populates="video",
        uselist=False,
        cascade="all, delete-orphan"
    )