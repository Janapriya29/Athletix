from datetime import datetime, timezone
from typing import Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.exceptions import BadRequestError, ConflictError, ForbiddenError, NotFoundError
from app.repositories.athlete_repository import (
    create_athlete as repo_create_athlete,
    get_athlete_by_email,
    get_athlete_by_id,
    get_athlete_by_user_id,
    list_athletes as repo_list_athletes,
    set_athlete_coach as repo_set_athlete_coach,
    set_athlete_status as repo_set_athlete_status,
    update_athlete as repo_update_athlete,
)
from app.repositories.coach_repository import (
    get_coach_assigned_athlete_ids,
    get_coach_by_id,
    get_coach_by_user_id,
)
from app.repositories.sport_repository import get_sport_by_id
from app.repositories.user_repository import create_user, get_user_by_email
from app.schemas.athlete import (
    AssignedCoachInfo,
    AthleteAssignCoach,
    AthleteAssignSport,
    AthleteCreate,
    AthleteResponse,
    AthleteSelfUpdate,
    AthleteUpdate,
)


async def _resolve_athlete_response(db: AsyncIOMotorDatabase, doc: dict) -> AthleteResponse:
    sport_name = None
    if doc.get("sport_id"):
        sport = await db.sports.find_one({"_id": doc["sport_id"]})
        if sport:
            sport_name = sport.get("name")

    coach_name = None
    if doc.get("coach_id"):
        coach = await db.coaches.find_one({"_id": doc["coach_id"]})
        if coach:
            coach_name = coach.get("full_name")

    return AthleteResponse.from_doc(doc, sport_name=sport_name, coach_name=coach_name)


async def list_athletes_service(
    db: AsyncIOMotorDatabase,
    current_user: dict,
    search: str = None,
    sport_id: str = None,
    coach_id: str = None,
    status: str = None,
    skip: int = 0,
    limit: int = 100,
) -> list[AthleteResponse]:
    role = current_user["role"]
    user_id = current_user["user_id"]

    allowed_ids = None

    if role == "athlete":
        # Athlete can only see their own profile
        my_athlete = await get_athlete_by_user_id(db, user_id)
        if not my_athlete:
            return []
        allowed_ids = [my_athlete["_id"]]

    elif role == "coach":
        # Coach can only see their assigned athletes
        coach = await get_coach_by_user_id(db, user_id)
        if not coach:
            return []
        c_id = str(coach["_id"])
        assigned_ids = await get_coach_assigned_athlete_ids(db, c_id)
        # Also check if any athlete has this coach_id directly
        cursor = db.athletes.find({"coach_id": coach["_id"]}, {"_id": 1})
        direct_docs = await cursor.to_list(length=500)
        direct_ids = [d["_id"] for d in direct_docs]
        all_ids = list(set(assigned_ids + direct_ids))
        allowed_ids = all_ids

    docs = await repo_list_athletes(
        db,
        search=search,
        sport_id=sport_id,
        coach_id=coach_id,
        status=status,
        allowed_athlete_ids=allowed_ids,
        skip=skip,
        limit=limit,
    )
    result = []
    for d in docs:
        result.append(await _resolve_athlete_response(db, d))
    return result


async def get_athlete_service(
    db: AsyncIOMotorDatabase, athlete_id: str, current_user: dict
) -> AthleteResponse:
    doc = await get_athlete_by_id(db, athlete_id)
    if not doc:
        raise NotFoundError("Athlete not found")

    role = current_user["role"]
    user_id = current_user["user_id"]

    if role == "athlete":
        if str(doc.get("user_id", "")) != user_id:
            raise ForbiddenError("You can only view your own athlete profile")

    elif role == "coach":
        coach = await get_coach_by_user_id(db, user_id)
        if not coach:
            raise ForbiddenError("Coach profile not found")
        assigned_ids = await get_coach_assigned_athlete_ids(db, str(coach["_id"]))
        is_direct = str(doc.get("coach_id", "")) == str(coach["_id"])
        is_assigned = doc["_id"] in assigned_ids
        if not is_direct and not is_assigned:
            raise ForbiddenError("You are not assigned to this athlete")

    return await _resolve_athlete_response(db, doc)


async def get_athlete_by_user_id_service(
    db: AsyncIOMotorDatabase, user_id: str
) -> AthleteResponse:
    doc = await get_athlete_by_user_id(db, user_id)
    if not doc:
        raise NotFoundError("Athlete profile not found for this user")
    return await _resolve_athlete_response(db, doc)


async def get_my_coach_service(
    db: AsyncIOMotorDatabase, user_id: str
) -> AssignedCoachInfo:
    ath = await get_athlete_by_user_id(db, user_id)
    if not ath:
        raise NotFoundError("Athlete profile not found")

    if not ath.get("coach_id"):
        raise NotFoundError("No coach is currently assigned to you")

    coach = await db.coaches.find_one({"_id": ath["coach_id"]})
    if not coach:
        raise NotFoundError("Assigned coach record not found")

    return AssignedCoachInfo(
        coach_id=str(coach["_id"]),
        full_name=coach.get("full_name", ""),
        email=coach.get("email", ""),
        phone=coach.get("phone"),
        specialization=coach.get("specialization"),
        bio=coach.get("bio"),
    )


async def create_athlete_service(db: AsyncIOMotorDatabase, data: AthleteCreate) -> AthleteResponse:
    # 1. Check if athlete already exists
    existing = await get_athlete_by_email(db, data.email)
    if existing:
        raise ConflictError(f"An athlete profile with email '{data.email}' already exists")

    # 2. Check user account or create one
    user = await get_user_by_email(db, data.email)
    if user:
        if user["role"] != "athlete":
            raise ConflictError(
                f"User with email '{data.email}' already exists with role '{user['role']}'"
            )
        user_id = user["_id"]
    else:
        password = data.password or "Athlete@123"
        user = await create_user(
            db,
            email=data.email,
            full_name=data.full_name,
            plain_password=password,
            role="athlete",
        )
        user_id = user["_id"]

    # 3. Validate primary sport
    sport = await get_sport_by_id(db, data.sport_id)
    if not sport:
        raise BadRequestError(f"Sport ID '{data.sport_id}' not found")
    if not sport.get("is_active", True):
        raise BadRequestError(f"Sport '{sport['name']}' is not active")
    primary_sport_oid = sport["_id"]

    # 4. Validate additional sports
    add_sport_oids = []
    for sid in (data.additional_sport_ids or []):
        s = await get_sport_by_id(db, sid)
        if not s:
            raise BadRequestError(f"Additional sport ID '{sid}' not found")
        add_sport_oids.append(s["_id"])

    # 5. Validate coach if provided
    coach_oid = None
    if data.coach_id:
        coach = await get_coach_by_id(db, data.coach_id)
        if not coach:
            raise BadRequestError(f"Coach ID '{data.coach_id}' not found")
        if coach.get("status") != "active":
            raise BadRequestError("Assigned coach is not active")
        coach_oid = coach["_id"]

    # 6. Insert athlete doc
    athlete_doc = {
        "user_id": user_id,
        "full_name": data.full_name.strip(),
        "email": data.email.strip().lower(),
        "phone": data.phone.strip() if data.phone else None,
        "date_of_birth": data.date_of_birth,
        "gender": data.gender,
        "sport_id": primary_sport_oid,
        "additional_sport_ids": add_sport_oids,
        "coach_id": coach_oid,
        "address": data.address.strip() if data.address else None,
        "emergency_contact": data.emergency_contact.strip() if data.emergency_contact else None,
        "joining_date": data.joining_date or datetime.now(timezone.utc),
        "status": data.status,
    }
    created = await repo_create_athlete(db, athlete_doc)

    # 7. Create coach_athlete_assignment if coach_oid is present
    if coach_oid:
        now = datetime.now(timezone.utc)
        await db.coach_athlete_assignments.update_one(
            {"coach_id": coach_oid, "athlete_id": created["_id"]},
            {"$set": {"assigned_at": now}},
            upsert=True,
        )

    return await _resolve_athlete_response(db, created)


async def update_athlete_service(
    db: AsyncIOMotorDatabase,
    athlete_id: str,
    data: AthleteUpdate,
    current_user: dict,
) -> AthleteResponse:
    athlete = await get_athlete_by_id(db, athlete_id)
    if not athlete:
        raise NotFoundError("Athlete not found")

    is_admin = current_user["role"] == "admin"
    is_self = str(athlete.get("user_id", "")) == current_user["user_id"]

    if not is_admin and not is_self:
        raise ForbiddenError("You cannot modify another athlete's profile")

    update_dict = {}
    if is_admin:
        raw = data.model_dump(exclude_unset=True)
        # Validate sport_id if changed
        if "sport_id" in raw and raw["sport_id"]:
            sport = await get_sport_by_id(db, raw["sport_id"])
            if not sport:
                raise BadRequestError(f"Sport ID '{raw['sport_id']}' not found")
            update_dict["sport_id"] = str(sport["_id"])

        # Validate additional_sport_ids
        if "additional_sport_ids" in raw and raw["additional_sport_ids"] is not None:
            valid_adds = []
            for sid in raw["additional_sport_ids"]:
                s = await get_sport_by_id(db, sid)
                if not s:
                    raise BadRequestError(f"Sport ID '{sid}' not found")
                valid_adds.append(str(s["_id"]))
            update_dict["additional_sport_ids"] = valid_adds

        # Validate coach_id if changed
        if "coach_id" in raw:
            if raw["coach_id"]:
                coach = await get_coach_by_id(db, raw["coach_id"])
                if not coach:
                    raise BadRequestError(f"Coach ID '{raw['coach_id']}' not found")
                update_dict["coach_id"] = str(coach["_id"])
                # Sync coach_athlete_assignments
                now = datetime.now(timezone.utc)
                await db.coach_athlete_assignments.delete_many({"athlete_id": athlete["_id"]})
                await db.coach_athlete_assignments.insert_one({
                    "coach_id": coach["_id"],
                    "athlete_id": athlete["_id"],
                    "assigned_at": now,
                })
            else:
                update_dict["coach_id"] = None
                await db.coach_athlete_assignments.delete_many({"athlete_id": athlete["_id"]})

        for k in ["full_name", "phone", "date_of_birth", "gender", "address", "emergency_contact", "status"]:
            if k in raw:
                update_dict[k] = raw[k]
    else:
        # Athlete self update: only phone, address, emergency_contact
        raw = data.model_dump(exclude_unset=True)
        for k in ["phone", "address", "emergency_contact"]:
            if k in raw:
                update_dict[k] = raw[k]

    updated = await repo_update_athlete(db, athlete_id, update_dict)
    # Sync user full_name if updated
    if is_admin and "full_name" in update_dict and athlete.get("user_id"):
        await db.users.update_one(
            {"_id": athlete["user_id"]},
            {"$set": {"full_name": update_dict["full_name"]}},
        )

    return await _resolve_athlete_response(db, updated)


async def set_athlete_status_service(
    db: AsyncIOMotorDatabase, athlete_id: str, status: str
) -> AthleteResponse:
    athlete = await get_athlete_by_id(db, athlete_id)
    if not athlete:
        raise NotFoundError("Athlete not found")

    updated = await repo_set_athlete_status(db, athlete_id, status)
    if athlete.get("user_id"):
        await db.users.update_one(
            {"_id": athlete["user_id"]},
            {"$set": {"is_active": (status == "active")}},
        )
    return await _resolve_athlete_response(db, updated)


async def assign_coach_service(
    db: AsyncIOMotorDatabase, athlete_id: str, coach_id: Optional[str]
) -> AthleteResponse:
    athlete = await get_athlete_by_id(db, athlete_id)
    if not athlete:
        raise NotFoundError("Athlete not found")

    if coach_id:
        coach = await get_coach_by_id(db, coach_id)
        if not coach:
            raise BadRequestError("Coach not found")
        if coach.get("status") != "active":
            raise BadRequestError("Coach is not active")

    updated = await repo_set_athlete_coach(db, athlete_id, coach_id)
    return await _resolve_athlete_response(db, updated)


async def assign_sport_service(
    db: AsyncIOMotorDatabase, athlete_id: str, data: AthleteAssignSport
) -> AthleteResponse:
    athlete = await get_athlete_by_id(db, athlete_id)
    if not athlete:
        raise NotFoundError("Athlete not found")

    sport = await get_sport_by_id(db, data.sport_id)
    if not sport:
        raise BadRequestError(f"Sport ID '{data.sport_id}' not found")
    if not sport.get("is_active", True):
        raise BadRequestError(f"Sport '{sport['name']}' is not active")

    add_oids = []
    for sid in (data.additional_sport_ids or []):
        s = await get_sport_by_id(db, sid)
        if not s:
            raise BadRequestError(f"Sport ID '{sid}' not found")
        add_oids.append(str(s["_id"]))

    update_dict = {
        "sport_id": str(sport["_id"]),
        "additional_sport_ids": add_oids,
    }
    updated = await repo_update_athlete(db, athlete_id, update_dict)
    return await _resolve_athlete_response(db, updated)
