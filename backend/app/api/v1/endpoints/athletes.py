from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import get_current_user, require_admin
from app.db.database import get_database
from app.schemas.athlete import (
    AssignedCoachInfo,
    AthleteAssignCoach,
    AthleteAssignSport,
    AthleteCreate,
    AthleteResponse,
    AthleteStatusUpdate,
    AthleteUpdate,
)
from app.services.athlete_service import (
    assign_coach_service,
    assign_sport_service,
    create_athlete_service,
    get_athlete_by_user_id_service,
    get_athlete_service,
    get_my_coach_service,
    list_athletes_service,
    set_athlete_status_service,
    update_athlete_service,
)

router = APIRouter(prefix="/athletes", tags=["Athletes"])


@router.get("", response_model=list[AthleteResponse])
async def list_athletes(
    current_user: Annotated[dict, Depends(get_current_user)],
    search: Optional[str] = Query(default=None, description="Search by name, email, phone"),
    sport_id: Optional[str] = Query(default=None, description="Filter by sport"),
    coach_id: Optional[str] = Query(default=None, description="Filter by coach"),
    status_filter: Optional[str] = Query(default=None, alias="status", description="Filter by status"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
):
    """
    List athletes.
    Admin sees all athletes with search/filters.
    Coach sees only their assigned athletes.
    Athlete sees only their own profile.
    """
    db = get_database()
    return await list_athletes_service(
        db,
        current_user=current_user,
        search=search,
        sport_id=sport_id,
        coach_id=coach_id,
        status=status_filter,
        skip=skip,
        limit=limit,
    )


from app.schemas.tournament import AthleteTournamentHistoryItem
from app.services.tournament_service import (
    get_athlete_tournament_history_service,
    get_my_tournament_history_service,
)


@router.get("/me", response_model=AthleteResponse)
async def get_my_athlete_profile(
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Return the authenticated athlete's profile."""
    db = get_database()
    return await get_athlete_by_user_id_service(db, current_user["user_id"])


@router.get("/me/coach", response_model=AssignedCoachInfo)
async def get_my_coach(
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Return the authenticated athlete's assigned coach info."""
    db = get_database()
    return await get_my_coach_service(db, current_user["user_id"])


@router.get("/me/tournaments", response_model=list[AthleteTournamentHistoryItem])
async def get_my_tournaments(
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Return the authenticated athlete's tournament history."""
    db = get_database()
    return await get_my_tournament_history_service(db, current_user)


@router.get("/{athlete_id}/tournaments", response_model=list[AthleteTournamentHistoryItem])
async def get_athlete_tournaments(
    athlete_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Return an athlete's tournament history (Admin, Coach of athlete, or Athlete themselves)."""
    db = get_database()
    return await get_athlete_tournament_history_service(db, athlete_id, current_user)


@router.post("", response_model=AthleteResponse, status_code=status.HTTP_201_CREATED)
async def create_athlete(
    body: AthleteCreate,
    current_user: Annotated[dict, Depends(require_admin)],
):
    """Create a new athlete profile and user account. Admin only."""
    db = get_database()
    return await create_athlete_service(db, body)


@router.get("/{athlete_id}", response_model=AthleteResponse)
async def get_athlete(
    athlete_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """
    Get athlete profile by ID.
    Accessible to Admin, assigned Coach, or the Athlete themselves.
    """
    db = get_database()
    return await get_athlete_service(db, athlete_id, current_user)


@router.put("/{athlete_id}", response_model=AthleteResponse)
async def update_athlete(
    athlete_id: str,
    body: AthleteUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """
    Update athlete profile.
    Admin can update all fields.
    Athlete can only update personal contact fields (phone, address, emergency contact).
    """
    db = get_database()
    return await update_athlete_service(db, athlete_id, body, current_user)


@router.patch("/{athlete_id}/status", response_model=AthleteResponse)
async def set_athlete_status(
    athlete_id: str,
    body: AthleteStatusUpdate,
    current_user: Annotated[dict, Depends(require_admin)],
):
    """Activate or deactivate athlete profile. Admin only."""
    db = get_database()
    return await set_athlete_status_service(db, athlete_id, body.status)


@router.patch("/{athlete_id}/coach", response_model=AthleteResponse)
async def assign_coach(
    athlete_id: str,
    body: AthleteAssignCoach,
    current_user: Annotated[dict, Depends(require_admin)],
):
    """Assign or reassign an athlete to a coach. Admin only."""
    db = get_database()
    return await assign_coach_service(db, athlete_id, body.coach_id)


@router.patch("/{athlete_id}/sport", response_model=AthleteResponse)
async def assign_sport(
    athlete_id: str,
    body: AthleteAssignSport,
    current_user: Annotated[dict, Depends(require_admin)],
):
    """Assign or reassign an athlete's sport. Admin only."""
    db = get_database()
    return await assign_sport_service(db, athlete_id, body)
