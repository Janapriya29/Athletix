from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_current_user, require_admin, require_coach
from app.db.database import get_database
from app.schemas.analytics import (
    AdminAnalyticsSummary,
    AdminSportsAnalyticsResponse,
    AthleteAnalyticsResponse,
    AthleteAnalyticsSummary,
    CoachAnalyticsSummary,
)
from app.services.analytics_service import (
    get_admin_sports_analytics_service,
    get_admin_summary_analytics_service,
    get_athlete_analytics_service,
    get_coach_athletes_analytics_service,
    get_coach_summary_analytics_service,
    get_my_athlete_analytics_service,
)

router = APIRouter(prefix="/analytics", tags=["Performance Analytics"])


# ── Athlete Analytics Endpoints ───────────────────────────────────────────────

@router.get("/athlete/me", response_model=AthleteAnalyticsResponse)
async def get_my_analytics(
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Get authenticated athlete's own performance and attendance analytics."""
    db = get_database()
    return await get_my_athlete_analytics_service(db, current_user)


@router.get("/athlete/{athlete_id}", response_model=AthleteAnalyticsResponse)
async def get_athlete_analytics(
    athlete_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """
    Get detailed performance analytics for an athlete.
    - Admin: can view any athlete.
    - Coach: can view assigned athletes only.
    - Athlete: can view own analytics only.
    """
    db = get_database()
    return await get_athlete_analytics_service(db, athlete_id, current_user)


# ── Coach Analytics Endpoints ─────────────────────────────────────────────────

@router.get("/coach/summary", response_model=CoachAnalyticsSummary)
async def get_coach_summary(
    current_user: Annotated[dict, Depends(require_coach)],
):
    """Get aggregate performance and attendance analytics for coach's assigned athletes."""
    db = get_database()
    return await get_coach_summary_analytics_service(db, current_user["user_id"])


@router.get("/coach/athletes", response_model=list[AthleteAnalyticsSummary])
async def list_coach_athletes_analytics(
    current_user: Annotated[dict, Depends(require_coach)],
    sport_id: Optional[str] = Query(default=None, description="Filter athletes by sport"),
):
    """Get list of assigned athletes with their performance & attendance summary metrics."""
    db = get_database()
    return await get_coach_athletes_analytics_service(db, current_user["user_id"], sport_id=sport_id)


@router.get("/coach/athletes/{athlete_id}", response_model=AthleteAnalyticsResponse)
async def get_coach_athlete_analytics_detail(
    athlete_id: str,
    current_user: Annotated[dict, Depends(require_coach)],
):
    """Get detailed performance analytics for an assigned athlete."""
    db = get_database()
    return await get_athlete_analytics_service(db, athlete_id, current_user)


# ── Admin Analytics Endpoints ─────────────────────────────────────────────────

@router.get("/admin/summary", response_model=AdminAnalyticsSummary)
async def get_admin_summary(
    current_user: Annotated[dict, Depends(require_admin)],
):
    """Get academy-wide performance and attendance analytics summary."""
    db = get_database()
    return await get_admin_summary_analytics_service(db)


@router.get("/admin/sports", response_model=AdminSportsAnalyticsResponse)
async def get_admin_sports_analytics(
    current_user: Annotated[dict, Depends(require_admin)],
):
    """Get sport-wise breakdown of performance and attendance analytics."""
    db = get_database()
    return await get_admin_sports_analytics_service(db)


@router.get("/admin/athletes/{athlete_id}", response_model=AthleteAnalyticsResponse)
async def get_admin_athlete_analytics_detail(
    athlete_id: str,
    current_user: Annotated[dict, Depends(require_admin)],
):
    """Admin view of detailed performance analytics for any athlete."""
    db = get_database()
    return await get_athlete_analytics_service(db, athlete_id, current_user)
