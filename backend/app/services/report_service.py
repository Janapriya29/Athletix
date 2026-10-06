import csv
from datetime import datetime, timezone
import io
import logging
from typing import Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.analytics.performance import (
    calculate_attendance_analytics,
    calculate_improvement,
    calculate_trend,
    identify_strongest_metric,
    identify_weakest_metric,
)
from app.core.exceptions import ForbiddenError, NotFoundError
from app.repositories.analytics_repository import (
    get_athlete_applicable_sessions,
    get_athlete_assessments,
    get_athlete_attendance_records,
)
from app.repositories.athlete_repository import (
    get_athlete_by_id,
    get_athlete_by_user_id,
)
from app.repositories.coach_repository import (
    get_coach_assigned_athlete_ids,
    get_coach_by_user_id,
)
from app.repositories.sport_repository import get_sport_by_id
from app.schemas.report import (
    AcademyAttendanceReportItem,
    AcademySummaryReport,
    AcademyTournamentReportItem,
    AthleteAttendanceReport,
    AthleteDevelopmentSummaryReport,
    AthletePerformanceReport,
    AthleteTournamentReportItem,
    AthleteTournamentsReport,
)

logger = logging.getLogger(__name__)


# ── RBAC Validation ────────────────────────────────────────────────────────────

async def _verify_athlete_report_access(
    db: AsyncIOMotorDatabase,
    athlete_doc: dict,
    current_user: dict,
) -> None:
    role = current_user.get("role")
    user_id = current_user.get("user_id")

    if role == "admin":
        return

    if role == "athlete":
        if str(athlete_doc.get("user_id", "")) != str(user_id):
            raise ForbiddenError("You cannot access another athlete's reports")
        return

    if role == "coach":
        coach = await get_coach_by_user_id(db, user_id)
        if not coach:
            raise ForbiddenError("Coach profile not found")

        assigned_ids = await get_coach_assigned_athlete_ids(db, str(coach["_id"]))
        is_direct = str(athlete_doc.get("coach_id", "")) == str(coach["_id"])
        is_assigned = athlete_doc["_id"] in assigned_ids
        if not is_direct and not is_assigned:
            raise ForbiddenError("You cannot access reports for an athlete not assigned to you")
        return

    raise ForbiddenError("Insufficient permissions")


# ── Athlete Reports ────────────────────────────────────────────────────────────

async def get_athlete_performance_report_service(
    db: AsyncIOMotorDatabase,
    athlete_id: str,
    current_user: dict,
) -> AthletePerformanceReport:
    athlete = await get_athlete_by_id(db, athlete_id)
    if not athlete:
        raise NotFoundError("Athlete not found")

    await _verify_athlete_report_access(db, athlete, current_user)

    # 1. Fetch assessments sorted date desc
    assessments = await get_athlete_assessments(db, athlete_id, sort_ascending=False)
    now = datetime.now(timezone.utc)

    sport_name = None
    if athlete.get("sport_id"):
        sp = await get_sport_by_id(db, str(athlete["sport_id"]))
        if sp:
            sport_name = sp.get("name")

    if not assessments:
        return AthletePerformanceReport(
            athlete_id=athlete_id,
            athlete_name=athlete.get("full_name", ""),
            sport_id=str(athlete["sport_id"]) if athlete.get("sport_id") else None,
            sport_name=sport_name,
            current_score=None,
            previous_score=None,
            improvement_pct=None,
            trend="Insufficient Data",
            strongest_metric=None,
            weakest_metric=None,
            total_assessments=0,
            assessment_history=[],
            generated_at=now,
        )

    latest = assessments[0]
    current_score = latest.get("overall_score")
    previous_score = assessments[1].get("overall_score") if len(assessments) >= 2 else None
    improvement_pct = calculate_improvement(current_score, previous_score)

    trend = calculate_trend(current_score, previous_score)

    latest_metrics = latest.get("metrics", {})
    strongest_obj = identify_strongest_metric(latest_metrics)
    strongest = strongest_obj["name"] if strongest_obj else None

    weakest_obj = identify_weakest_metric(latest_metrics)
    weakest = weakest_obj["name"] if weakest_obj else None

    history_items = []
    for a in assessments:
        d = a.get("date") or a.get("assessment_date")
        history_items.append({
            "id": str(a["_id"]),
            "date": d.isoformat() if hasattr(d, "isoformat") else str(d),
            "overall_score": a.get("overall_score"),
            "notes": a.get("notes") or a.get("remarks"),
        })

    return AthletePerformanceReport(
        athlete_id=athlete_id,
        athlete_name=athlete.get("full_name", ""),
        sport_id=str(athlete["sport_id"]) if athlete.get("sport_id") else None,
        sport_name=sport_name,
        current_score=current_score,
        previous_score=previous_score,
        improvement_pct=improvement_pct,
        trend=trend,
        strongest_metric=strongest,
        weakest_metric=weakest,
        total_assessments=len(assessments),
        assessment_history=history_items,
        generated_at=now,
    )


async def get_athlete_attendance_report_service(
    db: AsyncIOMotorDatabase,
    athlete_id: str,
    current_user: dict,
) -> AthleteAttendanceReport:
    athlete = await get_athlete_by_id(db, athlete_id)
    if not athlete:
        raise NotFoundError("Athlete not found")

    await _verify_athlete_report_access(db, athlete, current_user)

    applicable_sessions = await get_athlete_applicable_sessions(db, athlete_id)
    attendance_records = await get_athlete_attendance_records(db, athlete_id)

    stats = calculate_attendance_analytics(attendance_records, len(applicable_sessions))
    now = datetime.now(timezone.utc)

    sport_name = None
    if athlete.get("sport_id"):
        sp = await get_sport_by_id(db, str(athlete["sport_id"]))
        if sp:
            sport_name = sp.get("name")

    history_records = []
    for r in attendance_records:
        history_records.append({
            "id": str(r["_id"]),
            "session_id": str(r.get("session_id")),
            "status": r.get("status"),
            "remarks": r.get("remarks"),
        })

    return AthleteAttendanceReport(
        athlete_id=athlete_id,
        athlete_name=athlete.get("full_name", ""),
        sport_id=str(athlete["sport_id"]) if athlete.get("sport_id") else None,
        sport_name=sport_name,
        total_sessions=stats["total_sessions"],
        attended_sessions=stats["attended_sessions"],
        present_count=stats["present_count"],
        late_count=stats["late_count"],
        absent_count=stats["absent_count"],
        attendance_percentage=stats["percentage"],
        warning=stats["warning"],
        records=history_records,
        generated_at=now,
    )


async def get_athlete_tournaments_report_service(
    db: AsyncIOMotorDatabase,
    athlete_id: str,
    current_user: dict,
) -> AthleteTournamentsReport:
    athlete = await get_athlete_by_id(db, athlete_id)
    if not athlete:
        raise NotFoundError("Athlete not found")

    await _verify_athlete_report_access(db, athlete, current_user)

    try:
        a_oid = ObjectId(athlete_id)
    except Exception:
        raise NotFoundError("Invalid athlete ID")

    participants = await db.tournament_participants.find({"athlete_id": a_oid}).to_list(length=500)
    now = datetime.now(timezone.utc)

    sport_name = None
    if athlete.get("sport_id"):
        sp = await get_sport_by_id(db, str(athlete["sport_id"]))
        if sp:
            sport_name = sp.get("name")

    history = []
    medals = {"gold": 0, "silver": 0, "bronze": 0, "total": 0}
    total_pts = 0.0

    for p in participants:
        t_id = str(p.get("tournament_id"))
        tournament = await db.tournaments.find_one({"_id": ObjectId(t_id)}) if ObjectId.is_valid(t_id) else None
        t_name = tournament.get("name", "Tournament") if tournament else "Tournament"

        t_sport_name = None
        if tournament and tournament.get("sport_id"):
            tsp = await get_sport_by_id(db, str(tournament["sport_id"]))
            if tsp:
                t_sport_name = tsp.get("name")

        medal = p.get("medal")
        if medal:
            m_key = medal.strip().lower()
            if m_key in medals:
                medals[m_key] += 1
                medals["total"] += 1

        pts = float(p.get("points") or 0.0)
        total_pts += pts

        history.append(
            AthleteTournamentReportItem(
                tournament_id=t_id,
                tournament_name=t_name,
                sport_name=t_sport_name,
                start_date=tournament.get("start_date") if tournament else None,
                end_date=tournament.get("end_date") if tournament else None,
                event=p.get("event"),
                status=p.get("status", "registered"),
                position=p.get("position"),
                score=p.get("score"),
                points=p.get("points"),
                medal=medal,
                remarks=p.get("remarks"),
            )
        )

    return AthleteTournamentsReport(
        athlete_id=athlete_id,
        athlete_name=athlete.get("full_name", ""),
        sport_name=sport_name,
        total_tournaments=len(history),
        total_points=round(total_pts, 2),
        medals_summary=medals,
        history=history,
        generated_at=now,
    )


async def get_athlete_development_summary_service(
    db: AsyncIOMotorDatabase,
    athlete_id: str,
    current_user: dict,
) -> AthleteDevelopmentSummaryReport:
    athlete = await get_athlete_by_id(db, athlete_id)
    if not athlete:
        raise NotFoundError("Athlete not found")

    await _verify_athlete_report_access(db, athlete, current_user)

    perf_report = await get_athlete_performance_report_service(db, athlete_id, current_user)
    att_report = await get_athlete_attendance_report_service(db, athlete_id, current_user)
    tour_report = await get_athlete_tournaments_report_service(db, athlete_id, current_user)

    coach_name = None
    if athlete.get("coach_id"):
        coach = await db.coaches.find_one({"_id": athlete["coach_id"]})
        if coach:
            coach_name = coach.get("full_name")

    now = datetime.now(timezone.utc)

    return AthleteDevelopmentSummaryReport(
        athlete_id=athlete_id,
        athlete_name=athlete.get("full_name", ""),
        email=athlete.get("email", ""),
        sport_name=perf_report.sport_name,
        coach_name=coach_name,
        status=athlete.get("status", "active"),
        attendance_summary={
            "total_sessions": att_report.total_sessions,
            "attended_sessions": att_report.attended_sessions,
            "attendance_percentage": att_report.attendance_percentage,
            "warning": att_report.warning,
        },
        performance_summary={
            "current_score": perf_report.current_score,
            "previous_score": perf_report.previous_score,
            "improvement_pct": perf_report.improvement_pct,
            "trend": perf_report.trend,
            "strongest_metric": perf_report.strongest_metric,
            "weakest_metric": perf_report.weakest_metric,
            "total_assessments": perf_report.total_assessments,
        },
        tournaments_summary={
            "total_tournaments": tour_report.total_tournaments,
            "total_points": tour_report.total_points,
            "medals_summary": tour_report.medals_summary,
        },
        generated_at=now,
    )


# ── Academy Wide Reports ───────────────────────────────────────────────────────

async def get_academy_summary_report_service(
    db: AsyncIOMotorDatabase,
    current_user: dict,
) -> AcademySummaryReport:
    if current_user.get("role") != "admin":
        raise ForbiddenError("Only admins can access academy-wide summary report")

    total_athletes = await db.athletes.count_documents({})
    total_coaches = await db.coaches.count_documents({})
    total_sports = await db.sports.count_documents({"is_active": True})
    total_sessions = await db.training_sessions.count_documents({})
    total_attendance = await db.attendance.count_documents({})

    # Academy average attendance percentage
    athletes = await db.athletes.find({}).to_list(length=1000)
    total_att_pct_sum = 0.0
    athletes_with_sessions = 0
    for ath in athletes:
        a_id = str(ath["_id"])
        sessions = await get_athlete_applicable_sessions(db, a_id)
        records = await get_athlete_attendance_records(db, a_id)
        stats = calculate_attendance_analytics(records, len(sessions))
        if stats["percentage"] is not None:
            total_att_pct_sum += stats["percentage"]
            athletes_with_sessions += 1

    avg_att_pct = (
        round(total_att_pct_sum / athletes_with_sessions, 1)
        if athletes_with_sessions > 0
        else None
    )

    # Performance
    total_assessments = await db.performance_assessments.count_documents({})
    all_assessments = await db.performance_assessments.find({}).to_list(length=2000)
    score_sum = sum(
        a.get("overall_score") for a in all_assessments if a.get("overall_score") is not None
    )
    score_count = sum(1 for a in all_assessments if a.get("overall_score") is not None)
    avg_score = round(score_sum / score_count, 1) if score_count > 0 else None

    # Tournaments
    total_tournaments = await db.tournaments.count_documents({})
    total_participants = await db.tournament_participants.count_documents({})
    total_medals = await db.tournament_participants.count_documents({
        "medal": {"$in": ["Gold", "Silver", "Bronze", "gold", "silver", "bronze"]}
    })

    now = datetime.now(timezone.utc)
    return AcademySummaryReport(
        total_athletes=total_athletes,
        total_coaches=total_coaches,
        total_sports=total_sports,
        total_training_sessions=total_sessions,
        total_attendance_records=total_attendance,
        average_attendance_percentage=avg_att_pct,
        total_assessments=total_assessments,
        average_performance_score=avg_score,
        total_tournaments=total_tournaments,
        total_tournament_participants=total_participants,
        total_medals_awarded=total_medals,
        generated_at=now,
    )


async def get_academy_attendance_report_service(
    db: AsyncIOMotorDatabase,
    current_user: dict,
    sport_id: Optional[str] = None,
) -> list[AcademyAttendanceReportItem]:
    role = current_user.get("role")
    user_id = current_user.get("user_id")

    if role not in ("admin", "coach"):
        raise ForbiddenError("Only admins and coaches can access attendance reports")

    query = {}
    if sport_id:
        try:
            query["sport_id"] = ObjectId(sport_id)
        except Exception:
            return []

    if role == "coach":
        coach = await get_coach_by_user_id(db, user_id)
        if not coach:
            raise ForbiddenError("Coach profile not found")
        assigned_ids = await get_coach_assigned_athlete_ids(db, str(coach["_id"]))
        query["$or"] = [
            {"coach_id": coach["_id"]},
            {"_id": {"$in": assigned_ids}},
        ]

    athletes = await db.athletes.find(query).to_list(length=1000)

    # Pre-fetch sports & coaches
    sports = {str(s["_id"]): s.get("name") for s in await db.sports.find({}).to_list(length=500)}
    coaches = {str(c["_id"]): c.get("full_name") for c in await db.coaches.find({}).to_list(length=500)}

    results = []
    for ath in athletes:
        a_id = str(ath["_id"])
        sessions = await get_athlete_applicable_sessions(db, a_id)
        records = await get_athlete_attendance_records(db, a_id)
        stats = calculate_attendance_analytics(records, len(sessions))

        sp_name = sports.get(str(ath.get("sport_id")))
        c_name = coaches.get(str(ath.get("coach_id")))

        results.append(
            AcademyAttendanceReportItem(
                athlete_id=a_id,
                athlete_name=ath.get("full_name", ""),
                sport_name=sp_name,
                coach_name=c_name,
                total_sessions=stats["total_sessions"],
                attended_sessions=stats["attended_sessions"],
                attendance_percentage=stats["percentage"],
                warning=stats["warning"],
            )
        )
    return results


def export_attendance_report_to_csv(items: list[AcademyAttendanceReportItem]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Athlete ID",
        "Athlete Name",
        "Sport",
        "Coach",
        "Total Sessions",
        "Attended Sessions",
        "Attendance %",
        "Warning (<75%)",
    ])
    for item in items:
        pct_str = f"{item.attendance_percentage}%" if item.attendance_percentage is not None else "N/A"
        writer.writerow([
            item.athlete_id,
            item.athlete_name,
            item.sport_name or "N/A",
            item.coach_name or "N/A",
            item.total_sessions,
            item.attended_sessions,
            pct_str,
            "YES" if item.warning else "NO",
        ])
    return output.getvalue()


async def get_academy_tournaments_report_service(
    db: AsyncIOMotorDatabase,
    current_user: dict,
    sport_id: Optional[str] = None,
) -> list[AcademyTournamentReportItem]:
    role = current_user.get("role")
    if role not in ("admin", "coach"):
        raise ForbiddenError("Only admins and coaches can access tournament reports")

    query = {}
    if sport_id:
        try:
            query["sport_id"] = ObjectId(sport_id)
        except Exception:
            return []

    tournaments = await db.tournaments.find(query).sort("start_date", -1).to_list(length=500)
    sports = {str(s["_id"]): s.get("name") for s in await db.sports.find({}).to_list(length=500)}

    results = []
    for t in tournaments:
        t_id_str = str(t["_id"])
        parts = await db.tournament_participants.find({"tournament_id": t["_id"]}).to_list(length=500)
        total_p = len(parts)

        # Medalists
        gold = None
        silver = None
        bronze = None

        for p in parts:
            m = (p.get("medal") or "").strip().lower()
            if m in ("gold", "silver", "bronze"):
                ath = await db.athletes.find_one({"_id": p["athlete_id"]})
                ath_name = ath.get("full_name") if ath else "Athlete"
                if m == "gold" and not gold:
                    gold = ath_name
                elif m == "silver" and not silver:
                    silver = ath_name
                elif m == "bronze" and not bronze:
                    bronze = ath_name

        sp_name = sports.get(str(t.get("sport_id")))
        results.append(
            AcademyTournamentReportItem(
                tournament_id=t_id_str,
                tournament_name=t.get("name", "Tournament"),
                sport_name=sp_name,
                status=t.get("status", "upcoming"),
                start_date=t.get("start_date"),
                total_participants=total_p,
                gold_medalist=gold,
                silver_medalist=silver,
                bronze_medalist=bronze,
            )
        )
    return results


def export_tournaments_report_to_csv(items: list[AcademyTournamentReportItem]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Tournament ID",
        "Tournament Name",
        "Sport",
        "Status",
        "Start Date",
        "Total Participants",
        "Gold Medalist",
        "Silver Medalist",
        "Bronze Medalist",
    ])
    for item in items:
        dt_str = item.start_date.strftime("%Y-%m-%d") if item.start_date else "N/A"
        writer.writerow([
            item.tournament_id,
            item.tournament_name,
            item.sport_name or "N/A",
            item.status,
            dt_str,
            item.total_participants,
            item.gold_medalist or "N/A",
            item.silver_medalist or "N/A",
            item.bronze_medalist or "N/A",
        ])
    return output.getvalue()
