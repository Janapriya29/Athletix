import re
from datetime import datetime, timezone
from typing import Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase


# ── Tournaments Collection ─────────────────────────────────────────────────────

async def create_tournament(db: AsyncIOMotorDatabase, doc: dict) -> dict:
    now = datetime.now(timezone.utc)
    doc["created_at"] = doc.get("created_at") or now
    doc["updated_at"] = doc.get("updated_at") or now
    result = await db.tournaments.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


async def get_tournament_by_id(db: AsyncIOMotorDatabase, tournament_id: str) -> Optional[dict]:
    try:
        oid = ObjectId(tournament_id)
    except Exception:
        return None
    return await db.tournaments.find_one({"_id": oid})


async def get_tournament_by_name(db: AsyncIOMotorDatabase, name: str) -> Optional[dict]:
    pattern = f"^{re.escape(name.strip())}$"
    return await db.tournaments.find_one({"name": {"$regex": pattern, "$options": "i"}})


async def list_tournaments(
    db: AsyncIOMotorDatabase,
    search: Optional[str] = None,
    sport_id: Optional[str] = None,
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
            {"name": {"$regex": pattern, "$options": "i"}},
            {"description": {"$regex": pattern, "$options": "i"}},
            {"location": {"$regex": pattern, "$options": "i"}},
            {"venue": {"$regex": pattern, "$options": "i"}},
        ]

    if sport_id:
        s_matches = [str(sport_id)]
        try:
            s_matches.append(ObjectId(sport_id))
        except Exception:
            pass
        query["sport_id"] = {"$in": s_matches}

    if status:
        query["status"] = status.strip().lower()

    if start_date or end_date:
        date_q = {}
        if start_date:
            date_q["$gte"] = start_date
        if end_date:
            date_q["$lte"] = end_date
        query["start_date"] = date_q

    cursor = db.tournaments.find(query).sort("start_date", 1).skip(skip).limit(limit)
    return await cursor.to_list(length=limit)


async def count_tournaments(
    db: AsyncIOMotorDatabase,
    search: Optional[str] = None,
    sport_id: Optional[str] = None,
    status: Optional[str] = None,
) -> int:
    query = {}
    if search:
        pattern = re.escape(search.strip())
        query["$or"] = [
            {"name": {"$regex": pattern, "$options": "i"}},
            {"description": {"$regex": pattern, "$options": "i"}},
        ]
    if sport_id:
        s_matches = [str(sport_id)]
        try:
            s_matches.append(ObjectId(sport_id))
        except Exception:
            pass
        query["sport_id"] = {"$in": s_matches}
    if status:
        query["status"] = status.strip().lower()
    return await db.tournaments.count_documents(query)


async def update_tournament(
    db: AsyncIOMotorDatabase,
    tournament_id: str,
    update_doc: dict,
) -> Optional[dict]:
    try:
        oid = ObjectId(tournament_id)
    except Exception:
        return None
    update_doc["updated_at"] = datetime.now(timezone.utc)
    await db.tournaments.update_one({"_id": oid}, {"$set": update_doc})
    return await db.tournaments.find_one({"_id": oid})


async def delete_tournament(
    db: AsyncIOMotorDatabase,
    tournament_id: str,
) -> bool:
    try:
        oid = ObjectId(tournament_id)
    except Exception:
        return False
    # Remove participants as well
    await db.tournament_participants.delete_many({"tournament_id": oid})
    result = await db.tournaments.delete_one({"_id": oid})
    return result.deleted_count > 0


# ── Tournament Participants & Results ──────────────────────────────────────────

async def get_participant(
    db: AsyncIOMotorDatabase,
    tournament_id: str,
    athlete_id: str,
) -> Optional[dict]:
    t_matches = [str(tournament_id)]
    a_matches = [str(athlete_id)]
    try:
        t_matches.append(ObjectId(tournament_id))
    except Exception:
        pass
    try:
        a_matches.append(ObjectId(athlete_id))
    except Exception:
        pass
    return await db.tournament_participants.find_one({
        "tournament_id": {"$in": t_matches},
        "athlete_id": {"$in": a_matches},
    })


async def add_participant(
    db: AsyncIOMotorDatabase,
    tournament_id: str,
    athlete_id: str,
    event: Optional[str] = None,
    registered_by: Optional[str] = None,
) -> dict:
    try:
        t_oid = ObjectId(tournament_id)
    except Exception:
        t_oid = tournament_id
    try:
        a_oid = ObjectId(athlete_id)
    except Exception:
        a_oid = athlete_id

    rb_oid = None
    if registered_by:
        try:
            rb_oid = ObjectId(registered_by)
        except Exception:
            rb_oid = registered_by
    now = datetime.now(timezone.utc)

    doc = {
        "tournament_id": t_oid,
        "athlete_id": a_oid,
        "event": event.strip() if event else None,
        "status": "registered",
        "registered_by": rb_oid,
        "registered_at": now,
        "position": None,
        "score": None,
        "points": None,
        "medal": None,
        "remarks": None,
        "created_at": now,
        "updated_at": now,
    }
    result = await db.tournament_participants.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


async def remove_participant(
    db: AsyncIOMotorDatabase,
    tournament_id: str,
    athlete_id: str,
) -> bool:
    t_matches = [str(tournament_id)]
    a_matches = [str(athlete_id)]
    try:
        t_matches.append(ObjectId(tournament_id))
    except Exception:
        pass
    try:
        a_matches.append(ObjectId(athlete_id))
    except Exception:
        pass
    result = await db.tournament_participants.delete_one({
        "tournament_id": {"$in": t_matches},
        "athlete_id": {"$in": a_matches},
    })
    return result.deleted_count > 0


async def get_participants(
    db: AsyncIOMotorDatabase,
    tournament_id: str,
) -> list[dict]:
    t_matches = [str(tournament_id)]
    try:
        t_matches.append(ObjectId(tournament_id))
    except Exception:
        pass
    cursor = db.tournament_participants.find({"tournament_id": {"$in": t_matches}}).sort("registered_at", 1)
    return await cursor.to_list(length=1000)


async def count_participants(
    db: AsyncIOMotorDatabase,
    tournament_id: str,
) -> int:
    t_matches = [str(tournament_id)]
    try:
        t_matches.append(ObjectId(tournament_id))
    except Exception:
        pass
    return await db.tournament_participants.count_documents({"tournament_id": {"$in": t_matches}})


async def get_athlete_participations(
    db: AsyncIOMotorDatabase,
    athlete_id: str,
) -> list[dict]:
    a_matches = [str(athlete_id)]
    try:
        a_matches.append(ObjectId(athlete_id))
    except Exception:
        pass
    cursor = db.tournament_participants.find({"athlete_id": {"$in": a_matches}})
    return await cursor.to_list(length=1000)


async def update_result(
    db: AsyncIOMotorDatabase,
    tournament_id: str,
    athlete_id: str,
    result_fields: dict,
    recorded_by: Optional[str] = None,
) -> Optional[dict]:
    t_matches = [str(tournament_id)]
    a_matches = [str(athlete_id)]
    try:
        t_matches.append(ObjectId(tournament_id))
    except Exception:
        pass
    try:
        a_matches.append(ObjectId(athlete_id))
    except Exception:
        pass

    now = datetime.now(timezone.utc)
    set_doc = {
        **result_fields,
        "updated_at": now,
        "result_date": now,
        "status": "participated",
    }
    if recorded_by:
        try:
            set_doc["recorded_by"] = ObjectId(recorded_by)
        except Exception:
            set_doc["recorded_by"] = recorded_by

    q = {
        "tournament_id": {"$in": t_matches},
        "athlete_id": {"$in": a_matches},
    }
    await db.tournament_participants.update_one(q, {"$set": set_doc})
    return await db.tournament_participants.find_one(q)


async def get_all_participations_with_results(
    db: AsyncIOMotorDatabase,
) -> list[dict]:
    cursor = db.tournament_participants.find()
    return await cursor.to_list(length=5000)
