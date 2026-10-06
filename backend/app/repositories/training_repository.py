import re
from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase


# ── Training Sessions ──────────────────────────────────────────────────────────

async def get_session_by_id(db: AsyncIOMotorDatabase, session_id: str) -> Optional[dict]:
    try:
        oid = ObjectId(session_id)
    except Exception:
        return None
    return await db.training_sessions.find_one({"_id": oid})


async def list_sessions(
    db: AsyncIOMotorDatabase,
    search: Optional[str] = None,
    sport_id: Optional[str] = None,
    coach_id: Optional[str] = None,
    athlete_id: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
) -> list[dict]:
    query = {}
    if search:
        pattern = re.escape(search.strip())
        query["$or"] = [
            {"title": {"$regex": pattern, "$options": "i"}},
            {"description": {"$regex": pattern, "$options": "i"}},
            {"location": {"$regex": pattern, "$options": "i"}},
            {"venue": {"$regex": pattern, "$options": "i"}},
        ]
    if sport_id:
        try:
            query["sport_id"] = ObjectId(sport_id)
        except Exception:
            return []
    if coach_id:
        try:
            query["coach_id"] = ObjectId(coach_id)
        except Exception:
            return []
    if athlete_id:
        try:
            query["athlete_ids"] = ObjectId(athlete_id)
        except Exception:
            return []
    if status:
        query["status"] = status.lower()

    if start_date or end_date:
        date_q = {}
        if start_date:
            date_q["$gte"] = start_date
        if end_date:
            date_q["$lte"] = end_date
        # check both session_date and date field
        query["$and"] = query.get("$and", []) + [
            {"$or": [{"session_date": date_q}, {"date": date_q}]}
        ]

    # Sort by date/session_date descending
    cursor = db.training_sessions.find(query).sort([("session_date", -1), ("date", -1)]).skip(skip).limit(limit)
    return await cursor.to_list(length=limit)


async def count_sessions(
    db: AsyncIOMotorDatabase,
    sport_id: Optional[str] = None,
    coach_id: Optional[str] = None,
    athlete_id: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> int:
    query = {}
    if sport_id:
        try:
            query["sport_id"] = ObjectId(sport_id)
        except Exception:
            return 0
    if coach_id:
        try:
            query["coach_id"] = ObjectId(coach_id)
        except Exception:
            return 0
    if athlete_id:
        try:
            query["athlete_ids"] = ObjectId(athlete_id)
        except Exception:
            return 0
    if status:
        query["status"] = status.lower()
    if start_date or end_date:
        date_q = {}
        if start_date:
            date_q["$gte"] = start_date
        if end_date:
            date_q["$lte"] = end_date
        query["$or"] = [{"session_date": date_q}, {"date": date_q}]

    return await db.training_sessions.count_documents(query)


async def create_session(
    db: AsyncIOMotorDatabase,
    session_data: dict,
) -> dict:
    now = datetime.now(timezone.utc)
    session_data["created_at"] = now
    session_data["updated_at"] = now
    # Ensure date and session_date are both set for full compatibility
    dt_val = session_data.get("session_date") or session_data.get("date") or now
    session_data["session_date"] = dt_val
    session_data["date"] = dt_val
    result = await db.training_sessions.insert_one(session_data)
    session_data["_id"] = result.inserted_id
    return session_data


async def update_session(
    db: AsyncIOMotorDatabase,
    session_id: str,
    update_data: dict,
) -> Optional[dict]:
    try:
        oid = ObjectId(session_id)
    except Exception:
        return None

    update_fields = {}
    for key, val in update_data.items():
        if val is not None:
            if key in ["sport_id", "coach_id"]:
                update_fields[key] = ObjectId(val)
            elif key == "session_date":
                update_fields["session_date"] = val
                update_fields["date"] = val
            elif key == "athlete_ids":
                update_fields["athlete_ids"] = [
                    ObjectId(aid) if isinstance(aid, str) else aid for aid in val
                ]
            else:
                update_fields[key] = val.strip() if isinstance(val, str) else val

    if not update_fields:
        return await db.training_sessions.find_one({"_id": oid})

    update_fields["updated_at"] = datetime.now(timezone.utc)
    await db.training_sessions.update_one({"_id": oid}, {"$set": update_fields})
    return await db.training_sessions.find_one({"_id": oid})


async def set_session_status(
    db: AsyncIOMotorDatabase,
    session_id: str,
    status: str,
) -> Optional[dict]:
    try:
        oid = ObjectId(session_id)
    except Exception:
        return None
    now = datetime.now(timezone.utc)
    await db.training_sessions.update_one(
        {"_id": oid},
        {"$set": {"status": status.lower(), "updated_at": now}},
    )
    return await db.training_sessions.find_one({"_id": oid})


async def add_participant_to_session(
    db: AsyncIOMotorDatabase,
    session_id: str,
    athlete_id: str,
) -> Optional[dict]:
    try:
        s_oid = ObjectId(session_id)
        a_oid = ObjectId(athlete_id)
    except Exception:
        return None

    now = datetime.now(timezone.utc)
    await db.training_sessions.update_one(
        {"_id": s_oid},
        {
            "$addToSet": {"athlete_ids": a_oid},
            "$set": {"updated_at": now},
        },
    )
    return await db.training_sessions.find_one({"_id": s_oid})


async def remove_participant_from_session(
    db: AsyncIOMotorDatabase,
    session_id: str,
    athlete_id: str,
) -> Optional[dict]:
    try:
        s_oid = ObjectId(session_id)
        a_oid = ObjectId(athlete_id)
    except Exception:
        return None

    now = datetime.now(timezone.utc)
    await db.training_sessions.update_one(
        {"_id": s_oid},
        {
            "$pull": {"athlete_ids": a_oid},
            "$set": {"updated_at": now},
        },
    )
    # Also delete any attendance record for this athlete in this session
    await db.attendance.delete_many({"session_id": s_oid, "athlete_id": a_oid})
    return await db.training_sessions.find_one({"_id": s_oid})


# ── Attendance ─────────────────────────────────────────────────────────────────

async def get_session_attendance(
    db: AsyncIOMotorDatabase, session_id: str
) -> list[dict]:
    try:
        s_oid = ObjectId(session_id)
    except Exception:
        return []
    cursor = db.attendance.find({"session_id": s_oid})
    return await cursor.to_list(length=500)


async def get_athlete_attendance_record(
    db: AsyncIOMotorDatabase, session_id: str, athlete_id: str
) -> Optional[dict]:
    try:
        s_oid = ObjectId(session_id)
        a_oid = ObjectId(athlete_id)
    except Exception:
        return None
    return await db.attendance.find_one({"session_id": s_oid, "athlete_id": a_oid})


async def get_athlete_attendance_records(
    db: AsyncIOMotorDatabase, athlete_id: str
) -> list[dict]:
    try:
        a_oid = ObjectId(athlete_id)
    except Exception:
        return []
    cursor = db.attendance.find({"athlete_id": a_oid})
    return await cursor.to_list(length=1000)


async def upsert_attendance_record(
    db: AsyncIOMotorDatabase,
    session_id: str,
    athlete_id: str,
    status: str,
    marked_by: str,
    remarks: Optional[str] = None,
) -> dict:
    s_oid = ObjectId(session_id)
    a_oid = ObjectId(athlete_id)
    m_oid = ObjectId(marked_by) if marked_by else None
    now = datetime.now(timezone.utc)

    filter_q = {"session_id": s_oid, "athlete_id": a_oid}
    update_doc = {
        "$set": {
            "status": status.lower(),
            "marked_by": m_oid,
            "recorded_by": m_oid,
            "marked_at": now,
            "recorded_at": now,
            "remarks": remarks.strip() if remarks else None,
            "updated_at": now,
        },
        "$setOnInsert": {
            "created_at": now,
        },
    }

    result = await db.attendance.find_one_and_update(
        filter_q,
        update_doc,
        upsert=True,
        return_document=True,
    )
    return result
