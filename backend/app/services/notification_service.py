import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.repositories.notification_repository import (
    count_unread_notifications,
    create_notification,
    delete_notification as repo_delete_notification,
    get_notification_by_id,
    list_user_notifications,
    mark_all_as_read as repo_mark_all_as_read,
    mark_notification_as_read as repo_mark_as_read,
)
from app.schemas.notification import (
    NotificationCreate,
    NotificationResponse,
    ReadAllResponse,
    UnreadCountResponse,
)

logger = logging.getLogger(__name__)


def _to_notification_response(doc: dict) -> NotificationResponse:
    rec_id = str(doc.get("recipient_user_id") or doc.get("user_id") or "")
    return NotificationResponse(
        id=str(doc["_id"]),
        recipient_user_id=rec_id,
        recipient_role=doc.get("recipient_role"),
        type=doc.get("type", "general"),
        title=doc.get("title", ""),
        message=doc.get("message", ""),
        related_entity_type=doc.get("related_entity_type"),
        related_entity_id=str(doc.get("related_entity_id")) if doc.get("related_entity_id") else None,
        is_read=doc.get("is_read", False),
        created_at=doc.get("created_at"),
        read_at=doc.get("read_at"),
    )


# ── Notification Queries & Mutations ──────────────────────────────────────────

async def create_notification_service(
    db: AsyncIOMotorDatabase,
    payload: NotificationCreate,
) -> NotificationResponse:
    doc = await create_notification(
        db,
        recipient_user_id=payload.recipient_user_id,
        title=payload.title,
        message=payload.message,
        type=payload.type,
        recipient_role=payload.recipient_role,
        related_entity_type=payload.related_entity_type,
        related_entity_id=payload.related_entity_id,
    )
    if not doc:
        raise BadRequestError("Could not create notification")
    return _to_notification_response(doc)


async def get_my_notifications_service(
    db: AsyncIOMotorDatabase,
    current_user: dict,
    unread_only: bool = False,
    notification_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> list[NotificationResponse]:
    user_id = current_user["user_id"]
    docs = await list_user_notifications(
        db,
        user_id=user_id,
        unread_only=unread_only,
        notification_type=notification_type,
        skip=skip,
        limit=limit,
    )
    return [_to_notification_response(d) for d in docs]


async def get_my_unread_count_service(
    db: AsyncIOMotorDatabase,
    current_user: dict,
) -> UnreadCountResponse:
    user_id = current_user["user_id"]
    count = await count_unread_notifications(db, user_id)
    return UnreadCountResponse(unread_count=count)


async def mark_my_notification_read_service(
    db: AsyncIOMotorDatabase,
    notification_id: str,
    current_user: dict,
) -> NotificationResponse:
    notif = await get_notification_by_id(db, notification_id)
    if not notif:
        raise NotFoundError("Notification not found")

    owner_id = str(notif.get("recipient_user_id") or notif.get("user_id") or "")
    if owner_id != current_user["user_id"]:
        raise ForbiddenError("You cannot modify another user's notification")

    updated = await repo_mark_as_read(db, notification_id)
    return _to_notification_response(updated)


async def mark_all_my_notifications_read_service(
    db: AsyncIOMotorDatabase,
    current_user: dict,
) -> ReadAllResponse:
    user_id = current_user["user_id"]
    count = await repo_mark_all_as_read(db, user_id)
    return ReadAllResponse(updated_count=count)


async def delete_my_notification_service(
    db: AsyncIOMotorDatabase,
    notification_id: str,
    current_user: dict,
) -> dict:
    notif = await get_notification_by_id(db, notification_id)
    if not notif:
        raise NotFoundError("Notification not found")

    owner_id = str(notif.get("recipient_user_id") or notif.get("user_id") or "")
    if owner_id != current_user["user_id"]:
        raise ForbiddenError("You cannot delete another user's notification")

    success = await repo_delete_notification(db, notification_id)
    if not success:
        raise NotFoundError("Failed to delete notification")
    return {"message": "Notification deleted successfully", "id": notification_id}


# ── Event Notification Helpers ────────────────────────────────────────────────

async def notify_training_created(
    db: AsyncIOMotorDatabase,
    session_doc: dict,
) -> None:
    """Notifies all participants that a training session was scheduled."""
    ath_ids = session_doc.get("athlete_ids", [])
    if not ath_ids:
        return

    sess_id = str(session_doc["_id"])
    s_date = session_doc.get("session_date") or session_doc.get("date")
    date_str = s_date.strftime("%b %d, %Y") if hasattr(s_date, "strftime") else str(s_date)
    venue = session_doc.get("venue") or session_doc.get("location") or "Academy Ground"

    athletes = await db.athletes.find({"_id": {"$in": ath_ids}}).to_list(length=100)
    for ath in athletes:
        u_id = ath.get("user_id")
        if u_id:
            await create_notification(
                db,
                recipient_user_id=str(u_id),
                recipient_role="athlete",
                type="training",
                title="Training Session Scheduled",
                message=f"You have a training session on {date_str} at {venue}.",
                related_entity_type="training_session",
                related_entity_id=sess_id,
            )


async def notify_training_cancelled(
    db: AsyncIOMotorDatabase,
    session_doc: dict,
) -> None:
    """Notifies all participants that a training session was cancelled."""
    ath_ids = session_doc.get("athlete_ids", [])
    if not ath_ids:
        return

    sess_id = str(session_doc["_id"])
    s_date = session_doc.get("session_date") or session_doc.get("date")
    date_str = s_date.strftime("%b %d, %Y") if hasattr(s_date, "strftime") else str(s_date)

    athletes = await db.athletes.find({"_id": {"$in": ath_ids}}).to_list(length=100)
    for ath in athletes:
        u_id = ath.get("user_id")
        if u_id:
            await create_notification(
                db,
                recipient_user_id=str(u_id),
                recipient_role="athlete",
                type="training",
                title="Training Session Cancelled",
                message=f"The training session on {date_str} has been cancelled.",
                related_entity_type="training_session",
                related_entity_id=f"cancelled_{sess_id}",
            )


async def notify_attendance_recorded(
    db: AsyncIOMotorDatabase,
    athlete_user_id: str,
    status: str,
    session_date: str,
    session_id: str,
) -> None:
    """Notifies athlete of their attendance record."""
    if not athlete_user_id:
        return
    await create_notification(
        db,
        recipient_user_id=str(athlete_user_id),
        recipient_role="athlete",
        type="training",
        title="Attendance Recorded",
        message=f"Your attendance for {session_date} was recorded as: {status.capitalize()}.",
        related_entity_type="training_session",
        related_entity_id=f"att_{session_id}",
    )


async def notify_assessment_created(
    db: AsyncIOMotorDatabase,
    athlete_user_id: str,
    overall_score: float,
    assessment_id: str,
) -> None:
    """Notifies athlete of a new performance assessment."""
    if not athlete_user_id:
        return
    await create_notification(
        db,
        recipient_user_id=str(athlete_user_id),
        recipient_role="athlete",
        type="performance",
        title="New Performance Assessment",
        message=f"A new performance assessment has been recorded. Overall Score: {overall_score}/100.",
        related_entity_type="assessment",
        related_entity_id=str(assessment_id),
    )


async def notify_tournament_registration(
    db: AsyncIOMotorDatabase,
    athlete_user_id: str,
    tournament_name: str,
    tournament_id: str,
) -> None:
    """Notifies athlete when registered for a tournament."""
    if not athlete_user_id:
        return
    await create_notification(
        db,
        recipient_user_id=str(athlete_user_id),
        recipient_role="athlete",
        type="tournament",
        title="Tournament Registration Confirmed",
        message=f"You have been registered for '{tournament_name}'.",
        related_entity_type="tournament",
        related_entity_id=f"reg_{tournament_id}",
    )


async def notify_tournament_result(
    db: AsyncIOMotorDatabase,
    athlete_user_id: str,
    tournament_name: str,
    tournament_id: str,
    position: Optional[int] = None,
    medal: Optional[str] = None,
    points: Optional[float] = None,
) -> None:
    """Notifies athlete when tournament result is recorded."""
    if not athlete_user_id:
        return

    res_parts = []
    if position:
        res_parts.append(f"Position: #{position}")
    if medal:
        res_parts.append(f"Medal: {medal}")
    if points is not None:
        res_parts.append(f"Points: {points}")
    res_str = ", ".join(res_parts) if res_parts else "Results are now available"

    await create_notification(
        db,
        recipient_user_id=str(athlete_user_id),
        recipient_role="athlete",
        type="tournament",
        title="Tournament Result Recorded",
        message=f"Results for '{tournament_name}': {res_str}.",
        related_entity_type="tournament",
        related_entity_id=f"res_{tournament_id}",
    )
