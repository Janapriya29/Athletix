import re
from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase


async def get_coach_by_id(db: AsyncIOMotorDatabase, coach_id: str) -> Optional[dict]:
    try:
        oid = ObjectId(coach_id)
    except Exception:
        return None
    return await db.coaches.find_one({"_id": oid})


async def get_coach_by_user_id(db: AsyncIOMotorDatabase, user_id: str) -> Optional[dict]:
    try:
        oid = ObjectId(user_id)
    except Exception:
        return None
    return await db.coaches.find_one({"user_id": oid})


async def get_coach_by_email(db: AsyncIOMotorDatabase, email: str) -> Optional[dict]:
    return await db.coaches.find_one({"email": email.strip().lower()})


async def list_coaches(
    db: AsyncIOMotorDatabase,
    search: Optional[str] = None,
    sport_id: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> list[dict]:
    query = {}
    if search:
        pattern = re.escape(search.strip())
        query["$or"] = [
            {"full_name": {"$regex": pattern, "$options": "i"}},
            {"email": {"$regex": pattern, "$options": "i"}},
            {"specialization": {"$regex": pattern, "$options": "i"}},
        ]
    if sport_id:
        try:
            s_oid = ObjectId(sport_id)
            query["sport_ids"] = s_oid
        except Exception:
            return []
    if status:
        query["status"] = status

    cursor = db.coaches.find(query).sort("full_name", 1).skip(skip).limit(limit)
    return await cursor.to_list(length=limit)


async def count_coaches(
    db: AsyncIOMotorDatabase,
    search: Optional[str] = None,
    sport_id: Optional[str] = None,
    status: Optional[str] = None,
) -> int:
    query = {}
    if search:
        pattern = re.escape(search.strip())
        query["$or"] = [
            {"full_name": {"$regex": pattern, "$options": "i"}},
            {"email": {"$regex": pattern, "$options": "i"}},
            {"specialization": {"$regex": pattern, "$options": "i"}},
        ]
    if sport_id:
        try:
            query["sport_ids"] = ObjectId(sport_id)
        except Exception:
            return 0
    if status:
        query["status"] = status

    return await db.coaches.count_documents(query)


async def create_coach(
    db: AsyncIOMotorDatabase,
    coach_data: dict,
) -> dict:
    now = datetime.now(timezone.utc)
    coach_data["created_at"] = now
    coach_data["updated_at"] = now
    result = await db.coaches.insert_one(coach_data)
    coach_data["_id"] = result.inserted_id
    return coach_data


async def update_coach(
    db: AsyncIOMotorDatabase,
    coach_id: str,
    update_data: dict,
) -> Optional[dict]:
    try:
        oid = ObjectId(coach_id)
    except Exception:
        return None

    update_fields = {}
    for key, val in update_data.items():
        if val is not None:
            if key == "sport_ids":
                # Convert string IDs to ObjectIds
                update_fields["sport_ids"] = [
                    ObjectId(sid) if isinstance(sid, str) else sid for sid in val
                ]
            else:
                update_fields[key] = val.strip() if isinstance(val, str) else val

    if not update_fields:
        return await db.coaches.find_one({"_id": oid})

    update_fields["updated_at"] = datetime.now(timezone.utc)
    await db.coaches.update_one({"_id": oid}, {"$set": update_fields})
    return await db.coaches.find_one({"_id": oid})


async def set_coach_status(
    db: AsyncIOMotorDatabase,
    coach_id: str,
    status: str,
) -> Optional[dict]:
    try:
        oid = ObjectId(coach_id)
    except Exception:
        return None
    now = datetime.now(timezone.utc)
    await db.coaches.update_one({"_id": oid}, {"$set": {"status": status, "updated_at": now}})
    return await db.coaches.find_one({"_id": oid})


async def get_coach_assigned_athlete_ids(
    db: AsyncIOMotorDatabase,
    coach_id: str,
) -> list[ObjectId]:
    try:
        c_oid = ObjectId(coach_id)
    except Exception:
        return []
    cursor = db.coach_athlete_assignments.find({"coach_id": c_oid})
    docs = await cursor.to_list(length=500)
    return [d["athlete_id"] for d in docs]


async def count_assigned_athletes(
    db: AsyncIOMotorDatabase,
    coach_id: str,
) -> int:
    try:
        c_oid = ObjectId(coach_id)
    except Exception:
        return 0
    return await db.coach_athlete_assignments.count_documents({"coach_id": c_oid})


async def assign_athletes_to_coach(
    db: AsyncIOMotorDatabase,
    coach_id: str,
    athlete_ids: list[str],
) -> None:
    c_oid = ObjectId(coach_id)
    now = datetime.now(timezone.utc)
    for a_id in athlete_ids:
        try:
            ath_oid = ObjectId(a_id)
        except Exception:
            continue
        # Upsert assignment
        await db.coach_athlete_assignments.update_one(
            {"coach_id": c_oid, "athlete_id": ath_oid},
            {"$set": {"assigned_at": now}},
            upsert=True,
        )
        # Also update coach_id on the athlete doc for quick reference
        await db.athletes.update_one(
            {"_id": ath_oid},
            {"$set": {"coach_id": c_oid, "updated_at": now}},
        )


async def remove_athlete_assignment(
    db: AsyncIOMotorDatabase,
    coach_id: str,
    athlete_id: str,
) -> None:
    try:
        c_oid = ObjectId(coach_id)
        ath_oid = ObjectId(athlete_id)
    except Exception:
        return
    await db.coach_athlete_assignments.delete_one({"coach_id": c_oid, "athlete_id": ath_oid})
    # If the athlete's primary coach was this coach, set coach_id to None
    await db.athletes.update_one(
        {"_id": ath_oid, "coach_id": c_oid},
        {"$set": {"coach_id": None, "updated_at": datetime.now(timezone.utc)}},
    )
