import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import get_current_user
from app.db.database import get_database
from app.schemas.notification import (
    NotificationCreate,
    NotificationResponse,
    ReadAllResponse,
    UnreadCountResponse,
)
from app.services.notification_service import (
    delete_my_notification_service,
    get_my_notifications_service,
    get_my_unread_count_service,
    mark_all_my_notifications_read_service,
    mark_my_notification_read_service,
    create_notification_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=list[NotificationResponse])
async def list_notifications(
    current_user: Annotated[dict, Depends(get_current_user)],
    unread: Optional[bool] = Query(default=None, description="Filter unread notifications"),
    unread_only: Optional[bool] = Query(default=None, description="Alias for unread filter"),
    type: Optional[str] = Query(default=None, description="Filter by notification type"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
):
    """
    Get notifications for the current authenticated user.
    Supports filtering by unread status and notification type.
    """
    db = get_database()
    is_unread = True if (unread is True or unread_only is True) else (False if unread is False else False)
    # If unread filter wasn't explicitly set to true, check if unread is None
    unread_filter = True if (unread is True or unread_only is True) else False

    return await get_my_notifications_service(
        db,
        current_user=current_user,
        unread_only=unread_filter,
        notification_type=type,
        skip=skip,
        limit=limit,
    )


@router.get("/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Get the unread notification count for the current user."""
    db = get_database()
    return await get_my_unread_count_service(db, current_user=current_user)


@router.patch("/read-all", response_model=ReadAllResponse)
async def mark_all_read(
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Mark all notifications of current user as read."""
    db = get_database()
    return await mark_all_my_notifications_read_service(db, current_user=current_user)


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Mark a single notification as read. Enforces user ownership."""
    db = get_database()
    return await mark_my_notification_read_service(
        db,
        notification_id=notification_id,
        current_user=current_user,
    )


@router.delete("/{notification_id}", status_code=status.HTTP_200_OK)
async def delete_notification(
    notification_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Delete a single notification. Enforces user ownership."""
    db = get_database()
    return await delete_my_notification_service(
        db,
        notification_id=notification_id,
        current_user=current_user,
    )


@router.post("", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
async def create_notification_endpoint(
    payload: NotificationCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Create a notification (accessible to authenticated users/admins)."""
    db = get_database()
    return await create_notification_service(db, payload)
