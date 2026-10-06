from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.exceptions import BadRequestError, ConflictError, ForbiddenError, NotFoundError
from app.repositories.coach_repository import (
    assign_athletes_to_coach,
    count_assigned_athletes,
    create_coach as repo_create_coach,
    get_coach_assigned_athlete_ids,
    get_coach_by_email,
    get_coach_by_id,
    get_coach_by_user_id,
    list_coaches as repo_list_coaches,
    remove_athlete_assignment,
    set_coach_status as repo_set_coach_status,
    update_coach as repo_update_coach,
)
from app.repositories.sport_repository import get_sport_by_id
from app.repositories.user_repository import create_user, get_user_by_email, get_user_by_id
from app.schemas.coach import CoachCreate, CoachResponse, CoachUpdate


async def _resolve_coach_response(db: AsyncIOMotorDatabase, doc: dict) -> CoachResponse:
    c_id = str(doc["_id"])
    ath_count = await count_assigned_athletes(db, c_id)
    sport_docs = []
    for s_id in doc.get("sport_ids", []):
        s = await db.sports.find_one({"_id": s_id})
        if s:
            sport_docs.append(s)
    return CoachResponse.from_doc(doc, sports=sport_docs, athlete_count=ath_count)


async def list_coaches_service(
    db: AsyncIOMotorDatabase,
    search: str = None,
    sport_id: str = None,
    status: str = None,
    skip: int = 0,
    limit: int = 100,
) -> list[CoachResponse]:
    docs = await repo_list_coaches(
        db, search=search, sport_id=sport_id, status=status, skip=skip, limit=limit
    )
    result = []
    for doc in docs:
        result.append(await _resolve_coach_response(db, doc))
    return result


async def get_coach_service(db: AsyncIOMotorDatabase, coach_id: str) -> CoachResponse:
    doc = await get_coach_by_id(db, coach_id)
    if not doc:
        raise NotFoundError("Coach not found")
    return await _resolve_coach_response(db, doc)


async def get_coach_by_user_id_service(db: AsyncIOMotorDatabase, user_id: str) -> CoachResponse:
    doc = await get_coach_by_user_id(db, user_id)
    if not doc:
        raise NotFoundError("Coach profile not found for this user")
    return await _resolve_coach_response(db, doc)


async def create_coach_service(db: AsyncIOMotorDatabase, data: CoachCreate) -> CoachResponse:
    # 1. Check if coach profile already exists for this email
    existing_coach = await get_coach_by_email(db, data.email)
    if existing_coach:
        raise ConflictError(f"A coach profile with email '{data.email}' already exists")

    # 2. Check if a user account exists, or create one
    user = await get_user_by_email(db, data.email)
    if user:
        if user["role"] != "coach":
            raise ConflictError(
                f"User with email '{data.email}' already exists with role '{user['role']}'"
            )
        user_id = user["_id"]
    else:
        password = data.password or "Coach@123"
        user = await create_user(
            db,
            email=data.email,
            full_name=data.full_name,
            plain_password=password,
            role="coach",
        )
        user_id = user["_id"]

    # 3. Validate sport_ids
    valid_sport_oids = []
    for sid in (data.sport_ids or []):
        sport = await get_sport_by_id(db, sid)
        if not sport:
            raise BadRequestError(f"Sport ID '{sid}' not found")
        if not sport.get("is_active", True):
            raise BadRequestError(f"Sport '{sport['name']}' is not active")
        valid_sport_oids.append(sport["_id"])

    # 4. Insert coach doc
    coach_doc = {
        "user_id": user_id,
        "full_name": data.full_name.strip(),
        "email": data.email.strip().lower(),
        "phone": data.phone.strip() if data.phone else None,
        "specialization": data.specialization.strip() if data.specialization else None,
        "experience_years": data.experience_years or 0,
        "sport_ids": valid_sport_oids,
        "bio": data.bio.strip() if data.bio else None,
        "status": data.status,
    }
    created = await repo_create_coach(db, coach_doc)
    return await _resolve_coach_response(db, created)


async def update_coach_service(
    db: AsyncIOMotorDatabase,
    coach_id: str,
    data: CoachUpdate,
    current_user: dict,
) -> CoachResponse:
    coach = await get_coach_by_id(db, coach_id)
    if not coach:
        raise NotFoundError("Coach not found")

    is_admin = current_user["role"] == "admin"
    is_self = str(coach.get("user_id", "")) == current_user["user_id"]

    if not is_admin and not is_self:
        raise ForbiddenError("You cannot modify another coach's profile")

    update_dict = {}
    if is_admin:
        # Admin can update full profile
        raw = data.model_dump(exclude_unset=True)
        if "sport_ids" in raw and raw["sport_ids"] is not None:
            valid_sport_oids = []
            for sid in raw["sport_ids"]:
                sport = await get_sport_by_id(db, sid)
                if not sport:
                    raise BadRequestError(f"Sport ID '{sid}' not found")
                valid_sport_oids.append(sport["_id"])
            update_dict["sport_ids"] = valid_sport_oids
        for k in ["full_name", "phone", "specialization", "experience_years", "bio", "status"]:
            if k in raw:
                update_dict[k] = raw[k]
    else:
        # Coach can only update phone and bio
        if data.phone is not None:
            update_dict["phone"] = data.phone
        if data.bio is not None:
            update_dict["bio"] = data.bio

    updated = await repo_update_coach(db, coach_id, update_dict)
    # If full_name changed and user exists, update user doc
    if is_admin and "full_name" in update_dict and coach.get("user_id"):
        await db.users.update_one(
            {"_id": coach["user_id"]},
            {"$set": {"full_name": update_dict["full_name"]}},
        )

    return await _resolve_coach_response(db, updated)


async def set_coach_status_service(
    db: AsyncIOMotorDatabase, coach_id: str, status: str
) -> CoachResponse:
    coach = await get_coach_by_id(db, coach_id)
    if not coach:
        raise NotFoundError("Coach not found")

    updated = await repo_set_coach_status(db, coach_id, status)
    # Also update user active flag
    if coach.get("user_id"):
        await db.users.update_one(
            {"_id": coach["user_id"]},
            {"$set": {"is_active": (status == "active")}},
        )
    return await _resolve_coach_response(db, updated)


async def assign_athletes_to_coach_service(
    db: AsyncIOMotorDatabase, coach_id: str, athlete_ids: list[str]
) -> dict:
    coach = await get_coach_by_id(db, coach_id)
    if not coach:
        raise NotFoundError("Coach not found")

    # Validate athletes
    for a_id in athlete_ids:
        try:
            ath = await db.athletes.find_one({"_id": ObjectId(a_id)})
            if not ath:
                raise NotFoundError(f"Athlete with ID '{a_id}' not found")
        except Exception:
            raise BadRequestError(f"Invalid athlete ID '{a_id}'")

    await assign_athletes_to_coach(db, coach_id, athlete_ids)
    return {"message": f"Successfully assigned {len(athlete_ids)} athlete(s) to coach"}


async def remove_athlete_assignment_service(
    db: AsyncIOMotorDatabase, coach_id: str, athlete_id: str
) -> dict:
    coach = await get_coach_by_id(db, coach_id)
    if not coach:
        raise NotFoundError("Coach not found")

    await remove_athlete_assignment(db, coach_id, athlete_id)
    return {"message": "Athlete assignment removed successfully"}
