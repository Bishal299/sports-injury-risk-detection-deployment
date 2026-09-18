from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.notification import Notification, NotificationType
from app.models.user import User, UserRole


def create_notification(
    db: Session,
    *,
    recipient_user_id: UUID,
    notification_type: NotificationType,
    title: str,
    message: str,
    actor_user_id: UUID | None = None,
    entity_type: str | None = None,
    entity_id: UUID | str | None = None,
    action_url: str | None = None,
    dedupe: bool = True,
) -> Notification:
    normalized_entity_id = str(entity_id) if entity_id is not None else None

    if dedupe and normalized_entity_id:
        existing = (
            db.query(Notification)
            .filter(
                Notification.recipient_user_id == recipient_user_id,
                Notification.type == notification_type.value,
                Notification.entity_type == entity_type,
                Notification.entity_id == normalized_entity_id,
                Notification.actor_user_id == actor_user_id,
            )
            .first()
        )
        if existing:
            return existing

    notification = Notification(
        recipient_user_id=recipient_user_id,
        type=notification_type.value,
        title=title,
        message=message,
        actor_user_id=actor_user_id,
        entity_type=entity_type,
        entity_id=normalized_entity_id,
        action_url=action_url,
    )
    db.add(notification)
    return notification


def notify_admins(
    db: Session,
    *,
    notification_type: NotificationType,
    title: str,
    message: str,
    actor_user_id: UUID | None = None,
    entity_type: str | None = None,
    entity_id: UUID | str | None = None,
    action_url: str | None = None,
):
    admins = db.query(User).filter(User.role == UserRole.ADMINISTRATOR).all()
    for admin in admins:
        create_notification(
            db,
            recipient_user_id=admin.user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            actor_user_id=actor_user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action_url=action_url,
        )


def mark_notification_read(notification: Notification, is_read: bool = True):
    notification.is_read = is_read
    notification.read_at = datetime.now(timezone.utc) if is_read else None
    return notification
