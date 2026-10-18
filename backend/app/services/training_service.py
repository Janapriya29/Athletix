from datetime import date, datetime, timezone
from typing import Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.exceptions import (
    BadRequestError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
)
from app.repositories.athlete_repository import get_athlete_by_id, get_athlete_by_user_id
from app.repositories.coach_repository import (
    get_coach_assigned_athlete_ids,
    get_coach_by_id,
    get_coach_by_user_id,
)
from app.repositories.sport_repository import get_sport_by_id
from app.repositories.training_repository import (
    add_participant_to_session,
    count_sessions,
    create_session as repo_create_session,
    get_athlete_attendance_records,
    get_session_attendance,
    get_session_by_id,
    list_sessions as repo_list_sessions,
    remove_participant_from_session,
    set_session_status as repo_set_session_status,
    update_session as repo_update_session,
    upsert_attendance_record,
)
from app.schemas.training import (
    AdminTrainingSummary,
    AthleteAttendanceSummary,
    AttendanceBulkCreate,
    AttendanceRecordCreate,
    AttendanceResponse,
    CoachTrainingSummary,
    ParticipantInfo,
    TrainingSessionCreate,
    TrainingSessionResponse,
    TrainingSessionUpdate,
)

ATTENDANCE_WARNING_THRESHOLD = 75.0


# ── Helper: Resolve details for response ───────────────────────────────────────

async def _resolve_session_response(
    db: AsyncIOMotorDatabase, session_doc: dict
) -> TrainingSessionResponse:
    s_id = str(session_doc["_id"])

    # Sport name
    sport_name = None
    if session_doc.get("sport_id"):
        sport = await db.sports.find_one({"_id": session_doc["sport_id"]})
        if sport:
            sport_name = sport.get("name")

    # Coach name
    coach_name = None
    if session_doc.get("coach_id"):
        coach = await db.coaches.find_one({"_id": session_doc["coach_id"]})
        if coach:
            coach_name = coach.get("full_name")

    # Attendance map for this session
    attendance_docs = await get_session_attendance(db, s_id)
    att_map = {str(a["athlete_id"]): a for a in attendance_docs}

    # Participants list
    participants = []
    for ath_oid in session_doc.get("athlete_ids", []):
        ath = await db.athletes.find_one({"_id": ath_oid})
        if ath:
            a_id_str = str(ath["_id"])
            att_entry = att_map.get(a_id_str)
            att_status = att_entry.get("status") if att_entry else None
            remarks = att_entry.get("remarks") if att_entry else None

            # Athlete primary sport name
            ath_sport_name = None
            if ath.get("sport_id"):
                asport = await db.sports.find_one({"_id": ath["sport_id"]})
                if asport:
                    ath_sport_name = asport.get("name")

            participants.append(
                ParticipantInfo(
                    athlete_id=a_id_str,
                    full_name=ath.get("full_name", ""),
                    email=ath.get("email", ""),
                    sport_name=ath_sport_name,
                    attendance_status=att_status,
                    remarks=remarks,
                )
            )

    return TrainingSessionResponse.from_doc(
        session_doc,
        sport_name=sport_name,
        coach_name=coach_name,
        participants=participants,
    )


# ── Sessions ───────────────────────────────────────────────────────────────────

async def list_sessions_service(
    db: AsyncIOMotorDatabase,
    current_user: dict,
    search: Optional[str] = None,
    sport_id: Optional[str] = None,
    coach_id: Optional[str] = None,
    athlete_id: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
) -> list[TrainingSessionResponse]:
    role = current_user["role"]
    user_id = current_user["user_id"]

    if role == "athlete":
        # Athlete can only see their own sessions
        ath = await get_athlete_by_user_id(db, user_id)
        if not ath:
            return []
        athlete_id = str(ath["_id"])

    elif role == "coach":
        # Coach can only see their own sessions
        coach = await get_coach_by_user_id(db, user_id)
        if not coach:
            return []
        coach_id = str(coach["_id"])

    docs = await repo_list_sessions(
        db,
        search=search,
        sport_id=sport_id,
        coach_id=coach_id,
        athlete_id=athlete_id,
        status=status,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit,
    )
    results = []
    for d in docs:
        results.append(await _resolve_session_response(db, d))
    return results


async def get_session_service(
    db: AsyncIOMotorDatabase, session_id: str, current_user: dict
) -> TrainingSessionResponse:
    session = await get_session_by_id(db, session_id)
    if not session:
        raise NotFoundError("Training session not found")

    role = current_user["role"]
    user_id = current_user["user_id"]

    if role == "coach":
        coach = await get_coach_by_user_id(db, user_id)
        if not coach or str(session.get("coach_id", "")) != str(coach["_id"]):
            raise ForbiddenError("You cannot access another coach's training session")

    elif role == "athlete":
        ath = await get_athlete_by_user_id(db, user_id)
        if not ath or ath["_id"] not in session.get("athlete_ids", []):
            raise ForbiddenError("You are not a participant in this training session")

    return await _resolve_session_response(db, session)


async def create_session_service(
    db: AsyncIOMotorDatabase, data: TrainingSessionCreate, current_user: dict
) -> TrainingSessionResponse:
    role = current_user["role"]
    user_id = current_user["user_id"]

    if role == "athlete":
        raise ForbiddenError("Athletes cannot create training sessions")

    # 1. Validate sport exists and is active
    sport = await get_sport_by_id(db, data.sport_id)
    if not sport:
        raise BadRequestError("Sport not found")
    if not sport.get("is_active", True):
        raise BadRequestError(f"Sport '{sport['name']}' is currently inactive")

    # 2. Validate coach
    coach = await get_coach_by_id(db, data.coach_id)
    if not coach:
        raise BadRequestError("Coach not found")
    if coach.get("status") != "active":
        raise BadRequestError(f"Coach '{coach['full_name']}' is currently inactive")

    # If role is coach, must be creating session for oneself
    if role == "coach":
        my_coach = await get_coach_by_user_id(db, user_id)
        if not my_coach or str(my_coach["_id"]) != data.coach_id:
            raise ForbiddenError("Coaches can only create training sessions for themselves")

    # Validate coach is assigned to this sport
    if coach.get("sport_ids") and sport["_id"] not in coach["sport_ids"]:
        raise BadRequestError(f"Coach '{coach['full_name']}' is not assigned to sport '{sport['name']}'")

    # 3. Validate initial athlete_ids if provided
    valid_athlete_oids = []
    if data.athlete_ids:
        assigned_athlete_ids = None
        if role == "coach":
            assigned_athlete_ids = await get_coach_assigned_athlete_ids(db, data.coach_id)

        for a_id in data.athlete_ids:
            ath = await get_athlete_by_id(db, a_id)
            if not ath:
                raise BadRequestError(f"Athlete ID '{a_id}' not found")
            if ath.get("status") != "active":
                raise BadRequestError(f"Athlete '{ath['full_name']}' is inactive")
            # If coach, must be assigned to this coach
            if role == "coach":
                assigned_strs = {str(x) for x in assigned_athlete_ids}
                is_direct = str(ath.get("coach_id", "")) == data.coach_id
                is_assigned = str(ath["_id"]) in assigned_strs
                if not is_direct and not is_assigned:
                    raise ForbiddenError(f"Athlete '{ath['full_name']}' is not assigned to you")
            # Athlete sport validation: must match session sport or be an additional sport
            ath_sports = {
                str(sid)
                for sid in ([ath.get("sport_id")] + (ath.get("additional_sport_ids") or []))
                if sid is not None and str(sid) not in ("", "None")
            }
            if str(sport["_id"]) not in ath_sports:
                raise BadRequestError(
                    f"Athlete '{ath['full_name']}' does not participate in sport '{sport['name']}'"
                )
            if ath["_id"] not in valid_athlete_oids:
                valid_athlete_oids.append(ath["_id"])

    session_doc = {
        "title": data.title.strip(),
        "description": data.description.strip() if data.description else None,
        "sport_id": sport["_id"],
        "coach_id": coach["_id"],
        "session_date": data.session_date,
        "date": data.session_date,
        "start_time": data.start_time,
        "end_time": data.end_time,
        "location": data.location.strip() if data.location else "Academy Ground",
        "venue": data.location.strip() if data.location else "Academy Ground",
        "athlete_ids": valid_athlete_oids,
        "status": data.status.lower(),
    }
    created = await repo_create_session(db, session_doc)
    try:
        from app.services.notification_service import notify_training_created
        await notify_training_created(db, created)
    except Exception as exc:
        logger.warning("Failed to dispatch training created notification: %s", exc)
    return await _resolve_session_response(db, created)


async def update_session_service(
    db: AsyncIOMotorDatabase,
    session_id: str,
    data: TrainingSessionUpdate,
    current_user: dict,
) -> TrainingSessionResponse:
    session = await get_session_by_id(db, session_id)
    if not session:
        raise NotFoundError("Training session not found")

    role = current_user["role"]
    user_id = current_user["user_id"]

    if role == "athlete":
        raise ForbiddenError("Athletes cannot update training sessions")

    if role == "coach":
        coach = await get_coach_by_user_id(db, user_id)
        if not coach or str(session.get("coach_id", "")) != str(coach["_id"]):
            raise ForbiddenError("You cannot modify another coach's session")

    update_dict = data.model_dump(exclude_unset=True)

    # Validate sport if changing
    if "sport_id" in update_dict and update_dict["sport_id"]:
        sport = await get_sport_by_id(db, update_dict["sport_id"])
        if not sport:
            raise BadRequestError("Sport not found")
        if not sport.get("is_active", True):
            raise BadRequestError("Sport is not active")

    # Validate coach if changing (Admin only)
    if "coach_id" in update_dict and update_dict["coach_id"]:
        if role != "admin":
            raise ForbiddenError("Only admins can reassign a session to a different coach")
        coach = await get_coach_by_id(db, update_dict["coach_id"])
        if not coach:
            raise BadRequestError("Coach not found")
        if coach.get("status") != "active":
            raise BadRequestError("Coach is not active")

    updated = await repo_update_session(db, session_id, update_dict)
    if update_dict.get("status", "").lower() == "cancelled":
        try:
            from app.services.notification_service import notify_training_cancelled
            await notify_training_cancelled(db, updated)
        except Exception as exc:
            logger.warning("Failed to dispatch training cancelled notification: %s", exc)
    return await _resolve_session_response(db, updated)


async def set_session_status_service(
    db: AsyncIOMotorDatabase,
    session_id: str,
    status: str,
    current_user: dict,
) -> TrainingSessionResponse:
    session = await get_session_by_id(db, session_id)
    if not session:
        raise NotFoundError("Training session not found")

    role = current_user["role"]
    user_id = current_user["user_id"]

    if role == "athlete":
        raise ForbiddenError("Athletes cannot change session status")

    if role == "coach":
        coach = await get_coach_by_user_id(db, user_id)
        if not coach or str(session.get("coach_id", "")) != str(coach["_id"]):
            raise ForbiddenError("You cannot change status of another coach's session")

    updated = await repo_set_session_status(db, session_id, status)
    if status.lower() == "cancelled":
        try:
            from app.services.notification_service import notify_training_cancelled
            await notify_training_cancelled(db, updated)
        except Exception as exc:
            logger.warning("Failed to dispatch training cancelled notification: %s", exc)
    return await _resolve_session_response(db, updated)


# ── Participants ───────────────────────────────────────────────────────────────

async def add_participant_service(
    db: AsyncIOMotorDatabase,
    session_id: str,
    athlete_id: str,
    current_user: dict,
) -> TrainingSessionResponse:
    session = await get_session_by_id(db, session_id)
    if not session:
        raise NotFoundError("Training session not found")

    role = current_user["role"]
    user_id = current_user["user_id"]

    if role == "athlete":
        raise ForbiddenError("Athletes cannot manage session participants")

    if role == "coach":
        coach = await get_coach_by_user_id(db, user_id)
        if not coach or str(session.get("coach_id", "")) != str(coach["_id"]):
            raise ForbiddenError("You cannot manage participants for another coach's session")

    # Validate athlete
    ath = await get_athlete_by_id(db, athlete_id)
    if not ath:
        raise BadRequestError(f"Athlete ID '{athlete_id}' not found")
    if ath.get("status") != "active":
        raise BadRequestError(f"Athlete '{ath['full_name']}' is inactive")

    # If coach, must be assigned to this coach
    if role == "coach":
        assigned_ids = await get_coach_assigned_athlete_ids(db, str(session["coach_id"]))
        assigned_strs = {str(x) for x in assigned_ids}
        is_direct = str(ath.get("coach_id", "")) == str(session["coach_id"])
        is_assigned = str(ath["_id"]) in assigned_strs
        if not is_direct and not is_assigned:
            raise ForbiddenError(f"Athlete '{ath['full_name']}' is not assigned to you")

    # Check duplicate
    if ath["_id"] in session.get("athlete_ids", []):
        raise ConflictError(f"Athlete '{ath['full_name']}' is already a participant in this session")

    # Check sport compatibility
    ath_sports = {
        str(sid)
        for sid in ([ath.get("sport_id")] + (ath.get("additional_sport_ids") or []))
        if sid is not None and str(sid) not in ("", "None")
    }
    if str(session["sport_id"]) not in ath_sports:
        sport = await db.sports.find_one({"_id": session["sport_id"]})
        sport_name = sport.get("name") if sport else "this sport"
        raise BadRequestError(f"Athlete '{ath['full_name']}' is not registered for {sport_name}")

    updated = await add_participant_to_session(db, session_id, athlete_id)
    return await _resolve_session_response(db, updated)


async def remove_participant_service(
    db: AsyncIOMotorDatabase,
    session_id: str,
    athlete_id: str,
    current_user: dict,
) -> TrainingSessionResponse:
    session = await get_session_by_id(db, session_id)
    if not session:
        raise NotFoundError("Training session not found")

    role = current_user["role"]
    user_id = current_user["user_id"]

    if role == "athlete":
        raise ForbiddenError("Athletes cannot manage participants")

    if role == "coach":
        coach = await get_coach_by_user_id(db, user_id)
        if not coach or str(session.get("coach_id", "")) != str(coach["_id"]):
            raise ForbiddenError("You cannot manage participants for another coach's session")

    updated = await remove_participant_from_session(db, session_id, athlete_id)
    return await _resolve_session_response(db, updated)


# ── Attendance ─────────────────────────────────────────────────────────────────

async def get_session_attendance_service(
    db: AsyncIOMotorDatabase, session_id: str, current_user: dict
) -> list[AttendanceResponse]:
    session = await get_session_by_id(db, session_id)
    if not session:
        raise NotFoundError("Training session not found")

    role = current_user["role"]
    user_id = current_user["user_id"]

    if role == "coach":
        coach = await get_coach_by_user_id(db, user_id)
        if not coach or str(session.get("coach_id", "")) != str(coach["_id"]):
            raise ForbiddenError("You cannot view attendance for another coach's session")

    elif role == "athlete":
        raise ForbiddenError("Athletes cannot view session-wide attendance records")

    docs = await get_session_attendance(db, session_id)
    results = []
    for d in docs:
        ath = await db.athletes.find_one({"_id": d["athlete_id"]})
        ath_name = ath.get("full_name") if ath else "Unknown"
        results.append(
            AttendanceResponse(
                id=str(d["_id"]),
                session_id=str(d["session_id"]),
                athlete_id=str(d["athlete_id"]),
                athlete_name=ath_name,
                status=d["status"],
                marked_by=str(d.get("marked_by") or d.get("recorded_by") or ""),
                marked_at=d.get("marked_at") or d.get("recorded_at"),
                remarks=d.get("remarks"),
                created_at=d.get("created_at"),
                updated_at=d.get("updated_at"),
            )
        )
    return results


async def record_attendance_service(
    db: AsyncIOMotorDatabase,
    session_id: str,
    record: AttendanceRecordCreate,
    current_user: dict,
) -> AttendanceResponse:
    session = await get_session_by_id(db, session_id)
    if not session:
        raise NotFoundError("Training session not found")

    role = current_user["role"]
    user_id = current_user["user_id"]

    if role == "athlete":
        raise ForbiddenError("Athletes cannot record attendance")

    if role == "coach":
        coach = await get_coach_by_user_id(db, user_id)
        if not coach or str(session.get("coach_id", "")) != str(coach["_id"]):
            raise ForbiddenError("You cannot record attendance for another coach's session")

    # Validate athlete is in session's participants
    try:
        a_oid = ObjectId(record.athlete_id)
    except Exception:
        raise BadRequestError("Invalid athlete ID")

    if a_oid not in session.get("athlete_ids", []):
        raise BadRequestError("Athlete is not a participant in this training session")

    updated_record = await upsert_attendance_record(
        db,
        session_id=session_id,
        athlete_id=record.athlete_id,
        status=record.status,
        marked_by=user_id,
        remarks=record.remarks,
    )

    ath = await db.athletes.find_one({"_id": a_oid})
    ath_name = ath.get("full_name") if ath else "Unknown"

    if ath and ath.get("user_id"):
        try:
            from app.services.notification_service import notify_attendance_recorded
            s_date = session.get("session_date") or session.get("date")
            s_date_str = s_date.strftime("%b %d, %Y") if hasattr(s_date, "strftime") else str(s_date)
            await notify_attendance_recorded(
                db,
                athlete_user_id=str(ath["user_id"]),
                status=record.status,
                session_date=s_date_str,
                session_id=session_id,
            )
        except Exception as exc:
            logger.warning("Failed to dispatch attendance notification: %s", exc)

    # Dispatch notification to session coach
    if session.get("coach_id"):
        try:
            from app.services.notification_service import notify_coach_attendance
            c_doc = await db.coaches.find_one({"_id": session["coach_id"]})
            if c_doc and c_doc.get("user_id"):
                s_date = session.get("session_date") or session.get("date")
                s_date_str = s_date.strftime("%b %d, %Y") if hasattr(s_date, "strftime") else str(s_date)
                await notify_coach_attendance(
                    db,
                    coach_user_id=str(c_doc["user_id"]),
                    athlete_name=ath_name,
                    status=record.status,
                    session_date_str=s_date_str,
                    session_id=session_id,
                    athlete_id=str(a_oid),
                )
        except Exception as exc:
            logger.warning("Failed to dispatch coach attendance notification: %s", exc)

    return AttendanceResponse(
        id=str(updated_record["_id"]),
        session_id=str(updated_record["session_id"]),
        athlete_id=str(updated_record["athlete_id"]),
        athlete_name=ath_name,
        status=updated_record["status"],
        marked_by=str(updated_record.get("marked_by") or user_id),
        marked_at=updated_record.get("marked_at"),
        remarks=updated_record.get("remarks"),
        created_at=updated_record.get("created_at"),
        updated_at=updated_record.get("updated_at"),
    )


async def record_bulk_attendance_service(
    db: AsyncIOMotorDatabase,
    session_id: str,
    data: AttendanceBulkCreate,
    current_user: dict,
) -> list[AttendanceResponse]:
    responses = []
    for item in data.records:
        resp = await record_attendance_service(db, session_id, item, current_user)
        responses.append(resp)
    return responses


# ── Calculations & Summaries ───────────────────────────────────────────────────

def calculate_attendance_stats(records: list[dict], total_sessions: int) -> tuple[int, int, int, float, bool]:
    """
    Returns: (present_count, late_count, absent_count, percentage, warning)
    Present = attended
    Late = attended
    Absent = not attended
    """
    present = 0
    late = 0
    absent = 0

    for r in records:
        st = r.get("status", "").lower()
        if st == "present":
            present += 1
        elif st == "late":
            late += 1
        elif st == "absent":
            absent += 1

    attended = present + late
    if total_sessions > 0:
        percentage = round((attended / total_sessions) * 100, 1)
    elif (attended + absent) > 0:
        percentage = round((attended / (attended + absent)) * 100, 1)
    else:
        percentage = 0.0

    warning = percentage < ATTENDANCE_WARNING_THRESHOLD if total_sessions > 0 else False
    return present, late, absent, percentage, warning


async def get_athlete_attendance_summary_service(
    db: AsyncIOMotorDatabase, athlete_id: str, current_user: dict
) -> AthleteAttendanceSummary:
    ath = await get_athlete_by_id(db, athlete_id)
    if not ath:
        raise NotFoundError("Athlete not found")

    role = current_user["role"]
    user_id = current_user["user_id"]

    if role == "athlete":
        if str(ath.get("user_id", "")) != user_id:
            raise ForbiddenError("You can only view your own attendance summary")

    elif role == "coach":
        coach = await get_coach_by_user_id(db, user_id)
        if not coach:
            raise ForbiddenError("Coach profile not found")
        assigned_ids = await get_coach_assigned_athlete_ids(db, str(coach["_id"]))
        is_direct = str(ath.get("coach_id", "")) == str(coach["_id"])
        is_assigned = ath["_id"] in assigned_ids
        if not is_direct and not is_assigned:
            raise ForbiddenError("You are not assigned to this athlete")

    # 1. Total applicable sessions (non-cancelled sessions where athlete was participant)
    cursor = db.training_sessions.find({
        "athlete_ids": ath["_id"],
        "status": {"$ne": "cancelled"},
    }).sort([("session_date", -1), ("date", -1)])
    sessions = await cursor.to_list(length=500)
    total_applicable = len(sessions)

    # 2. Attendance records for this athlete
    attendance_records = await get_athlete_attendance_records(db, athlete_id)
    att_by_session = {str(a["session_id"]): a for a in attendance_records}

    # Filter attendance records that belong to non-cancelled sessions
    non_cancelled_ids = {str(s["_id"]) for s in sessions}
    valid_att_records = [a for a in attendance_records if str(a["session_id"]) in non_cancelled_ids]

    present, late, absent, percentage, warning = calculate_attendance_stats(
        valid_att_records, total_applicable
    )

    # Build history list
    history = []
    for s in sessions:
        s_id_str = str(s["_id"])
        att = att_by_session.get(s_id_str)
        sport = await db.sports.find_one({"_id": s["sport_id"]})
        coach_doc = await db.coaches.find_one({"_id": s["coach_id"]})

        history.append({
            "session_id": s_id_str,
            "title": s.get("title", ""),
            "sport_name": sport.get("name") if sport else None,
            "coach_name": coach_doc.get("full_name") if coach_doc else None,
            "date": s.get("session_date") or s.get("date"),
            "start_time": s.get("start_time", "09:00"),
            "end_time": s.get("end_time", "10:00"),
            "location": s.get("location") or s.get("venue"),
            "session_status": s.get("status", "scheduled"),
            "attendance_status": att.get("status") if att else "unrecorded",
            "remarks": att.get("remarks") if att else None,
        })

    return AthleteAttendanceSummary(
        total_sessions=total_applicable,
        attended_sessions=present + late,
        present_count=present,
        late_count=late,
        absent_count=absent,
        attendance_percentage=percentage,
        warning=warning,
        history=history,
    )


async def get_coach_dashboard_summary_service(
    db: AsyncIOMotorDatabase, user_id: str
) -> CoachTrainingSummary:
    coach = await get_coach_by_user_id(db, user_id)
    if not coach:
        return CoachTrainingSummary(
            today_count=0, upcoming_count=0, completed_count=0, average_attendance_percentage=0.0
        )

    c_id = coach["_id"]
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = datetime.now(timezone.utc).replace(hour=23, minute=59, end_sec=59, microsecond=999999) if False else datetime.now(timezone.utc).replace(hour=23, minute=59, second=59, microsecond=999999)

    today_count = await db.training_sessions.count_documents({
        "coach_id": c_id,
        "$or": [{"session_date": {"$gte": today_start, "$lte": today_end}},
                {"date": {"$gte": today_start, "$lte": today_end}}],
        "status": {"$ne": "cancelled"},
    })

    upcoming_count = await db.training_sessions.count_documents({
        "coach_id": c_id,
        "status": "scheduled",
    })

    completed_count = await db.training_sessions.count_documents({
        "coach_id": c_id,
        "status": "completed",
    })

    # Average attendance percentage across completed sessions
    cursor = db.training_sessions.find({"coach_id": c_id, "status": "completed"})
    completed_sessions = await cursor.to_list(length=200)

    total_pct = 0.0
    count_calc = 0
    for cs in completed_sessions:
        ath_ids = cs.get("athlete_ids", [])
        if not ath_ids:
            continue
        att_docs = await get_session_attendance(db, str(cs["_id"]))
        attended = sum(1 for a in att_docs if a.get("status", "").lower() in ("present", "late"))
        pct = (attended / len(ath_ids)) * 100
        total_pct += pct
        count_calc += 1

    avg_pct = round(total_pct / count_calc, 1) if count_calc > 0 else 0.0

    return CoachTrainingSummary(
        today_count=today_count,
        upcoming_count=upcoming_count,
        completed_count=completed_count,
        average_attendance_percentage=avg_pct,
    )


async def get_admin_dashboard_summary_service(db: AsyncIOMotorDatabase) -> AdminTrainingSummary:
    total = await db.training_sessions.count_documents({})
    scheduled = await db.training_sessions.count_documents({"status": "scheduled"})
    completed = await db.training_sessions.count_documents({"status": "completed"})
    cancelled = await db.training_sessions.count_documents({"status": "cancelled"})

    cursor = db.training_sessions.find({"status": "completed"})
    completed_sessions = await cursor.to_list(length=300)

    total_pct = 0.0
    count_calc = 0
    for cs in completed_sessions:
        ath_ids = cs.get("athlete_ids", [])
        if not ath_ids:
            continue
        att_docs = await get_session_attendance(db, str(cs["_id"]))
        attended = sum(1 for a in att_docs if a.get("status", "").lower() in ("present", "late"))
        pct = (attended / len(ath_ids)) * 100
        total_pct += pct
        count_calc += 1

    avg_pct = round(total_pct / count_calc, 1) if count_calc > 0 else 0.0

    return AdminTrainingSummary(
        total_sessions=total,
        scheduled_count=scheduled,
        completed_count=completed,
        cancelled_count=cancelled,
        average_attendance_percentage=avg_pct,
    )
