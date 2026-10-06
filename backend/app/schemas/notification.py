from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class NotificationCreate(BaseModel):
    recipient_user_id: str
    recipient_role: Optional[str] = None
    type: str = "general"  # "training" | "performance" | "tournament" | "general"
    title: str
    message: str
    related_entity_type: Optional[str] = None  # "training_session", "assessment", "tournament", etc.
    related_entity_id: Optional[str] = None


class NotificationResponse(BaseModel):
    id: str
    recipient_user_id: str
    recipient_role: Optional[str] = None
    type: str
    title: str
    message: str
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[str] = None
    is_read: bool = False
    created_at: datetime
    read_at: Optional[datetime] = None


class UnreadCountResponse(BaseModel):
    unread_count: int


class ReadAllResponse(BaseModel):
    updated_count: int
