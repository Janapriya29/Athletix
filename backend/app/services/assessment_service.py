import logging
from datetime import datetime, timezone
from typing import Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.repositories.assessment_repository import (
    create_assessment as repo_create_assessment,
    get_assessment_by_id as repo_get_assessment_by_id,
    get_athlete_assessment_history as repo_get_athlete_assessment_history,
    list_assessments as repo_list_assessments,
)
from app.repositories.athlete_repository import (
    get_athlete_by_id,
    get_athlete_by_user_id,
)
from app.repositories.coach_repository import (
    get_coach_assigned_athlete_ids,
    get_coach_by_id,
    get_coach_by_user_id,
)
from app.repositories.sport_repository import get_sport_by_id
from app.schemas.assessment import AssessmentCreate, AssessmentResponse
from app.services.notification_service import (
    get_coach_user_ids_for_athlete,
    notify_assessment_created,
    notify_coach_assessment,
)

logger = logging.getLogger(__name__)


async def _resolve_doc_names(db: AsyncIOMotorDatabase, doc: dict) -> AssessmentResponse:
    athlete_name = None
    if doc.get("athlete_id"):
        ath_matches = [str(doc["athlete_id"])]
        try:
            ath_matches.append(ObjectId(doc["athlete_id"]))
        except Exception:
            pass
        ath = await db.athletes.find_one({"_id": {"$in": ath_matches}})
        if ath:
            athlete_name = ath.get("full_name")

    coach_name = None
    if doc.get("coach_id"):
        c_matches = [str(doc["coach_id"])]
        try:
            c_matches.append(ObjectId(doc["coach_id"]))
        except Exception:
            pass
        coach = await db.coaches.find_one({"_id": {"$in": c_matches}})
        if coach:
            coach_name = coach.get("full_name")

    sport_name = None
    if doc.get("sport_id"):
        s_matches = [str(doc["sport_id"])]
        try:
            s_matches.append(ObjectId(doc["sport_id"]))
        except Exception:
            pass
        sport = await db.sports.find_one({"_id": {"$in": s_matches}})
        if sport:
            sport_name = sport.get("name")

    return AssessmentResponse.from_doc(
        doc,
        athlete_name=athlete_name,
        coach_name=coach_name,
        sport_name=sport_name,
    )


async def create_assessment_service(
    db: AsyncIOMotorDatabase,
    data: AssessmentCreate,
    current_user: dict,
) -> AssessmentResponse:
    role = current_user.get("role")
    user_id = current_user.get("user_id")

    if role == "athlete":
        raise ForbiddenError("Athletes cannot create performance assessments")

    # 1. Validate athlete exists and is active
    athlete = await get_athlete_by_id(db, data.athlete_id)
    if not athlete:
        raise NotFoundError("Athlete not found")
    if athlete.get("status") != "active":
        raise BadRequestError(f"Athlete '{athlete.get('full_name')}' is inactive")

    # 2. RBAC assignment checks
    coach_oid = None
    if role == "coach":
        coach = await get_coach_by_user_id(db, user_id)
        if not coach:
            raise ForbiddenError("Coach profile not found")

        assigned_ids = await get_coach_assigned_athlete_ids(db, str(coach["_id"]))
        assigned_strs = {str(x) for x in assigned_ids}
        is_direct = str(athlete.get("coach_id", "")) == str(coach["_id"])
        is_assigned = str(athlete["_id"]) in assigned_strs

        if not is_direct and not is_assigned:
            raise ForbiddenError(f"Athlete '{athlete.get('full_name')}' is not assigned to you")

        coach_oid = coach["_id"]
    elif role == "admin":
        if data.coach_id:
            c = await get_coach_by_id(db, data.coach_id)
            if not c:
                raise BadRequestError("Coach not found")
            coach_oid = c["_id"]
        elif athlete.get("coach_id"):
            coach_oid = athlete["coach_id"]

    # 3. Sport validation
    sport_oid = None
    sport_name = None
    if data.sport_id:
        sport = await get_sport_by_id(db, data.sport_id)
        if not sport:
            raise BadRequestError("Sport not found")
        # Validate athlete is registered for this sport
        ath_sports = {str(athlete.get("sport_id", ""))}
        for sid in athlete.get("additional_sport_ids") or []:
            if sid:
                ath_sports.add(str(sid))
        if str(sport["_id"]) not in ath_sports:
            raise BadRequestError(f"Athlete '{athlete.get('full_name')}' is not enrolled in sport '{sport['name']}'")
        sport_oid = sport["_id"]
        sport_name = sport.get("name")
    else:
        if not athlete.get("sport_id"):
            raise BadRequestError("Athlete does not have a primary sport assigned")
        sport_oid = athlete["sport_id"]
        sport = await get_sport_by_id(db, str(sport_oid))
        if sport:
            sport_name = sport.get("name")

    # 4. Overall score calculation
    if data.overall_score is not None:
        overall_score = round(float(data.overall_score), 2)
    else:
        overall_score = round(sum(data.metrics.values()) / len(data.metrics), 2)

    # 5. Assessment date
    assessment_date = data.date or datetime.now(timezone.utc)
    if assessment_date.tzinfo is None:
        assessment_date = assessment_date.replace(tzinfo=timezone.utc)

    # 6. Insert doc
    now = datetime.now(timezone.utc)
    # Ensure keys are lowercase string
    cleaned_metrics = {str(k).lower(): round(float(v), 2) for k, v in data.metrics.items()}
    doc = {
        "athlete_id": athlete["_id"],
        "coach_id": coach_oid,
        "sport_id": sport_oid,
        "date": assessment_date,
        "metrics": cleaned_metrics,
        "overall_score": overall_score,
        "remarks": data.remarks.strip() if data.remarks else None,
        "created_at": now,
    }

    inserted = await repo_create_assessment(db, doc)

    # 7. Notify athlete
    if athlete.get("user_id"):
        try:
            await notify_assessment_created(
                db,
                str(athlete["user_id"]),
                overall_score,
                str(inserted["_id"]),
            )
        except Exception as e:
            logger.warning("Failed to send assessment notification: %s", e)

    # 8. Notify assigned coaches
    try:
        coach_user_ids = await get_coach_user_ids_for_athlete(db, athlete)
        ath_name = athlete.get("full_name") or "Athlete"
        for c_uid in coach_user_ids:
            if str(c_uid) != str(user_id):
                await notify_coach_assessment(
                    db,
                    coach_user_id=str(c_uid),
                    athlete_name=ath_name,
                    overall_score=overall_score,
                    assessment_id=str(inserted["_id"]),
                    athlete_id=str(athlete["_id"]),
                )
    except Exception as e:
        logger.warning("Failed to notify coach of assessment: %s", e)

    coach_name = None
    if coach_oid:
        c_doc = await db.coaches.find_one({"_id": coach_oid})
        if c_doc:
            coach_name = c_doc.get("full_name")

    return AssessmentResponse.from_doc(
        inserted,
        athlete_name=athlete.get("full_name"),
        coach_name=coach_name,
        sport_name=sport_name,
    )


async def list_assessments_service(
    db: AsyncIOMotorDatabase,
    current_user: dict,
    athlete_id: Optional[str] = None,
    coach_id: Optional[str] = None,
    sport_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
) -> list[AssessmentResponse]:
    role = current_user.get("role")
    user_id = current_user.get("user_id")

    allowed_athlete_ids = None

    if role == "athlete":
        ath = await get_athlete_by_user_id(db, user_id)
        if not ath:
            return []
        ath_id_str = str(ath["_id"])
        if athlete_id and athlete_id != ath_id_str:
            raise ForbiddenError("You can only view your own assessments")
        athlete_id = ath_id_str
        allowed_athlete_ids = [ath["_id"]]

    elif role == "coach":
        coach = await get_coach_by_user_id(db, user_id)
        if not coach:
            return []
        c_id = str(coach["_id"])
        assigned_ids = await get_coach_assigned_athlete_ids(db, c_id)
        cursor = db.athletes.find({"coach_id": coach["_id"]}, {"_id": 1})
        direct_docs = await cursor.to_list(length=500)
        direct_ids = [d["_id"] for d in direct_docs]
        all_assigned = list(set(assigned_ids + direct_ids))

        if athlete_id:
            assigned_strs = {str(x) for x in all_assigned}
            if athlete_id not in assigned_strs:
                raise ForbiddenError("Athlete is not assigned to you")
        allowed_athlete_ids = all_assigned

    docs = await repo_list_assessments(
        db,
        athlete_id=athlete_id,
        coach_id=coach_id,
        sport_id=sport_id,
        allowed_athlete_ids=allowed_athlete_ids,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit,
    )

    # Batch resolve names
    if not docs:
        return []

    ath_ids = {d["athlete_id"] for d in docs if d.get("athlete_id")}
    coach_ids = {d["coach_id"] for d in docs if d.get("coach_id")}
    sport_ids = {d["sport_id"] for d in docs if d.get("sport_id")}

    ath_map = {}
    if ath_ids:
        aths = await db.athletes.find({"_id": {"$in": list(ath_ids)}}).to_list(length=len(ath_ids))
        ath_map = {str(a["_id"]): a.get("full_name") for a in aths}

    coach_map = {}
    if coach_ids:
        coaches = await db.coaches.find({"_id": {"$in": list(coach_ids)}}).to_list(length=len(coach_ids))
        coach_map = {str(c["_id"]): c.get("full_name") for c in coaches}

    sport_map = {}
    if sport_ids:
        sports = await db.sports.find({"_id": {"$in": list(sport_ids)}}).to_list(length=len(sport_ids))
        sport_map = {str(s["_id"]): s.get("name") for s in sports}

    responses = []
    for d in docs:
        a_id = str(d.get("athlete_id", ""))
        c_id = str(d.get("coach_id", ""))
        s_id = str(d.get("sport_id", ""))
        responses.append(
            AssessmentResponse.from_doc(
                d,
                athlete_name=ath_map.get(a_id),
                coach_name=coach_map.get(c_id),
                sport_name=sport_map.get(s_id),
            )
        )
    return responses


async def get_assessment_service(
    db: AsyncIOMotorDatabase,
    assessment_id: str,
    current_user: dict,
) -> AssessmentResponse:
    doc = await repo_get_assessment_by_id(db, assessment_id)
    if not doc:
        raise NotFoundError("Assessment not found")

    role = current_user.get("role")
    user_id = current_user.get("user_id")

    if role == "athlete":
        ath = await get_athlete_by_user_id(db, user_id)
        if not ath or str(doc.get("athlete_id", "")) != str(ath["_id"]):
            raise ForbiddenError("You cannot access another athlete's assessment")

    elif role == "coach":
        coach = await get_coach_by_user_id(db, user_id)
        if not coach:
            raise ForbiddenError("Coach profile not found")

        is_creator = str(doc.get("coach_id", "")) == str(coach["_id"])
        if not is_creator:
            assigned_ids = await get_coach_assigned_athlete_ids(db, str(coach["_id"]))
            assigned_strs = {str(x) for x in assigned_ids}
            ath_doc = await db.athletes.find_one({"_id": doc["athlete_id"]})
            is_direct = ath_doc and str(ath_doc.get("coach_id", "")) == str(coach["_id"])
            if str(doc["athlete_id"]) not in assigned_strs and not is_direct:
                raise ForbiddenError("You cannot access assessments for athletes not assigned to you")

    return await _resolve_doc_names(db, doc)


async def get_athlete_assessments_service(
    db: AsyncIOMotorDatabase,
    athlete_id: str,
    current_user: dict,
) -> list[AssessmentResponse]:
    athlete = await get_athlete_by_id(db, athlete_id)
    if not athlete:
        raise NotFoundError("Athlete not found")

    role = current_user.get("role")
    user_id = current_user.get("user_id")

    if role == "athlete":
        if str(athlete.get("user_id", "")) != str(user_id):
            raise ForbiddenError("You cannot view assessments for another athlete")

    elif role == "coach":
        coach = await get_coach_by_user_id(db, user_id)
        if not coach:
            raise ForbiddenError("Coach profile not found")

        assigned_ids = await get_coach_assigned_athlete_ids(db, str(coach["_id"]))
        assigned_strs = {str(x) for x in assigned_ids}
        is_direct = str(athlete.get("coach_id", "")) == str(coach["_id"])
        is_assigned = str(athlete["_id"]) in assigned_strs
        if not is_direct and not is_assigned:
            raise ForbiddenError("You cannot view assessments for athletes not assigned to you")

    docs = await repo_get_athlete_assessment_history(db, athlete_id)
    responses = []
    for d in docs:
        responses.append(await _resolve_doc_names(db, d))
    return responses
