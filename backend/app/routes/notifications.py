from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import (
    NotificationListResponse,
    NotificationResponse,
    NotificationUnreadCountResponse,
)
from app.services.notifications import mark_notification_read


router = APIRouter(prefix="/notifications", tags=["Notifications"])


def _get_owned_notification(notification_id: UUID, current_user: User, db: Session) -> Notification:
    notification = (
        db.query(Notification)
        .filter(
            Notification.notification_id == notification_id,
            Notification.recipient_user_id == current_user.user_id,
        )
        .first()
    )
    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return notification


@router.get("", response_model=NotificationListResponse)
def list_notifications(
    unread_only: bool = Query(default=False),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Notification).filter(Notification.recipient_user_id == current_user.user_id)
    if unread_only:
        query = query.filter(Notification.is_read.is_(False))

    total = query.with_entities(func.count(Notification.notification_id)).scalar() or 0
    notifications = query.order_by(Notification.created_at.desc()).offset(offset).limit(limit).all()

    return NotificationListResponse(notifications=notifications, total=total, limit=limit, offset=offset)


@router.get("/unread-count", response_model=NotificationUnreadCountResponse)
def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    count = (
        db.query(func.count(Notification.notification_id))
        .filter(Notification.recipient_user_id == current_user.user_id, Notification.is_read.is_(False))
        .scalar()
        or 0
    )
    return NotificationUnreadCountResponse(unread_count=count)


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
def mark_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    notification = _get_owned_notification(notification_id, current_user, db)
    mark_notification_read(notification, True)
    db.commit()
    db.refresh(notification)
    return notification


@router.patch("/{notification_id}/unread", response_model=NotificationResponse)
def mark_unread(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    notification = _get_owned_notification(notification_id, current_user, db)
    mark_notification_read(notification, False)
    db.commit()
    db.refresh(notification)
    return notification


@router.patch("/read-all")
def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    notifications = (
        db.query(Notification)
        .filter(Notification.recipient_user_id == current_user.user_id, Notification.is_read.is_(False))
        .all()
    )
    for notification in notifications:
        mark_notification_read(notification, True)

    db.commit()
    return {"updated": len(notifications)}
