from datetime import datetime, timezone
from typing import Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase


async def create_notification(
    db: AsyncIOMotorDatabase,
    recipient_user_id: str,
    title: str,
    message: str,
    type: str = "general",
    recipient_role: Optional[str] = None,
    related_entity_type: Optional[str] = None,
    related_entity_id: Optional[str] = None,
) -> Optional[dict]:
    """
    Creates an in-app notification in MongoDB.
    Enforces duplicate prevention: if a notification with the same
    (recipient_user_id, type, related_entity_type, related_entity_id) already exists,
    it returns the existing one without duplicating.
    """
    try:
        user_oid = ObjectId(recipient_user_id)
    except Exception:
        return None

    # Duplicate protection for entity-linked notifications
    if related_entity_type and related_entity_id:
        existing = await db.notifications.find_one({
            "$or": [
                {"recipient_user_id": user_oid},
                {"user_id": user_oid},
            ],
            "type": type,
            "related_entity_type": related_entity_type,
            "related_entity_id": str(related_entity_id),
        })
        if existing:
            return existing

    now = datetime.now(timezone.utc)
    doc = {
        "recipient_user_id": user_oid,
        "user_id": user_oid,  # compatibility alias
        "recipient_role": recipient_role,
        "type": type.strip().lower(),
        "title": title.strip(),
        "message": message.strip(),
        "related_entity_type": related_entity_type,
        "related_entity_id": str(related_entity_id) if related_entity_id else None,
        "is_read": False,
        "created_at": now,
        "read_at": None,
    }
    result = await db.notifications.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


async def get_notification_by_id(
    db: AsyncIOMotorDatabase,
    notification_id: str,
) -> Optional[dict]:
    try:
        oid = ObjectId(notification_id)
    except Exception:
        return None
    return await db.notifications.find_one({"_id": oid})


async def list_user_notifications(
    db: AsyncIOMotorDatabase,
    user_id: str,
    unread_only: bool = False,
    notification_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> list[dict]:
    try:
        u_oid = ObjectId(user_id)
    except Exception:
        return []

    query: dict = {
        "$or": [
            {"recipient_user_id": u_oid},
            {"user_id": u_oid},
        ]
    }
    if unread_only:
        query["is_read"] = False

    if notification_type:
        query["type"] = notification_type.strip().lower()

    cursor = db.notifications.find(query).sort("created_at", -1).skip(skip).limit(limit)
    return await cursor.to_list(length=limit)


async def count_unread_notifications(
    db: AsyncIOMotorDatabase,
    user_id: str,
) -> int:
    try:
        u_oid = ObjectId(user_id)
    except Exception:
        return 0

    query = {
        "$or": [
            {"recipient_user_id": u_oid},
            {"user_id": u_oid},
        ],
        "is_read": False,
    }
    return await db.notifications.count_documents(query)


async def mark_notification_as_read(
    db: AsyncIOMotorDatabase,
    notification_id: str,
) -> Optional[dict]:
    try:
        oid = ObjectId(notification_id)
    except Exception:
        return None

    now = datetime.now(timezone.utc)
    await db.notifications.update_one(
        {"_id": oid},
        {"$set": {"is_read": True, "read_at": now}},
    )
    return await db.notifications.find_one({"_id": oid})


async def mark_all_as_read(
    db: AsyncIOMotorDatabase,
    user_id: str,
) -> int:
    try:
        u_oid = ObjectId(user_id)
    except Exception:
        return 0

    now = datetime.now(timezone.utc)
    result = await db.notifications.update_many(
        {
            "$or": [
                {"recipient_user_id": u_oid},
                {"user_id": u_oid},
            ],
            "is_read": False,
        },
        {"$set": {"is_read": True, "read_at": now}},
    )
    return result.modified_count


async def delete_notification(
    db: AsyncIOMotorDatabase,
    notification_id: str,
) -> bool:
    try:
        oid = ObjectId(notification_id)
    except Exception:
        return False
    result = await db.notifications.delete_one({"_id": oid})
    return result.deleted_count > 0
