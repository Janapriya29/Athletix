from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import get_current_user, require_admin, require_coach
from app.core.exceptions import ForbiddenError, NotFoundError
from app.db.database import get_database
from app.repositories.athlete_repository import get_athlete_by_user_id
from app.schemas.training import (
    AdminTrainingSummary,
    AthleteAttendanceSummary,
    AttendanceBulkCreate,
    AttendanceRecordCreate,
    AttendanceRecordUpdate,
    AttendanceResponse,
    CoachTrainingSummary,
    ParticipantAdd,
    TrainingSessionCreate,
    TrainingSessionResponse,
    TrainingSessionUpdate,
    TrainingStatusUpdate,
)
from app.services.training_service import (
    add_participant_service,
    create_session_service,
    get_admin_dashboard_summary_service,
    get_athlete_attendance_summary_service,
    get_coach_dashboard_summary_service,
    get_session_attendance_service,
    get_session_service,
    list_sessions_service,
    record_attendance_service,
    record_bulk_attendance_service,
    remove_participant_service,
    set_session_status_service,
    update_session_service,
)

router = APIRouter(prefix="/training", tags=["Training & Attendance"])


# ── Training Sessions ──────────────────────────────────────────────────────────

@router.get("/sessions", response_model=list[TrainingSessionResponse])
async def list_sessions(
    current_user: Annotated[dict, Depends(get_current_user)],
    search: Optional[str] = Query(default=None, description="Search by title, description, location"),
    sport_id: Optional[str] = Query(default=None, description="Filter by sport"),
    coach_id: Optional[str] = Query(default=None, description="Filter by coach"),
    athlete_id: Optional[str] = Query(default=None, description="Filter by athlete"),
    status_filter: Optional[str] = Query(default=None, alias="status", description="Filter by status"),
    start_date: Optional[datetime] = Query(default=None, description="Filter from start date"),
    end_date: Optional[datetime] = Query(default=None, description="Filter to end date"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
):
    """
    List training sessions.
    - Admin sees all or filtered sessions.
    - Coach sees own scheduled/completed sessions.
    - Athlete sees sessions where they are a participant.
    """
    db = get_database()
    return await list_sessions_service(
        db,
        current_user=current_user,
        search=search,
        sport_id=sport_id,
        coach_id=coach_id,
        athlete_id=athlete_id,
        status=status_filter,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit,
    )


@router.post("/sessions", response_model=TrainingSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    body: TrainingSessionCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """
    Create a new training session.
    Admin can create for any active sport/coach.
    Coach can create for own assigned sports.
    Athlete is forbidden.
    """
    db = get_database()
    return await create_session_service(db, body, current_user)


@router.get("/sessions/{session_id}", response_model=TrainingSessionResponse)
async def get_session(
    session_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Get single session by ID. Role-restricted."""
    db = get_database()
    return await get_session_service(db, session_id, current_user)


@router.put("/sessions/{session_id}", response_model=TrainingSessionResponse)
async def update_session(
    session_id: str,
    body: TrainingSessionUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Update training session. Admin or owning coach."""
    db = get_database()
    return await update_session_service(db, session_id, body, current_user)


@router.patch("/sessions/{session_id}/status", response_model=TrainingSessionResponse)
async def set_session_status(
    session_id: str,
    body: TrainingStatusUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Update session status: scheduled, completed, cancelled."""
    db = get_database()
    return await set_session_status_service(db, session_id, body.status, current_user)


# ── Participants ───────────────────────────────────────────────────────────────

@router.post("/sessions/{session_id}/participants", response_model=TrainingSessionResponse)
async def add_participant(
    session_id: str,
    body: ParticipantAdd,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Add an eligible athlete to a training session."""
    db = get_database()
    return await add_participant_service(db, session_id, body.athlete_id, current_user)


@router.delete("/sessions/{session_id}/participants/{athlete_id}", response_model=TrainingSessionResponse)
async def remove_participant(
    session_id: str,
    athlete_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Remove an athlete from a training session and clear session attendance."""
    db = get_database()
    return await remove_participant_service(db, session_id, athlete_id, current_user)


# ── Attendance ─────────────────────────────────────────────────────────────────

@router.get("/sessions/{session_id}/attendance", response_model=list[AttendanceResponse])
async def get_session_attendance(
    session_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Get attendance records for a session. Admin or session Coach only."""
    db = get_database()
    return await get_session_attendance_service(db, session_id, current_user)


@router.post("/sessions/{session_id}/attendance", response_model=AttendanceResponse)
async def record_attendance(
    session_id: str,
    body: AttendanceRecordCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Record or update attendance for an athlete in a session."""
    db = get_database()
    return await record_attendance_service(db, session_id, body, current_user)


@router.post("/sessions/{session_id}/attendance/bulk", response_model=list[AttendanceResponse])
async def record_bulk_attendance(
    session_id: str,
    body: AttendanceBulkCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Record or update multiple attendance records at once."""
    db = get_database()
    return await record_bulk_attendance_service(db, session_id, body, current_user)


@router.put("/sessions/{session_id}/attendance/{athlete_id}", response_model=AttendanceResponse)
async def update_attendance_for_athlete(
    session_id: str,
    athlete_id: str,
    body: AttendanceRecordUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Update single attendance record."""
    db = get_database()
    record = AttendanceRecordCreate(athlete_id=athlete_id, status=body.status, remarks=body.remarks)
    return await record_attendance_service(db, session_id, record, current_user)


# ── Athlete Views & Summaries ──────────────────────────────────────────────────

@router.get("/me", response_model=list[TrainingSessionResponse])
async def get_my_training_sessions(
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Return authenticated athlete's training schedule."""
    if current_user["role"] != "athlete":
        raise ForbiddenError("Only athletes can access /training/me")
    db = get_database()
    ath = await get_athlete_by_user_id(db, current_user["user_id"])
    if not ath:
        return []
    return await list_sessions_service(db, current_user=current_user, athlete_id=str(ath["_id"]))


@router.get("/me/attendance", response_model=AthleteAttendanceSummary)
async def get_my_attendance_summary(
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Return authenticated athlete's attendance statistics and history."""
    if current_user["role"] != "athlete":
        raise ForbiddenError("Only athletes can access /training/me/attendance")
    db = get_database()
    ath = await get_athlete_by_user_id(db, current_user["user_id"])
    if not ath:
        raise NotFoundError("Athlete profile not found")
    return await get_athlete_attendance_summary_service(db, str(ath["_id"]), current_user)


@router.get("/athlete/{athlete_id}/attendance", response_model=AthleteAttendanceSummary)
async def get_athlete_attendance_summary(
    athlete_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Get attendance statistics and history for an athlete. Admin or assigned Coach."""
    db = get_database()
    return await get_athlete_attendance_summary_service(db, athlete_id, current_user)


# ── Dashboard Summaries ────────────────────────────────────────────────────────

@router.get("/coach/summary", response_model=CoachTrainingSummary)
async def get_coach_summary(
    current_user: Annotated[dict, Depends(require_coach)],
):
    """Return training metrics for coach dashboard."""
    db = get_database()
    return await get_coach_dashboard_summary_service(db, current_user["user_id"])


@router.get("/admin/summary", response_model=AdminTrainingSummary)
async def get_admin_summary(
    current_user: Annotated[dict, Depends(require_admin)],
):
    """Return academy-wide training metrics for admin dashboard."""
    db = get_database()
    return await get_admin_dashboard_summary_service(db)
