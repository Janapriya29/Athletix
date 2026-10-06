from datetime import datetime
from typing import Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase


async def get_athlete_assessments(
    db: AsyncIOMotorDatabase,
    athlete_id: str,
    sort_ascending: bool = False,
) -> list[dict]:
    """
    Get all performance assessments for an athlete.
    Default sort is descending by date (latest first).
    """
    try:
        a_oid = ObjectId(athlete_id)
    except Exception:
        return []

    sort_order = 1 if sort_ascending else -1
    cursor = db.performance_assessments.find({"athlete_id": a_oid}).sort("date", sort_order)
    return await cursor.to_list(length=1000)


async def count_total_assessments(
    db: AsyncIOMotorDatabase,
    sport_id: Optional[str] = None,
) -> int:
    """Count total performance assessments, optionally filtered by sport."""
    query = {}
    if sport_id:
        try:
            query["sport_id"] = ObjectId(sport_id)
        except Exception:
            return 0
    return await db.performance_assessments.count_documents(query)


async def get_athlete_applicable_sessions(
    db: AsyncIOMotorDatabase,
    athlete_id: str,
) -> list[dict]:
    """
    Get all non-cancelled training sessions where athlete is a participant.
    """
    try:
        a_oid = ObjectId(athlete_id)
    except Exception:
        return []

    cursor = db.training_sessions.find({
        "athlete_ids": a_oid,
        "status": {"$ne": "cancelled"},
    }).sort([("session_date", -1), ("date", -1)])
    return await cursor.to_list(length=1000)


async def get_athlete_attendance_records(
    db: AsyncIOMotorDatabase,
    athlete_id: str,
) -> list[dict]:
    """Get all attendance records for an athlete."""
    try:
        a_oid = ObjectId(athlete_id)
    except Exception:
        return []

    cursor = db.attendance.find({"athlete_id": a_oid})
    return await cursor.to_list(length=1000)
