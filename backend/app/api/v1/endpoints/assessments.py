import logging
from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import get_current_user
from app.db.database import get_database
from app.schemas.assessment import AssessmentCreate, AssessmentResponse
from app.services.assessment_service import (
    create_assessment_service,
    get_assessment_service,
    get_athlete_assessments_service,
    list_assessments_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/assessments", tags=["Assessments"])


@router.post("", response_model=AssessmentResponse, status_code=status.HTTP_201_CREATED)
async def create_assessment(
    body: AssessmentCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """
    Record a new performance assessment.
    Accessible to coaches (for assigned athletes) and admins. Athletes receive 403.
    Automatically computes overall_score if not provided, and notifies athlete.
    """
    db = get_database()
    return await create_assessment_service(db, body, current_user)


@router.get("", response_model=list[AssessmentResponse])
async def list_assessments(
    current_user: Annotated[dict, Depends(get_current_user)],
    athlete_id: Optional[str] = Query(default=None, description="Filter by athlete ID"),
    coach_id: Optional[str] = Query(default=None, description="Filter by coach ID"),
    sport_id: Optional[str] = Query(default=None, description="Filter by sport ID"),
    start_date: Optional[datetime] = Query(default=None, description="Filter date >= value"),
    end_date: Optional[datetime] = Query(default=None, description="Filter date <= value"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
):
    """
    List performance assessments with optional filters.
    RBAC enforced:
    - Admin: can view all
    - Coach: can view assessments for assigned athletes
    - Athlete: can view only own assessments
    """
    db = get_database()
    return await list_assessments_service(
        db,
        current_user=current_user,
        athlete_id=athlete_id,
        coach_id=coach_id,
        sport_id=sport_id,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit,
    )


@router.get("/{assessment_id}", response_model=AssessmentResponse)
async def get_assessment(
    assessment_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """
    Get a single performance assessment by ID.
    RBAC enforced.
    """
    db = get_database()
    return await get_assessment_service(db, assessment_id, current_user)


@router.get("/athlete/{athlete_id}", response_model=list[AssessmentResponse])
async def get_athlete_assessments(
    athlete_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """
    Get all performance assessments for a specific athlete, latest first.
    RBAC enforced.
    """
    db = get_database()
    return await get_athlete_assessments_service(db, athlete_id, current_user)
