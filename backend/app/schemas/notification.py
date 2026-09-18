from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.notification import NotificationType


class NotificationResponse(BaseModel):
    notification_id: UUID
    recipient_user_id: UUID
    type: NotificationType
    title: str
    message: str
    actor_user_id: UUID | None = None
    entity_type: str | None = None
    entity_id: str | None = None
    action_url: str | None = None
    is_read: bool
    created_at: datetime
    read_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class NotificationListResponse(BaseModel):
    notifications: list[NotificationResponse]
    total: int
    limit: int
    offset: int


class NotificationUnreadCountResponse(BaseModel):
    unread_count: int
