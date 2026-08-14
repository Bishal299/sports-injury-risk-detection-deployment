from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class VideoCreate(BaseModel):
    activity: str | None = None


class VideoRead(BaseModel):
    video_id: UUID
    athlete_id: UUID

    activity: str | None = None
    video_url: str | None = None

    duration: float | None = None
    fps: int | None = None
    resolution: str | None = None

    quality_score: float | None = None
    processing_status: str | None = None

    uploaded_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)