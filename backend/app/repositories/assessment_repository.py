from datetime import datetime, timezone
from typing import Optional, Union
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase


async def create_assessment(db: AsyncIOMotorDatabase, doc: dict) -> dict:
    """Inserts a performance assessment document into MongoDB."""
    if "created_at" not in doc:
        doc["created_at"] = datetime.now(timezone.utc)
    if "date" not in doc:
        doc["date"] = doc["created_at"]
    result = await db.performance_assessments.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


async def get_assessment_by_id(db: AsyncIOMotorDatabase, assessment_id: str) -> Optional[dict]:
    """Finds a single assessment by its ObjectId or string ID."""
    match_ids = [str(assessment_id)]
    try:
        match_ids.append(ObjectId(assessment_id))
    except Exception:
        pass
    return await db.performance_assessments.find_one({"_id": {"$in": match_ids}})


async def list_assessments(
    db: AsyncIOMotorDatabase,
    athlete_id: Optional[str] = None,
    coach_id: Optional[str] = None,
    sport_id: Optional[str] = None,
    allowed_athlete_ids: Optional[list] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
) -> list[dict]:
    """Queries performance assessments with optional filters, sorted by date descending."""
    query = {}

    # Athlete filtering
    if athlete_id:
        ath_matches: list[Union[ObjectId, str]] = [str(athlete_id)]
        try:
            ath_matches.append(ObjectId(athlete_id))
        except Exception:
            pass

        if allowed_athlete_ids is not None:
            allowed_set = {str(x) for x in allowed_athlete_ids}
            if str(athlete_id) not in allowed_set:
                return []
            query["athlete_id"] = {"$in": ath_matches}
        else:
            query["athlete_id"] = {"$in": ath_matches}
    elif allowed_athlete_ids is not None:
        if not allowed_athlete_ids:
            return []
        all_matches = []
        for a in allowed_athlete_ids:
            all_matches.append(str(a))
            try:
                all_matches.append(ObjectId(a))
            except Exception:
                pass
        query["athlete_id"] = {"$in": all_matches}

    # Coach filtering
    if coach_id:
        c_matches = [str(coach_id)]
        try:
            c_matches.append(ObjectId(coach_id))
        except Exception:
            pass
        query["coach_id"] = {"$in": c_matches}

    # Sport filtering
    if sport_id:
        s_matches = [str(sport_id)]
        try:
            s_matches.append(ObjectId(sport_id))
        except Exception:
            pass
        query["sport_id"] = {"$in": s_matches}

    # Date range filtering
    if start_date or end_date:
        date_q = {}
        if start_date:
            date_q["$gte"] = start_date
        if end_date:
            date_q["$lte"] = end_date
        query["date"] = date_q

    cursor = db.performance_assessments.find(query).sort([("date", -1), ("created_at", -1)]).skip(skip).limit(limit)
    return await cursor.to_list(length=limit)


async def count_assessments(
    db: AsyncIOMotorDatabase,
    athlete_id: Optional[str] = None,
    coach_id: Optional[str] = None,
    sport_id: Optional[str] = None,
    allowed_athlete_ids: Optional[list] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> int:
    """Counts performance assessments matching filters."""
    query = {}
    if athlete_id:
        ath_matches: list[Union[ObjectId, str]] = [str(athlete_id)]
        try:
            ath_matches.append(ObjectId(athlete_id))
        except Exception:
            pass

        if allowed_athlete_ids is not None:
            allowed_set = {str(x) for x in allowed_athlete_ids}
            if str(athlete_id) not in allowed_set:
                return 0
            query["athlete_id"] = {"$in": ath_matches}
        else:
            query["athlete_id"] = {"$in": ath_matches}
    elif allowed_athlete_ids is not None:
        if not allowed_athlete_ids:
            return 0
        all_matches = []
        for a in allowed_athlete_ids:
            all_matches.append(str(a))
            try:
                all_matches.append(ObjectId(a))
            except Exception:
                pass
        query["athlete_id"] = {"$in": all_matches}

    if coach_id:
        c_matches = [str(coach_id)]
        try:
            c_matches.append(ObjectId(coach_id))
        except Exception:
            pass
        query["coach_id"] = {"$in": c_matches}

    if sport_id:
        s_matches = [str(sport_id)]
        try:
            s_matches.append(ObjectId(sport_id))
        except Exception:
            pass
        query["sport_id"] = {"$in": s_matches}

    if start_date or end_date:
        date_q = {}
        if start_date:
            date_q["$gte"] = start_date
        if end_date:
            date_q["$lte"] = end_date
        query["date"] = date_q

    return await db.performance_assessments.count_documents(query)


async def get_athlete_assessment_history(
    db: AsyncIOMotorDatabase,
    athlete_id: str,
) -> list[dict]:
    """Gets all assessments for an athlete, latest first."""
    matches = [str(athlete_id)]
    try:
        matches.append(ObjectId(athlete_id))
    except Exception:
        pass
    cursor = db.performance_assessments.find({"athlete_id": {"$in": matches}}).sort([("date", -1), ("created_at", -1)])
    return await cursor.to_list(length=1000)
