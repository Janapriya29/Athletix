import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query, Response, status

from app.core.dependencies import get_current_user, require_admin
from app.db.database import get_database
from app.schemas.report import (
    AcademyAttendanceReportItem,
    AcademySummaryReport,
    AcademyTournamentReportItem,
    AthleteAttendanceReport,
    AthleteDevelopmentSummaryReport,
    AthletePerformanceReport,
    AthleteTournamentsReport,
)
from app.services.report_service import (
    export_attendance_report_to_csv,
    export_tournaments_report_to_csv,
    get_academy_attendance_report_service,
    get_academy_summary_report_service,
    get_academy_tournaments_report_service,
    get_athlete_attendance_report_service,
    get_athlete_development_summary_service,
    get_athlete_performance_report_service,
    get_athlete_tournaments_report_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["Reports"])


# ── Athlete Reports ────────────────────────────────────────────────────────────

@router.get("/athlete/{athlete_id}/performance", response_model=AthletePerformanceReport)
async def get_athlete_performance_report(
    athlete_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """
    Get athlete performance report.
    - Admin: any athlete
    - Coach: assigned athletes only
    - Athlete: own report only
    """
    db = get_database()
    return await get_athlete_performance_report_service(db, athlete_id, current_user)


@router.get("/athlete/{athlete_id}/attendance", response_model=AthleteAttendanceReport)
async def get_athlete_attendance_report(
    athlete_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """
    Get athlete attendance report.
    - Admin: any athlete
    - Coach: assigned athletes only
    - Athlete: own report only
    """
    db = get_database()
    return await get_athlete_attendance_report_service(db, athlete_id, current_user)


@router.get("/athlete/{athlete_id}/tournaments", response_model=AthleteTournamentsReport)
async def get_athlete_tournaments_report(
    athlete_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """
    Get athlete tournament history & medals report.
    - Admin: any athlete
    - Coach: assigned athletes only
    - Athlete: own report only
    """
    db = get_database()
    return await get_athlete_tournaments_report_service(db, athlete_id, current_user)


@router.get("/athlete/{athlete_id}/development", response_model=AthleteDevelopmentSummaryReport)
async def get_athlete_development_summary(
    athlete_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """
    Get comprehensive athlete development profile summary.
    - Admin: any athlete
    - Coach: assigned athletes only
    - Athlete: own report only
    """
    db = get_database()
    return await get_athlete_development_summary_service(db, athlete_id, current_user)


# ── Academy Wide Reports ───────────────────────────────────────────────────────

@router.get("/academy/summary", response_model=AcademySummaryReport)
async def get_academy_summary_report(
    current_user: Annotated[dict, Depends(require_admin)],
):
    """
    Get comprehensive academy-wide summary report.
    - Admin only.
    """
    db = get_database()
    return await get_academy_summary_report_service(db, current_user)


@router.get("/attendance")
async def get_academy_attendance_report(
    current_user: Annotated[dict, Depends(get_current_user)],
    sport_id: Optional[str] = Query(default=None, description="Filter by sport"),
    format: Optional[str] = Query(default=None, description="Export format, e.g. csv"),
):
    """
    Get academy/team attendance report.
    Supports ?format=csv export.
    - Admin: all athletes
    - Coach: assigned athletes
    """
    db = get_database()
    items = await get_academy_attendance_report_service(db, current_user, sport_id=sport_id)

    if format and format.lower() == "csv":
        csv_data = export_attendance_report_to_csv(items)
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=attendance_report.csv"},
        )

    return items


@router.get("/tournaments")
async def get_academy_tournaments_report(
    current_user: Annotated[dict, Depends(get_current_user)],
    sport_id: Optional[str] = Query(default=None, description="Filter by sport"),
    format: Optional[str] = Query(default=None, description="Export format, e.g. csv"),
):
    """
    Get tournament results and medalists report.
    Supports ?format=csv export.
    - Admin & Coach
    """
    db = get_database()
    items = await get_academy_tournaments_report_service(db, current_user, sport_id=sport_id)

    if format and format.lower() == "csv":
        csv_data = export_tournaments_report_to_csv(items)
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=tournaments_report.csv"},
        )

    return items
