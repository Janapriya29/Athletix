from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import get_current_user, require_admin
from app.db.database import get_database
from app.schemas.coach import (
    CoachAssignAthletes,
    CoachCreate,
    CoachResponse,
    CoachStatusUpdate,
    CoachUpdate,
)
from app.services.coach_service import (
    assign_athletes_to_coach_service,
    create_coach_service,
    get_coach_by_user_id_service,
    get_coach_service,
    list_coaches_service,
    remove_athlete_assignment_service,
    set_coach_status_service,
    update_coach_service,
)

router = APIRouter(prefix="/coaches", tags=["Coaches"])


@router.get("", response_model=list[CoachResponse])
async def list_coaches(
    current_user: Annotated[dict, Depends(get_current_user)],
    search: Optional[str] = Query(default=None, description="Search by name, email, specialization"),
    sport_id: Optional[str] = Query(default=None, description="Filter by sport"),
    status_filter: Optional[str] = Query(default=None, alias="status", description="Filter by status"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
):
    """
    List coaches with search and filters.
    Admin sees all or filtered by status.
    Coaches and Athletes can view active coaches.
    """
    db = get_database()
    effective_status = status_filter
    if current_user["role"] != "admin":
        effective_status = "active"

    return await list_coaches_service(
        db,
        search=search,
        sport_id=sport_id,
        status=effective_status,
        skip=skip,
        limit=limit,
    )


@router.get("/me", response_model=CoachResponse)
async def get_my_coach_profile(
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Return the authenticated coach's profile."""
    db = get_database()
    return await get_coach_by_user_id_service(db, current_user["user_id"])


@router.post("", response_model=CoachResponse, status_code=status.HTTP_201_CREATED)
async def create_coach(
    body: CoachCreate,
    current_user: Annotated[dict, Depends(require_admin)],
):
    """Create a new coach profile and user account. Admin only."""
    db = get_database()
    return await create_coach_service(db, body)


@router.get("/{coach_id}", response_model=CoachResponse)
async def get_coach(
    coach_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Get single coach by ID. Accessible to authenticated users."""
    db = get_database()
    return await get_coach_service(db, coach_id)


@router.put("/{coach_id}", response_model=CoachResponse)
async def update_coach(
    coach_id: str,
    body: CoachUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """
    Update coach profile.
    Admin can update all fields; Coach can update own phone & bio.
    """
    db = get_database()
    return await update_coach_service(db, coach_id, body, current_user)


@router.patch("/{coach_id}/status", response_model=CoachResponse)
async def set_coach_status(
    coach_id: str,
    body: CoachStatusUpdate,
    current_user: Annotated[dict, Depends(require_admin)],
):
    """Activate or deactivate coach. Admin only."""
    db = get_database()
    return await set_coach_status_service(db, coach_id, body.status)


@router.post("/{coach_id}/athletes")
async def assign_athletes(
    coach_id: str,
    body: CoachAssignAthletes,
    current_user: Annotated[dict, Depends(require_admin)],
):
    """Assign multiple athletes to a coach. Admin only."""
    db = get_database()
    return await assign_athletes_to_coach_service(db, coach_id, body.athlete_ids)


@router.delete("/{coach_id}/athletes/{athlete_id}")
async def remove_athlete(
    coach_id: str,
    athlete_id: str,
    current_user: Annotated[dict, Depends(require_admin)],
):
    """Remove an athlete assignment from a coach. Admin only."""
    db = get_database()
    return await remove_athlete_assignment_service(db, coach_id, athlete_id)
