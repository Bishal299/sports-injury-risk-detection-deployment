import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class PhysiotherapistNote(Base):
    __tablename__ = "physiotherapist_notes"
    __table_args__ = (
        Index("ix_physiotherapist_notes_athlete_id", "athlete_id"),
        Index("ix_physiotherapist_notes_physiotherapist_user_id", "physiotherapist_user_id"),
        Index(
            "ix_physiotherapist_notes_physio_athlete",
            "physiotherapist_user_id",
            "athlete_id",
        ),
    )

    note_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    athlete_id = Column(
        UUID(as_uuid=True),
        ForeignKey("athletes.athlete_id", ondelete="CASCADE"),
        nullable=False,
    )
    physiotherapist_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    title = Column(String(255), nullable=True)
    note = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False)
    updated_at = Column(
        DateTime,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        nullable=False,
    )

    athlete = relationship("Athlete", back_populates="physiotherapist_notes")
    physiotherapist = relationship("User", foreign_keys=[physiotherapist_user_id])
