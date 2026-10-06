import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_current_user
from app.db.database import get_database
from app.schemas.ranking import (
    AttendanceRankingItem,
    ImprovementRankingItem,
    PerformanceRankingItem,
    RankingsResponse,
    TournamentRankingItem,
)
from app.services.ranking_service import (
    get_attendance_rankings_service,
    get_improvement_rankings_service,
    get_performance_rankings_service,
    get_rankings_service,
    get_tournament_rankings_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rankings", tags=["Rankings"])


@router.get("", response_model=RankingsResponse)
async def get_rankings(
    current_user: Annotated[dict, Depends(get_current_user)],
    type: str = Query(default="tournament", description="Ranking type: tournament, performance, attendance, improvement"),
    sport_id: Optional[str] = Query(default=None, description="Optional sport ID filter"),
):
    """
    Get unified academy rankings by type.
    Supported types: tournament, performance, attendance, improvement.
    Accessible to all authenticated users.
    """
    db = get_database()
    return await get_rankings_service(db, ranking_type=type, sport_id=sport_id)


@router.get("/tournament", response_model=list[TournamentRankingItem])
async def get_tournament_rankings(
    current_user: Annotated[dict, Depends(get_current_user)],
    sport_id: Optional[str] = Query(default=None, description="Optional sport ID filter"),
):
    """Get tournament points and medal rankings."""
    db = get_database()
    return await get_tournament_rankings_service(db, sport_id=sport_id)


@router.get("/performance", response_model=list[PerformanceRankingItem])
async def get_performance_rankings(
    current_user: Annotated[dict, Depends(get_current_user)],
    sport_id: Optional[str] = Query(default=None, description="Optional sport ID filter"),
):
    """Get performance assessment score rankings."""
    db = get_database()
    return await get_performance_rankings_service(db, sport_id=sport_id)


@router.get("/attendance", response_model=list[AttendanceRankingItem])
async def get_attendance_rankings(
    current_user: Annotated[dict, Depends(get_current_user)],
    sport_id: Optional[str] = Query(default=None, description="Optional sport ID filter"),
):
    """Get training attendance percentage rankings."""
    db = get_database()
    return await get_attendance_rankings_service(db, sport_id=sport_id)


@router.get("/improvement", response_model=list[ImprovementRankingItem])
async def get_improvement_rankings(
    current_user: Annotated[dict, Depends(get_current_user)],
    sport_id: Optional[str] = Query(default=None, description="Optional sport ID filter"),
):
    """Get performance improvement percentage rankings."""
    db = get_database()
    return await get_improvement_rankings_service(db, sport_id=sport_id)
