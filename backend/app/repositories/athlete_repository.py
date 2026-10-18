import re
from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase


async def get_athlete_by_id(db: AsyncIOMotorDatabase, athlete_id: str) -> Optional[dict]:
    try:
        oid = ObjectId(athlete_id)
    except Exception:
        return None
    return await db.athletes.find_one({"_id": oid})


async def get_athlete_by_user_id(db: AsyncIOMotorDatabase, user_id: str) -> Optional[dict]:
    try:
        oid = ObjectId(user_id)
    except Exception:
        return None
    return await db.athletes.find_one({"user_id": oid})


async def get_athlete_by_email(db: AsyncIOMotorDatabase, email: str) -> Optional[dict]:
    return await db.athletes.find_one({"email": email.strip().lower()})


def _build_athlete_query(
    search: Optional[str] = None,
    sport_id: Optional[str] = None,
    coach_id: Optional[str] = None,
    status: Optional[str] = None,
    allowed_athlete_ids: Optional[list[ObjectId]] = None,
) -> dict:
    conditions = []
    if allowed_athlete_ids is not None:
        conditions.append({"_id": {"$in": allowed_athlete_ids}})

    if search:
        pattern = re.escape(search.strip())
        conditions.append({
            "$or": [
                {"full_name": {"$regex": pattern, "$options": "i"}},
                {"email": {"$regex": pattern, "$options": "i"}},
                {"phone": {"$regex": pattern, "$options": "i"}},
            ]
        })

    if sport_id:
        s_matches = [str(sport_id)]
        try:
            s_matches.append(ObjectId(sport_id))
        except Exception:
            pass
        conditions.append({
            "$or": [
                {"sport_id": {"$in": s_matches}},
                {"additional_sport_ids": {"$in": s_matches}},
            ]
        })

    if coach_id:
        c_matches = [str(coach_id)]
        try:
            c_matches.append(ObjectId(coach_id))
        except Exception:
            pass
        conditions.append({"coach_id": {"$in": c_matches}})

    if status:
        conditions.append({"status": status})

    if not conditions:
        return {}
    if len(conditions) == 1:
        return conditions[0]
    return {"$and": conditions}


async def list_athletes(
    db: AsyncIOMotorDatabase,
    search: Optional[str] = None,
    sport_id: Optional[str] = None,
    coach_id: Optional[str] = None,
    status: Optional[str] = None,
    allowed_athlete_ids: Optional[list[ObjectId]] = None,
    skip: int = 0,
    limit: int = 100,
) -> list[dict]:
    query = _build_athlete_query(
        search=search,
        sport_id=sport_id,
        coach_id=coach_id,
        status=status,
        allowed_athlete_ids=allowed_athlete_ids,
    )
    cursor = db.athletes.find(query).sort("full_name", 1).skip(skip).limit(limit)
    return await cursor.to_list(length=limit)


async def count_athletes(
    db: AsyncIOMotorDatabase,
    search: Optional[str] = None,
    sport_id: Optional[str] = None,
    coach_id: Optional[str] = None,
    status: Optional[str] = None,
    allowed_athlete_ids: Optional[list[ObjectId]] = None,
) -> int:
    query = _build_athlete_query(
        search=search,
        sport_id=sport_id,
        coach_id=coach_id,
        status=status,
        allowed_athlete_ids=allowed_athlete_ids,
    )
    return await db.athletes.count_documents(query)


async def create_athlete(
    db: AsyncIOMotorDatabase,
    athlete_data: dict,
) -> dict:
    now = datetime.now(timezone.utc)
    athlete_data["created_at"] = now
    athlete_data["updated_at"] = now
    result = await db.athletes.insert_one(athlete_data)
    athlete_data["_id"] = result.inserted_id
    return athlete_data


async def update_athlete(
    db: AsyncIOMotorDatabase,
    athlete_id: str,
    update_data: dict,
) -> Optional[dict]:
    try:
        oid = ObjectId(athlete_id)
    except Exception:
        return None

    update_fields = {}
    for key, val in update_data.items():
        if val is not None:
            if key in ["sport_id", "coach_id"]:
                update_fields[key] = ObjectId(val) if val else None
            elif key == "additional_sport_ids":
                update_fields[key] = [ObjectId(s) for s in val]
            else:
                update_fields[key] = val.strip() if isinstance(val, str) else val

    if not update_fields:
        return await db.athletes.find_one({"_id": oid})

    update_fields["updated_at"] = datetime.now(timezone.utc)
    await db.athletes.update_one({"_id": oid}, {"$set": update_fields})
    return await db.athletes.find_one({"_id": oid})


async def set_athlete_status(
    db: AsyncIOMotorDatabase,
    athlete_id: str,
    status: str,
) -> Optional[dict]:
    try:
        oid = ObjectId(athlete_id)
    except Exception:
        return None
    now = datetime.now(timezone.utc)
    await db.athletes.update_one({"_id": oid}, {"$set": {"status": status, "updated_at": now}})
    return await db.athletes.find_one({"_id": oid})


async def set_athlete_coach(
    db: AsyncIOMotorDatabase,
    athlete_id: str,
    coach_id: Optional[str],
) -> Optional[dict]:
    try:
        ath_oid = ObjectId(athlete_id)
    except Exception:
        return None

    c_oid = ObjectId(coach_id) if coach_id else None
    now = datetime.now(timezone.utc)

    # First remove any old assignments for this athlete
    await db.coach_athlete_assignments.delete_many({"athlete_id": ath_oid})

    if c_oid:
        # Create assignment
        await db.coach_athlete_assignments.insert_one({
            "coach_id": c_oid,
            "athlete_id": ath_oid,
            "assigned_at": now,
        })

    await db.athletes.update_one(
        {"_id": ath_oid},
        {"$set": {"coach_id": c_oid, "updated_at": now}},
    )
    return await db.athletes.find_one({"_id": ath_oid})
