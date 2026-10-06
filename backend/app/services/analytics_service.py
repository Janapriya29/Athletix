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
    count_total_assessments,
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
    get_coach_by_id,
    get_coach_by_user_id,
)
from app.repositories.sport_repository import get_sport_by_id
from app.schemas.analytics import (
    AdminAnalyticsSummary,
    AdminSportsAnalyticsResponse,
    AssessmentHistoryItem,
    AthleteAnalyticsResponse,
    AthleteAnalyticsSummary,
    AttendanceAnalytics,
    CoachAnalyticsSummary,
    MetricScore,
    PerformanceScoreInfo,
    SportAnalyticsItem,
)

logger = logging.getLogger(__name__)


# ── Helper: Compute Single Athlete Analytics Bundle ───────────────────────────

async def _compute_athlete_analytics(
    db: AsyncIOMotorDatabase,
    athlete_doc: dict,
) -> dict:
    """
    Computes all analytics for a given athlete document.
    Returns a dictionary of raw computed fields.
    """
    ath_id_str = str(athlete_doc["_id"])

    # 1. Fetch assessments sorted date desc
    assessments = await get_athlete_assessments(db, ath_id_str, sort_ascending=False)

    curr_perf = None
    prev_perf = None
    improvement = None
    trend = "Insufficient Data"
    strongest = None
    weakest = None
    metrics_list = []
    history_items = []

    if len(assessments) == 1:
        latest = assessments[0]
        c_score = latest.get("overall_score")
        c_date = latest.get("date")
        curr_perf = PerformanceScoreInfo(score=c_score, assessment_date=c_date)
        strongest_dict = identify_strongest_metric(latest.get("metrics"))
        weakest_dict = identify_weakest_metric(latest.get("metrics"))
        if strongest_dict:
            strongest = MetricScore(**strongest_dict)
        if weakest_dict:
            weakest = MetricScore(**weakest_dict)
        metrics_list = [
            MetricScore(name=str(k), score=float(v))
            for k, v in (latest.get("metrics") or {}).items()
            if v is not None
        ]
        history_items.append(
            AssessmentHistoryItem(
                id=str(latest["_id"]),
                date=c_date,
                overall_score=c_score,
                improvement_percentage=None,
                trend="Insufficient Data",
                metrics={str(k): float(v) for k, v in (latest.get("metrics") or {}).items() if v is not None},
                remarks=latest.get("remarks"),
            )
        )

    elif len(assessments) >= 2:
        latest = assessments[0]
        previous = assessments[1]
        c_score = latest.get("overall_score")
        c_date = latest.get("date")
        p_score = previous.get("overall_score")
        p_date = previous.get("date")

        curr_perf = PerformanceScoreInfo(score=c_score, assessment_date=c_date)
        prev_perf = PerformanceScoreInfo(score=p_score, assessment_date=p_date)
        improvement = calculate_improvement(c_score, p_score)
        trend = calculate_trend(c_score, p_score)

        strongest_dict = identify_strongest_metric(latest.get("metrics"))
        weakest_dict = identify_weakest_metric(latest.get("metrics"))
        if strongest_dict:
            strongest = MetricScore(**strongest_dict)
        if weakest_dict:
            weakest = MetricScore(**weakest_dict)
        metrics_list = [
            MetricScore(name=str(k), score=float(v))
            for k, v in (latest.get("metrics") or {}).items()
            if v is not None
        ]

        # Build chronological history
        for i in range(len(assessments)):
            item = assessments[i]
            i_score = item.get("overall_score")
            i_date = item.get("date")
            if i + 1 < len(assessments):
                older = assessments[i + 1]
                o_score = older.get("overall_score")
                it_imp = calculate_improvement(i_score, o_score)
                it_trend = calculate_trend(i_score, o_score)
            else:
                it_imp = None
                it_trend = "Insufficient Data"

            history_items.append(
                AssessmentHistoryItem(
                    id=str(item["_id"]),
                    date=i_date,
                    overall_score=i_score,
                    improvement_percentage=it_imp,
                    trend=it_trend,
                    metrics={str(k): float(v) for k, v in (item.get("metrics") or {}).items() if v is not None},
                    remarks=item.get("remarks"),
                )
            )

    # 2. Fetch applicable sessions & attendance records
    applicable_sessions = await get_athlete_applicable_sessions(db, ath_id_str)
    all_att_records = await get_athlete_attendance_records(db, ath_id_str)
    app_sess_ids = {str(s["_id"]) for s in applicable_sessions}
    valid_att_records = [r for r in all_att_records if str(r.get("session_id", "")) in app_sess_ids]

    attendance_data = calculate_attendance_analytics(valid_att_records, len(applicable_sessions))
    attendance = AttendanceAnalytics(**attendance_data)

    return {
        "current_performance": curr_perf,
        "previous_performance": prev_perf,
        "improvement_percentage": improvement,
        "trend": trend,
        "strongest_metric": strongest,
        "weakest_metric": weakest,
        "metrics": metrics_list,
        "attendance": attendance,
        "assessment_history": history_items,
    }


# ── 1. Single Athlete Full Analytics ──────────────────────────────────────────

async def get_athlete_analytics_service(
    db: AsyncIOMotorDatabase,
    athlete_id: str,
    current_user: dict,
) -> AthleteAnalyticsResponse:
    athlete = await get_athlete_by_id(db, athlete_id)
    if not athlete:
        raise NotFoundError("Athlete not found")

    role = current_user.get("role")
    user_id = current_user.get("user_id")

    # RBAC Enforcement
    if role == "athlete":
        if str(athlete.get("user_id", "")) != user_id:
            raise ForbiddenError("You can only view your own analytics")

    elif role == "coach":
        coach = await get_coach_by_user_id(db, user_id)
        if not coach:
            raise ForbiddenError("Coach profile not found")
        assigned_ids = await get_coach_assigned_athlete_ids(db, str(coach["_id"]))
        is_direct = str(athlete.get("coach_id", "")) == str(coach["_id"])
        is_assigned = athlete["_id"] in assigned_ids
        if not is_direct and not is_assigned:
            raise ForbiddenError("You can only view analytics for your assigned athletes")

    elif role != "admin":
        raise ForbiddenError("Insufficient permissions")

    # Sport & Coach name resolution
    sport_name = None
    if athlete.get("sport_id"):
        sp = await get_sport_by_id(db, str(athlete["sport_id"]))
        if sp:
            sport_name = sp.get("name")

    coach_name = None
    if athlete.get("coach_id"):
        c = await get_coach_by_id(db, str(athlete["coach_id"]))
        if c:
            coach_name = c.get("full_name")

    analytics_bundle = await _compute_athlete_analytics(db, athlete)

    return AthleteAnalyticsResponse(
        athlete_id=str(athlete["_id"]),
        athlete_name=athlete.get("full_name", ""),
        sport_id=str(athlete.get("sport_id", "")) if athlete.get("sport_id") else None,
        sport_name=sport_name,
        coach_id=str(athlete.get("coach_id", "")) if athlete.get("coach_id") else None,
        coach_name=coach_name,
        **analytics_bundle,
    )


async def get_my_athlete_analytics_service(
    db: AsyncIOMotorDatabase,
    current_user: dict,
) -> AthleteAnalyticsResponse:
    if current_user.get("role") != "athlete":
        raise ForbiddenError("Only athletes can access /analytics/athlete/me")

    athlete = await get_athlete_by_user_id(db, current_user["user_id"])
    if not athlete:
        raise NotFoundError("Athlete profile not found")

    return await get_athlete_analytics_service(db, str(athlete["_id"]), current_user)


# ── 2. Coach Analytics ────────────────────────────────────────────────────────

async def get_coach_assigned_athletes(
    db: AsyncIOMotorDatabase,
    coach_user_id: str,
    sport_id: Optional[str] = None,
) -> tuple[dict, list[dict]]:
    coach = await get_coach_by_user_id(db, coach_user_id)
    if not coach:
        raise ForbiddenError("Coach profile not found")

    assigned_ids = await get_coach_assigned_athlete_ids(db, str(coach["_id"]))
    query = {
        "$or": [
            {"coach_id": coach["_id"]},
            {"_id": {"$in": assigned_ids}},
        ]
    }
    if sport_id:
        try:
            query["sport_id"] = ObjectId(sport_id)
        except Exception:
            return coach, []

    cursor = db.athletes.find(query).sort("full_name", 1)
    athletes = await cursor.to_list(length=500)
    return coach, athletes


async def get_coach_summary_analytics_service(
    db: AsyncIOMotorDatabase,
    coach_user_id: str,
) -> CoachAnalyticsSummary:
    coach, athletes = await get_coach_assigned_athletes(db, coach_user_id)

    scores = []
    attendance_rates = []
    improving_count = 0
    declining_count = 0
    stable_count = 0
    below_att_count = 0

    for a in athletes:
        bundle = await _compute_athlete_analytics(db, a)
        c_perf = bundle["current_performance"]
        if c_perf and c_perf.score is not None:
            scores.append(c_perf.score)

        tr = bundle["trend"]
        if tr == "Improving":
            improving_count += 1
        elif tr == "Declining":
            declining_count += 1
        elif tr == "Stable":
            stable_count += 1

        att = bundle["attendance"]
        if att.percentage is not None:
            attendance_rates.append(att.percentage)
            if att.warning:
                below_att_count += 1

    avg_perf = round(sum(scores) / len(scores), 2) if scores else None
    avg_att = round(sum(attendance_rates) / len(attendance_rates), 1) if attendance_rates else None

    return CoachAnalyticsSummary(
        total_assigned_athletes=len(athletes),
        average_performance=avg_perf,
        average_attendance=avg_att,
        improving_athletes_count=improving_count,
        declining_athletes_count=declining_count,
        stable_athletes_count=stable_count,
        athletes_below_attendance_threshold=below_att_count,
    )


async def get_coach_athletes_analytics_service(
    db: AsyncIOMotorDatabase,
    coach_user_id: str,
    sport_id: Optional[str] = None,
) -> list[AthleteAnalyticsSummary]:
    coach, athletes = await get_coach_assigned_athletes(db, coach_user_id, sport_id)

    # Pre-cache sports for fast name lookups
    sports_cursor = db.sports.find()
    all_sports = await sports_cursor.to_list(length=100)
    sport_map = {str(s["_id"]): s.get("name") for s in all_sports}

    results = []
    for a in athletes:
        bundle = await _compute_athlete_analytics(db, a)
        c_perf = bundle["current_performance"]
        p_perf = bundle["previous_performance"]
        att = bundle["attendance"]
        sp_id = str(a.get("sport_id", "")) if a.get("sport_id") else None

        results.append(
            AthleteAnalyticsSummary(
                athlete_id=str(a["_id"]),
                athlete_name=a.get("full_name", ""),
                sport_name=sport_map.get(sp_id),
                current_score=c_perf.score if c_perf else None,
                previous_score=p_perf.score if p_perf else None,
                improvement_percentage=bundle["improvement_percentage"],
                trend=bundle["trend"],
                attendance_percentage=att.percentage,
                attendance_warning=att.warning,
                strongest_metric=bundle["strongest_metric"],
                weakest_metric=bundle["weakest_metric"],
            )
        )

    return results


# ── 3. Admin Analytics ────────────────────────────────────────────────────────

async def get_admin_summary_analytics_service(
    db: AsyncIOMotorDatabase,
) -> AdminAnalyticsSummary:
    total_athletes = await db.athletes.count_documents({})
    total_coaches = await db.coaches.count_documents({})
    total_active_sports = await db.sports.count_documents({"is_active": True})
    total_assessments = await count_total_assessments(db)

    # Compute metrics across all athletes
    athletes_cursor = db.athletes.find()
    all_athletes = await athletes_cursor.to_list(length=1000)

    scores = []
    attendance_rates = []
    improving_count = 0
    declining_count = 0
    stable_count = 0
    below_att_count = 0

    for a in all_athletes:
        bundle = await _compute_athlete_analytics(db, a)
        c_perf = bundle["current_performance"]
        if c_perf and c_perf.score is not None:
            scores.append(c_perf.score)

        tr = bundle["trend"]
        if tr == "Improving":
            improving_count += 1
        elif tr == "Declining":
            declining_count += 1
        elif tr == "Stable":
            stable_count += 1

        att = bundle["attendance"]
        if att.percentage is not None:
            attendance_rates.append(att.percentage)
            if att.warning:
                below_att_count += 1

    avg_perf = round(sum(scores) / len(scores), 2) if scores else None
    avg_att = round(sum(attendance_rates) / len(attendance_rates), 1) if attendance_rates else None

    return AdminAnalyticsSummary(
        total_athletes=total_athletes,
        total_coaches=total_coaches,
        total_active_sports=total_active_sports,
        total_assessments=total_assessments,
        average_performance=avg_perf,
        average_attendance=avg_att,
        improving_athletes_count=improving_count,
        declining_athletes_count=declining_count,
        stable_athletes_count=stable_count,
        athletes_below_attendance_threshold=below_att_count,
    )


async def get_admin_sports_analytics_service(
    db: AsyncIOMotorDatabase,
) -> AdminSportsAnalyticsResponse:
    sports_cursor = db.sports.find({"is_active": True}).sort("name", 1)
    sports = await sports_cursor.to_list(length=100)

    results = []
    for s in sports:
        s_id = s["_id"]
        # Athletes with this primary sport
        athletes_cursor = db.athletes.find({"sport_id": s_id})
        sport_athletes = await athletes_cursor.to_list(length=500)
        ath_count = len(sport_athletes)

        # Assessments count for this sport
        assess_count = await count_total_assessments(db, str(s_id))

        scores = []
        attendance_rates = []
        for a in sport_athletes:
            bundle = await _compute_athlete_analytics(db, a)
            c_perf = bundle["current_performance"]
            if c_perf and c_perf.score is not None:
                scores.append(c_perf.score)
            att = bundle["attendance"]
            if att.percentage is not None:
                attendance_rates.append(att.percentage)

        avg_perf = round(sum(scores) / len(scores), 2) if scores else None
        avg_att = round(sum(attendance_rates) / len(attendance_rates), 1) if attendance_rates else None

        results.append(
            SportAnalyticsItem(
                sport_id=str(s_id),
                sport_name=s.get("name", ""),
                athlete_count=ath_count,
                assessment_count=assess_count,
                average_performance=avg_perf,
                average_attendance=avg_att,
            )
        )

    return AdminSportsAnalyticsResponse(sports=results)
