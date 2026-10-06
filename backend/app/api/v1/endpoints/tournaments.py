import logging
from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import get_current_user
from app.db.database import get_database
from app.schemas.tournament import (
    AthleteTournamentHistoryItem,
    ParticipantAdd,
    ParticipantResponse,
    ResultRecordCreate,
    ResultRecordUpdate,
    TournamentCreate,
    TournamentResponse,
    TournamentUpdate,
)
from app.services.tournament_service import (
    add_participant_service,
    create_tournament_service,
    delete_tournament_service,
    get_athlete_tournament_history_service,
    get_tournament_results_service,
    get_tournament_service,
    list_tournament_participants_service,
    list_tournaments_service,
    record_tournament_result_service,
    remove_participant_service,
    update_tournament_result_service,
    update_tournament_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tournaments", tags=["Tournaments"])


# ── Tournament CRUD ────────────────────────────────────────────────────────────

@router.get("", response_model=list[TournamentResponse])
async def list_tournaments(
    current_user: Annotated[dict, Depends(get_current_user)],
    search: Optional[str] = Query(default=None, description="Search by name, description, venue"),
    sport_id: Optional[str] = Query(default=None, description="Filter by sport ID"),
    status_filter: Optional[str] = Query(default=None, alias="status", description="Filter by status (upcoming, ongoing, completed, cancelled)"),
    start_date: Optional[datetime] = Query(default=None, description="Filter start date >= value"),
    end_date: Optional[datetime] = Query(default=None, description="Filter end date <= value"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
):
    """List tournaments. Accessible to all authenticated users."""
    db = get_database()
    return await list_tournaments_service(
        db,
        search=search,
        sport_id=sport_id,
        status=status_filter,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit,
    )


@router.post("", response_model=TournamentResponse, status_code=status.HTTP_201_CREATED)
async def create_tournament(
    body: TournamentCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Create a new tournament. Admin only."""
    db = get_database()
    return await create_tournament_service(db, body, current_user)


@router.get("/{tournament_id}", response_model=TournamentResponse)
async def get_tournament(
    tournament_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Get tournament details by ID."""
    db = get_database()
    return await get_tournament_service(db, tournament_id)


@router.put("/{tournament_id}", response_model=TournamentResponse)
async def update_tournament(
    tournament_id: str,
    body: TournamentUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Update tournament details. Admin only."""
    db = get_database()
    return await update_tournament_service(db, tournament_id, body, current_user)


@router.delete("/{tournament_id}")
async def delete_tournament(
    tournament_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Delete a tournament. Admin only."""
    db = get_database()
    return await delete_tournament_service(db, tournament_id, current_user)


# ── Participation Management ───────────────────────────────────────────────────

@router.get("/{tournament_id}/participants", response_model=list[ParticipantResponse])
async def list_tournament_participants(
    tournament_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """List all participants registered for a tournament."""
    db = get_database()
    return await list_tournament_participants_service(db, tournament_id)


@router.post("/{tournament_id}/participants", response_model=ParticipantResponse, status_code=status.HTTP_201_CREATED)
async def add_tournament_participant(
    tournament_id: str,
    body: ParticipantAdd,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """
    Register an athlete for a tournament.
    - Admin: can register any active athlete.
    - Coach: can register only their assigned athletes.
    - Athlete: can only register themselves.
    """
    db = get_database()
    return await add_participant_service(
        db,
        tournament_id=tournament_id,
        athlete_id=body.athlete_id,
        event=body.event,
        current_user=current_user,
    )


@router.delete("/{tournament_id}/participants/{athlete_id}")
async def remove_tournament_participant(
    tournament_id: str,
    athlete_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """
    Remove/withdraw an athlete's tournament registration.
    - Admin: can remove any athlete.
    - Coach: can remove only assigned athletes.
    - Athlete: can withdraw only their own registration.
    """
    db = get_database()
    return await remove_participant_service(
        db,
        tournament_id=tournament_id,
        athlete_id=athlete_id,
        current_user=current_user,
    )


# ── Results Management ─────────────────────────────────────────────────────────

@router.get("/{tournament_id}/results", response_model=list[ParticipantResponse])
async def get_tournament_results(
    tournament_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Get all recorded results for a tournament."""
    db = get_database()
    return await get_tournament_results_service(db, tournament_id)


@router.post("/{tournament_id}/results", response_model=ParticipantResponse)
async def record_tournament_result(
    tournament_id: str,
    body: ResultRecordCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """
    Record or update an athlete's result in a tournament.
    - Admin: can record results for any athlete.
    - Coach: can record results for assigned athletes.
    - Athlete: forbidden (cannot modify results).
    """
    db = get_database()
    return await record_tournament_result_service(db, tournament_id, body, current_user)


@router.put("/{tournament_id}/results/{athlete_id}", response_model=ParticipantResponse)
async def update_tournament_result(
    tournament_id: str,
    athlete_id: str,
    body: ResultRecordUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """
    Update an athlete's result in a tournament.
    - Admin: can update results for any athlete.
    - Coach: can update results for assigned athletes.
    - Athlete: forbidden (cannot modify results).
    """
    db = get_database()
    return await update_tournament_result_service(db, tournament_id, athlete_id, body, current_user)


# ── Athlete Tournament History ─────────────────────────────────────────────────

@router.get("/history/{athlete_id}", response_model=list[AthleteTournamentHistoryItem])
async def get_athlete_tournament_history(
    athlete_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """
    Get full tournament history for a specific athlete.
    - Admin: any athlete.
    - Coach: assigned athletes only.
    - Athlete: own history only.
    """
    db = get_database()
    return await get_athlete_tournament_history_service(db, athlete_id, current_user)
