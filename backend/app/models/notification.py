import enum
import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class NotificationType(str, enum.Enum):
    CONNECTION_REQUEST = "CONNECTION_REQUEST"
    CONNECTION_ACCEPTED = "CONNECTION_ACCEPTED"
    CONNECTION_REJECTED = "CONNECTION_REJECTED"
    COACH_RECOMMENDATION = "COACH_RECOMMENDATION"
    COACH_TASK_UPDATED = "COACH_TASK_UPDATED"
    REHAB_PLAN_CREATED = "REHAB_PLAN_CREATED"
    REHAB_PLAN_UPDATED = "REHAB_PLAN_UPDATED"
    PROFESSIONAL_ROLE_REQUEST = "PROFESSIONAL_ROLE_REQUEST"
    PROFESSIONAL_ROLE_APPROVED = "PROFESSIONAL_ROLE_APPROVED"
    PROFESSIONAL_ROLE_REJECTED = "PROFESSIONAL_ROLE_REJECTED"
    ANALYSIS_COMPLETED = "ANALYSIS_COMPLETED"
    REPORT_AVAILABLE = "REPORT_AVAILABLE"
    SYSTEM_ALERT = "SYSTEM_ALERT"


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_recipient_user_id", "recipient_user_id"),
        Index("ix_notifications_recipient_read", "recipient_user_id", "is_read"),
        Index("ix_notifications_created_at", "created_at"),
        Index("ix_notifications_event_lookup", "recipient_user_id", "type", "entity_type", "entity_id", "actor_user_id"),
    )

    notification_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    recipient_user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    type = Column(String(50), nullable=False)
    title = Column(String(160), nullable=False)
    message = Column(Text, nullable=False)
    actor_user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    entity_type = Column(String(80), nullable=True)
    entity_id = Column(String(80), nullable=True)
    action_url = Column(Text, nullable=True)
    is_read = Column(Boolean, nullable=False, default=False, server_default="false")
    created_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False)
    read_at = Column(DateTime, nullable=True)

    recipient = relationship("User", foreign_keys=[recipient_user_id], back_populates="notifications")
    actor = relationship("User", foreign_keys=[actor_user_id])
