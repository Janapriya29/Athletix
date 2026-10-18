import logging
from datetime import datetime
from typing import Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.repositories.athlete_repository import (
    get_athlete_by_id,
    get_athlete_by_user_id,
)
from app.repositories.coach_repository import (
    get_coach_assigned_athlete_ids,
    get_coach_by_user_id,
)
from app.repositories.sport_repository import get_sport_by_id
from app.repositories.tournament_repository import (
    add_participant,
    count_participants,
    count_tournaments,
    create_tournament,
    delete_tournament,
    get_athlete_participations,
    get_participant,
    get_participants,
    get_tournament_by_id,
    get_tournament_by_name,
    list_tournaments,
    remove_participant,
    update_result,
    update_tournament,
)
from app.schemas.tournament import (
    AthleteTournamentHistoryItem,
    ParticipantResponse,
    ResultRecordCreate,
    ResultRecordUpdate,
    TournamentCreate,
    TournamentResponse,
    TournamentUpdate,
    calculate_tournament_points,
)

logger = logging.getLogger(__name__)


# ── Helper to resolve Tournament Response ──────────────────────────────────────

async def _resolve_tournament_response(
    db: AsyncIOMotorDatabase,
    doc: dict,
) -> TournamentResponse:
    t_id_str = str(doc["_id"])
    sport_name = None
    if doc.get("sport_id"):
        sp = await get_sport_by_id(db, str(doc["sport_id"]))
        if sp:
            sport_name = sp.get("name")

    p_count = await count_participants(db, t_id_str)

    loc = doc.get("location") or doc.get("venue")
    return TournamentResponse(
        id=t_id_str,
        name=doc.get("name", ""),
        description=doc.get("description"),
        sport_id=str(doc.get("sport_id", "")),
        sport_name=sport_name,
        location=loc,
        venue=loc,
        start_date=doc.get("start_date"),
        end_date=doc.get("end_date"),
        registration_deadline=doc.get("registration_deadline"),
        status=doc.get("status", "upcoming"),
        participant_count=p_count,
        created_by=str(doc["created_by"]) if doc.get("created_by") else None,
        created_at=doc.get("created_at", datetime.utcnow()),
        updated_at=doc.get("updated_at"),
    )


# ── 1. Tournament CRUD ─────────────────────────────────────────────────────────

async def create_tournament_service(
    db: AsyncIOMotorDatabase,
    data: TournamentCreate,
    current_user: dict,
) -> TournamentResponse:
    if current_user.get("role") != "admin":
        raise ForbiddenError("Only admins can create tournaments")

    # Sport validation
    sport = await get_sport_by_id(db, data.sport_id)
    if not sport:
        raise BadRequestError("Sport not found")
    if not sport.get("is_active", True):
        raise BadRequestError("Cannot create tournament for an inactive sport")

    # Duplicate name check
    existing = await get_tournament_by_name(db, data.name)
    if existing:
        raise BadRequestError(f"Tournament '{data.name}' already exists")

    loc = data.location or data.venue or "Main Sports Complex"
    doc = {
        "name": data.name.strip(),
        "description": data.description.strip() if data.description else None,
        "sport_id": sport["_id"],
        "location": loc.strip(),
        "venue": loc.strip(),
        "start_date": data.start_date,
        "end_date": data.end_date,
        "registration_deadline": data.registration_deadline,
        "status": data.status.lower(),
        "created_by": ObjectId(current_user["user_id"]),
    }
    created = await create_tournament(db, doc)
    return await _resolve_tournament_response(db, created)


async def get_tournament_service(
    db: AsyncIOMotorDatabase,
    tournament_id: str,
) -> TournamentResponse:
    tournament = await get_tournament_by_id(db, tournament_id)
    if not tournament:
        raise NotFoundError("Tournament not found")
    return await _resolve_tournament_response(db, tournament)


async def list_tournaments_service(
    db: AsyncIOMotorDatabase,
    search: Optional[str] = None,
    sport_id: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
) -> list[TournamentResponse]:
    tournaments = await list_tournaments(
        db,
        search=search,
        sport_id=sport_id,
        status=status,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit,
    )
    # Pre-cache sports
    sports_cursor = db.sports.find()
    sports = await sports_cursor.to_list(length=100)
    sport_map = {str(s["_id"]): s.get("name") for s in sports}

    results = []
    for t in tournaments:
        t_id_str = str(t["_id"])
        sp_id = str(t.get("sport_id", ""))
        p_count = await count_participants(db, t_id_str)
        loc = t.get("location") or t.get("venue")
        results.append(
            TournamentResponse(
                id=t_id_str,
                name=t.get("name", ""),
                description=t.get("description"),
                sport_id=sp_id,
                sport_name=sport_map.get(sp_id),
                location=loc,
                venue=loc,
                start_date=t.get("start_date"),
                end_date=t.get("end_date"),
                registration_deadline=t.get("registration_deadline"),
                status=t.get("status", "upcoming"),
                participant_count=p_count,
                created_by=str(t["created_by"]) if t.get("created_by") else None,
                created_at=t.get("created_at", datetime.utcnow()),
                updated_at=t.get("updated_at"),
            )
        )
    return results


async def update_tournament_service(
    db: AsyncIOMotorDatabase,
    tournament_id: str,
    data: TournamentUpdate,
    current_user: dict,
) -> TournamentResponse:
    if current_user.get("role") != "admin":
        raise ForbiddenError("Only admins can update tournaments")

    tournament = await get_tournament_by_id(db, tournament_id)
    if not tournament:
        raise NotFoundError("Tournament not found")

    update_doc = {}
    if data.name:
        existing = await get_tournament_by_name(db, data.name)
        if existing and str(existing["_id"]) != tournament_id:
            raise BadRequestError(f"Tournament name '{data.name}' is already in use")
        update_doc["name"] = data.name

    if data.description is not None:
        update_doc["description"] = data.description

    if data.sport_id:
        sport = await get_sport_by_id(db, data.sport_id)
        if not sport:
            raise BadRequestError("Sport not found")
        update_doc["sport_id"] = sport["_id"]

    new_start = data.start_date or tournament.get("start_date")
    new_end = data.end_date or tournament.get("end_date")
    if new_end < new_start:
        raise BadRequestError("End date cannot be before start date")

    if data.start_date:
        update_doc["start_date"] = data.start_date
    if data.end_date:
        update_doc["end_date"] = data.end_date
    if data.registration_deadline:
        if data.registration_deadline > new_start:
            raise BadRequestError("Registration deadline cannot be after start date")
        update_doc["registration_deadline"] = data.registration_deadline

    if data.status:
        update_doc["status"] = data.status

    if data.location or data.venue:
        loc = data.location or data.venue
        update_doc["location"] = loc
        update_doc["venue"] = loc

    updated = await update_tournament(db, tournament_id, update_doc)
    return await _resolve_tournament_response(db, updated)


async def delete_tournament_service(
    db: AsyncIOMotorDatabase,
    tournament_id: str,
    current_user: dict,
) -> dict:
    if current_user.get("role") != "admin":
        raise ForbiddenError("Only admins can delete tournaments")

    tournament = await get_tournament_by_id(db, tournament_id)
    if not tournament:
        raise NotFoundError("Tournament not found")

    success = await delete_tournament(db, tournament_id)
    if not success:
        raise BadRequestError("Failed to delete tournament")
    return {"message": "Tournament deleted successfully", "id": tournament_id}


# ── 2. Participation Management ────────────────────────────────────────────────

async def add_participant_service(
    db: AsyncIOMotorDatabase,
    tournament_id: str,
    athlete_id: str,
    event: Optional[str],
    current_user: dict,
) -> ParticipantResponse:
    tournament = await get_tournament_by_id(db, tournament_id)
    if not tournament:
        raise NotFoundError("Tournament not found")

    if tournament.get("status") == "cancelled":
        raise BadRequestError("Cannot register for a cancelled tournament")

    athlete = await get_athlete_by_id(db, athlete_id)
    if not athlete:
        raise NotFoundError("Athlete not found")

    if athlete.get("status") != "active":
        raise BadRequestError("Athlete is inactive")

    role = current_user.get("role")
    user_id = current_user.get("user_id")

    # Authorization check
    if role == "athlete":
        if str(athlete.get("user_id", "")) != user_id:
            raise ForbiddenError("Athletes cannot register other athletes")

    elif role == "coach":
        coach = await get_coach_by_user_id(db, user_id)
        if not coach:
            raise ForbiddenError("Coach profile not found")
        assigned_ids = await get_coach_assigned_athlete_ids(db, str(coach["_id"]))
        assigned_strs = {str(x) for x in assigned_ids}
        is_direct = str(athlete.get("coach_id", "")) == str(coach["_id"])
        is_assigned = str(athlete["_id"]) in assigned_strs
        if not is_direct and not is_assigned:
            raise ForbiddenError("You can only register athletes assigned to you")

    elif role != "admin":
        raise ForbiddenError("Insufficient permissions")

    # Sport compatibility check
    t_sport_str = str(tournament.get("sport_id", ""))
    ath_sports_str = {
        str(sid)
        for sid in ([athlete.get("sport_id")] + (athlete.get("additional_sport_ids") or []))
        if sid is not None and str(sid) not in ("", "None")
    }
    if not t_sport_str or t_sport_str not in ath_sports_str:
        raise BadRequestError("Athlete sport does not match tournament sport")

    # Duplicate check
    existing = await get_participant(db, tournament_id, athlete_id)
    if existing:
        raise BadRequestError("Athlete is already registered for this tournament")

    added = await add_participant(
        db,
        tournament_id=tournament_id,
        athlete_id=athlete_id,
        event=event,
        registered_by=user_id,
    )

    if athlete.get("user_id"):
        try:
            from app.services.notification_service import notify_tournament_registration
            await notify_tournament_registration(
                db,
                athlete_user_id=str(athlete["user_id"]),
                tournament_name=tournament.get("name", "Tournament"),
                tournament_id=tournament_id,
            )
        except Exception as exc:
            logger.warning("Failed to dispatch tournament registration notification: %s", exc)

    # Notify assigned coaches
    try:
        from app.services.notification_service import (
            get_coach_user_ids_for_athlete,
            notify_coach_tournament_registration,
        )
        coach_uids = await get_coach_user_ids_for_athlete(db, athlete)
        for c_uid in coach_uids:
            await notify_coach_tournament_registration(
                db,
                coach_user_id=c_uid,
                athlete_name=athlete.get("full_name", "Athlete"),
                tournament_name=tournament.get("name", "Tournament"),
                tournament_id=tournament_id,
                athlete_id=athlete_id,
            )
    except Exception as exc:
        logger.warning("Failed to dispatch coach tournament registration notification: %s", exc)

    sport = await get_sport_by_id(db, t_sport_str)
    return ParticipantResponse(
        id=str(added["_id"]),
        tournament_id=tournament_id,
        athlete_id=athlete_id,
        athlete_name=athlete.get("full_name", ""),
        sport_name=sport.get("name") if sport else None,
        event=added.get("event"),
        status=added.get("status", "registered"),
        position=added.get("position"),
        rank=added.get("position"),
        score=added.get("score"),
        points=added.get("points"),
        medal=added.get("medal"),
        remarks=added.get("remarks"),
        registered_at=added.get("registered_at", datetime.utcnow()),
    )


async def remove_participant_service(
    db: AsyncIOMotorDatabase,
    tournament_id: str,
    athlete_id: str,
    current_user: dict,
) -> dict:
    tournament = await get_tournament_by_id(db, tournament_id)
    if not tournament:
        raise NotFoundError("Tournament not found")

    participant = await get_participant(db, tournament_id, athlete_id)
    if not participant:
        raise NotFoundError("Participant registration not found")

    athlete = await get_athlete_by_id(db, athlete_id)
    role = current_user.get("role")
    user_id = current_user.get("user_id")

    if role == "athlete":
        if not athlete or str(athlete.get("user_id", "")) != user_id:
            raise ForbiddenError("Athletes can only withdraw their own registration")

    elif role == "coach":
        coach = await get_coach_by_user_id(db, user_id)
        if not coach:
            raise ForbiddenError("Coach profile not found")
        assigned_ids = await get_coach_assigned_athlete_ids(db, str(coach["_id"]))
        is_direct = athlete and str(athlete.get("coach_id", "")) == str(coach["_id"])
        is_assigned = athlete and athlete["_id"] in assigned_ids
        if not is_direct and not is_assigned:
            raise ForbiddenError("You can only remove athletes assigned to you")

    elif role != "admin":
        raise ForbiddenError("Insufficient permissions")

    success = await remove_participant(db, tournament_id, athlete_id)
    if not success:
        raise BadRequestError("Failed to remove participant")
    return {"message": "Participant removed successfully", "athlete_id": athlete_id}


async def list_tournament_participants_service(
    db: AsyncIOMotorDatabase,
    tournament_id: str,
) -> list[ParticipantResponse]:
    tournament = await get_tournament_by_id(db, tournament_id)
    if not tournament:
        raise NotFoundError("Tournament not found")

    participants = await get_participants(db, tournament_id)

    # Pre-cache athletes
    athletes_cursor = db.athletes.find()
    athletes = await athletes_cursor.to_list(length=1000)
    athlete_map = {str(a["_id"]): a for a in athletes}

    sport = await get_sport_by_id(db, str(tournament["sport_id"]))
    sport_name = sport.get("name") if sport else None

    results = []
    for p in participants:
        a_id = str(p["athlete_id"])
        ath = athlete_map.get(a_id, {})
        pos = p.get("position")
        results.append(
            ParticipantResponse(
                id=str(p["_id"]),
                tournament_id=tournament_id,
                athlete_id=a_id,
                athlete_name=ath.get("full_name", "Unknown Athlete"),
                sport_name=sport_name,
                event=p.get("event"),
                status=p.get("status", "registered"),
                position=pos,
                rank=pos,
                score=p.get("score"),
                points=p.get("points"),
                medal=p.get("medal"),
                remarks=p.get("remarks"),
                registered_at=p.get("registered_at", datetime.utcnow()),
            )
        )
    return results


# ── 3. Results Management ──────────────────────────────────────────────────────

async def record_tournament_result_service(
    db: AsyncIOMotorDatabase,
    tournament_id: str,
    data: ResultRecordCreate,
    current_user: dict,
) -> ParticipantResponse:
    role = current_user.get("role")
    user_id = current_user.get("user_id")

    if role == "athlete":
        raise ForbiddenError("Athletes cannot record or modify tournament results")

    tournament = await get_tournament_by_id(db, tournament_id)
    if not tournament:
        raise NotFoundError("Tournament not found")

    participant = await get_participant(db, tournament_id, data.athlete_id)
    if not participant:
        raise NotFoundError("Athlete is not registered for this tournament")

    athlete = await get_athlete_by_id(db, data.athlete_id)

    # Coach permission
    if role == "coach":
        coach = await get_coach_by_user_id(db, user_id)
        if not coach:
            raise ForbiddenError("Coach profile not found")
        assigned_ids = await get_coach_assigned_athlete_ids(db, str(coach["_id"]))
        is_direct = athlete and str(athlete.get("coach_id", "")) == str(coach["_id"])
        is_assigned = athlete and athlete["_id"] in assigned_ids
        if not is_direct and not is_assigned:
            raise ForbiddenError("Coaches can only record results for assigned athletes")

    final_medal = data.medal
    if not final_medal and data.position:
        if data.position == 1:
            final_medal = "Gold"
        elif data.position == 2:
            final_medal = "Silver"
        elif data.position == 3:
            final_medal = "Bronze"

    final_points = calculate_tournament_points(
        position=data.position,
        medal=final_medal,
        explicit_points=data.points,
    )

    result_fields = {
        "position": data.position,
        "score": data.score,
        "points": final_points,
        "medal": final_medal,
        "remarks": data.remarks,
    }

    updated = await update_result(
        db,
        tournament_id=tournament_id,
        athlete_id=data.athlete_id,
        result_fields=result_fields,
        recorded_by=user_id,
    )

    if athlete and athlete.get("user_id"):
        try:
            from app.services.notification_service import notify_tournament_result
            await notify_tournament_result(
                db,
                athlete_user_id=str(athlete["user_id"]),
                tournament_name=tournament.get("name", "Tournament"),
                tournament_id=tournament_id,
                position=data.position,
                medal=final_medal,
                points=final_points,
            )
        except Exception as exc:
            logger.warning("Failed to dispatch tournament result notification: %s", exc)

    # Notify assigned coaches
    if athlete:
        try:
            from app.services.notification_service import (
                get_coach_user_ids_for_athlete,
                notify_coach_tournament_result,
            )
            coach_uids = await get_coach_user_ids_for_athlete(db, athlete)
            for c_uid in coach_uids:
                await notify_coach_tournament_result(
                    db,
                    coach_user_id=c_uid,
                    athlete_name=athlete.get("full_name", "Athlete"),
                    tournament_name=tournament.get("name", "Tournament"),
                    tournament_id=tournament_id,
                    athlete_id=data.athlete_id,
                    position=data.position,
                    medal=final_medal,
                    points=final_points,
                )
        except Exception as exc:
            logger.warning("Failed to dispatch coach tournament result notification: %s", exc)

    sport = await get_sport_by_id(db, str(tournament["sport_id"]))
    return ParticipantResponse(
        id=str(updated["_id"]),
        tournament_id=tournament_id,
        athlete_id=data.athlete_id,
        athlete_name=athlete.get("full_name") if athlete else "Athlete",
        sport_name=sport.get("name") if sport else None,
        event=updated.get("event"),
        status=updated.get("status", "participated"),
        position=updated.get("position"),
        rank=updated.get("position"),
        score=updated.get("score"),
        points=updated.get("points"),
        medal=updated.get("medal"),
        remarks=updated.get("remarks"),
        registered_at=updated.get("registered_at", datetime.utcnow()),
    )


async def get_tournament_results_service(
    db: AsyncIOMotorDatabase,
    tournament_id: str,
) -> list[ParticipantResponse]:
    participants = await list_tournament_participants_service(db, tournament_id)
    return [
        p for p in participants
        if p.status == "participated" or p.position is not None or p.score is not None or p.points is not None or p.medal is not None
    ]


async def update_tournament_result_service(
    db: AsyncIOMotorDatabase,
    tournament_id: str,
    athlete_id: str,
    data: ResultRecordUpdate,
    current_user: dict,
) -> ParticipantResponse:
    create_data = ResultRecordCreate(
        athlete_id=athlete_id,
        position=data.position,
        rank=data.rank,
        score=data.score,
        points=data.points,
        medal=data.medal,
        remarks=data.remarks,
    )
    return await record_tournament_result_service(db, tournament_id, create_data, current_user)


# ── 4. Athlete Tournament History ──────────────────────────────────────────────

async def get_athlete_tournament_history_service(
    db: AsyncIOMotorDatabase,
    athlete_id: str,
    current_user: dict,
) -> list[AthleteTournamentHistoryItem]:
    athlete = await get_athlete_by_id(db, athlete_id)
    if not athlete:
        raise NotFoundError("Athlete not found")

    role = current_user.get("role")
    user_id = current_user.get("user_id")

    if role == "athlete":
        if str(athlete.get("user_id", "")) != user_id:
            raise ForbiddenError("You can only view your own tournament history")

    elif role == "coach":
        coach = await get_coach_by_user_id(db, user_id)
        if not coach:
            raise ForbiddenError("Coach profile not found")
        assigned_ids = await get_coach_assigned_athlete_ids(db, str(coach["_id"]))
        is_direct = str(athlete.get("coach_id", "")) == str(coach["_id"])
        is_assigned = athlete["_id"] in assigned_ids
        if not is_direct and not is_assigned:
            raise ForbiddenError("You can only view tournament history for assigned athletes")

    elif role != "admin":
        raise ForbiddenError("Insufficient permissions")

    participations = await get_athlete_participations(db, athlete_id)

    # Pre-cache sports & tournaments
    sports_cursor = db.sports.find()
    all_sports = await sports_cursor.to_list(length=100)
    sport_map = {str(s["_id"]): s.get("name") for s in all_sports}

    results = []
    for p in participations:
        t_id_str = str(p["tournament_id"])
        tourney = await get_tournament_by_id(db, t_id_str)
        if not tourney:
            continue

        sp_id = str(tourney.get("sport_id", ""))
        loc = tourney.get("location") or tourney.get("venue")

        results.append(
            AthleteTournamentHistoryItem(
                tournament_id=t_id_str,
                tournament_name=tourney.get("name", ""),
                sport_name=sport_map.get(sp_id),
                location=loc,
                start_date=tourney.get("start_date"),
                end_date=tourney.get("end_date"),
                tournament_status=tourney.get("status", "upcoming"),
                participation_status=p.get("status", "registered"),
                event=p.get("event"),
                position=p.get("position"),
                medal=p.get("medal"),
                score=p.get("score"),
                points=p.get("points"),
                remarks=p.get("remarks"),
            )
        )

    # Sort chronologically by start date descending
    results.sort(key=lambda item: item.start_date, reverse=True)
    return results


async def get_my_tournament_history_service(
    db: AsyncIOMotorDatabase,
    current_user: dict,
) -> list[AthleteTournamentHistoryItem]:
    if current_user.get("role") != "athlete":
        raise ForbiddenError("Only athletes can access personal tournament history")

    athlete = await get_athlete_by_user_id(db, current_user["user_id"])
    if not athlete:
        raise NotFoundError("Athlete profile not found")

    return await get_athlete_tournament_history_service(db, str(athlete["_id"]), current_user)
