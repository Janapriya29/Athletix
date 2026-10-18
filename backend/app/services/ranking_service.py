import logging
from typing import Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.analytics.performance import (
    calculate_attendance_analytics,
    calculate_improvement,
)
from app.core.exceptions import BadRequestError
from app.repositories.analytics_repository import (
    get_athlete_applicable_sessions,
    get_athlete_assessments,
    get_athlete_attendance_records,
)
from app.repositories.sport_repository import get_sport_by_id
from app.schemas.ranking import (
    AttendanceRankingItem,
    ImprovementRankingItem,
    PerformanceRankingItem,
    RankingsResponse,
    TournamentRankingItem,
)

logger = logging.getLogger(__name__)


async def _get_athlete_map_and_sports(db: AsyncIOMotorDatabase) -> tuple[dict, dict]:
    """Helper to pre-fetch athletes and sports maps for efficient joining."""
    athletes_cursor = db.athletes.find()
    athletes = await athletes_cursor.to_list(length=1000)
    athlete_map = {str(a["_id"]): a for a in athletes}

    sports_cursor = db.sports.find()
    sports = await sports_cursor.to_list(length=100)
    sport_map = {str(s["_id"]): s.get("name", "") for s in sports}

    return athlete_map, sport_map


# ── 1. Tournament Rankings ─────────────────────────────────────────────────────

async def get_tournament_rankings_service(
    db: AsyncIOMotorDatabase,
    sport_id: Optional[str] = None,
    include_zero: bool = False,
) -> list[TournamentRankingItem]:
    """
    Computes tournament points and medal rankings based on real tournament results.
    When include_zero is True, eligible athletes with zero tournament participation
    are included with 0 points, 0 medals, and 0 tournaments played.
    Deterministic sorting:
    1. Points descending (-points)
    2. Gold medal count descending (-gold_count)
    3. Silver medal count descending (-silver_count)
    4. Bronze medal count descending (-bronze_count)
    5. Tournaments played descending (-tournaments_played)
    6. Athlete name ascending (athlete_name.lower())
    """
    athlete_map, sport_map = await _get_athlete_map_and_sports(db)

    # Filter tournaments by sport if sport_id is provided
    tournament_filter = {}
    if sport_id:
        sport = await get_sport_by_id(db, sport_id)
        if not sport:
            raise BadRequestError("Sport not found")
        s_matches = [str(sport_id)]
        try:
            s_matches.append(ObjectId(sport_id))
        except Exception:
            pass
        tournament_filter["sport_id"] = {"$in": s_matches}

    matching_tournaments = await db.tournaments.find(tournament_filter).to_list(length=1000)
    matching_tournament_ids = {t["_id"] for t in matching_tournaments}

    if sport_id and not matching_tournament_ids and not include_zero:
        return []

    # Find participations
    part_query = {}
    if sport_id:
        t_matches = list(matching_tournament_ids) + [str(t) for t in matching_tournament_ids]
        part_query["tournament_id"] = {"$in": t_matches}

    participations = await db.tournament_participants.find(part_query).to_list(length=5000)

    # Aggregate by athlete
    athlete_stats: dict[str, dict] = {}

    if include_zero:
        sp_str_matches = {str(sport_id)} if sport_id else set()
        for a_id, ath in athlete_map.items():
            if sport_id:
                ath_sp_str = str(ath.get("sport_id", ""))
                add_sp_strs = {str(sid) for sid in (ath.get("additional_sport_ids") or []) if sid}
                if ath_sp_str not in sp_str_matches and not (add_sp_strs & sp_str_matches):
                    continue

            ath_sport_id = str(ath.get("sport_id", ""))
            athlete_stats[a_id] = {
                "athlete_id": a_id,
                "athlete_name": ath.get("full_name", "Unknown Athlete"),
                "sport_id": ath_sport_id,
                "sport_name": sport_map.get(ath_sport_id, ""),
                "points": 0.0,
                "gold_count": 0,
                "silver_count": 0,
                "bronze_count": 0,
                "tournaments": set(),
            }

    for p in participations:
        a_id = str(p["athlete_id"])
        if a_id not in athlete_map:
            continue

        if a_id not in athlete_stats:
            if not include_zero:
                ath = athlete_map[a_id]
                ath_sport_id = str(ath.get("sport_id", ""))
                athlete_stats[a_id] = {
                    "athlete_id": a_id,
                    "athlete_name": ath.get("full_name", "Unknown Athlete"),
                    "sport_id": ath_sport_id,
                    "sport_name": sport_map.get(ath_sport_id, ""),
                    "points": 0.0,
                    "gold_count": 0,
                    "silver_count": 0,
                    "bronze_count": 0,
                    "tournaments": set(),
                }
            else:
                continue

        stats = athlete_stats[a_id]
        stats["tournaments"].add(str(p["tournament_id"]))

        # Add points if recorded
        pts = p.get("points")
        if pts is not None:
            try:
                stats["points"] += float(pts)
            except (ValueError, TypeError):
                pass

        # Medals
        pos = p.get("position")
        med = str(p.get("medal") or "").strip().lower()
        if pos == 1 or med == "gold":
            stats["gold_count"] += 1
        elif pos == 2 or med == "silver":
            stats["silver_count"] += 1
        elif pos == 3 or med == "bronze":
            stats["bronze_count"] += 1

    # Deterministic sorting
    raw_items = list(athlete_stats.values())
    raw_items.sort(
        key=lambda x: (
            -x["points"],
            -x["gold_count"],
            -x["silver_count"],
            -x["bronze_count"],
            -len(x["tournaments"]),
            x["athlete_name"].lower(),
        )
    )

    ranked_items = []
    for rank, item in enumerate(raw_items, start=1):
        total_medals = item["gold_count"] + item["silver_count"] + item["bronze_count"]
        ranked_items.append(
            TournamentRankingItem(
                rank=rank,
                athlete_id=item["athlete_id"],
                athlete_name=item["athlete_name"],
                sport_id=item["sport_id"] or None,
                sport_name=item["sport_name"] or None,
                points=round(item["points"], 2),
                gold_count=item["gold_count"],
                silver_count=item["silver_count"],
                bronze_count=item["bronze_count"],
                total_medals=total_medals,
                tournaments_played=len(item["tournaments"]),
            )
        )

    return ranked_items


# ── 2. Performance Rankings ────────────────────────────────────────────────────

async def get_performance_rankings_service(
    db: AsyncIOMotorDatabase,
    sport_id: Optional[str] = None,
    include_zero: bool = False,
) -> list[PerformanceRankingItem]:
    """
    Computes performance rankings based on the latest assessment overall_score.
    When include_zero is True, unassessed eligible athletes are also included
    with performance_score=None and assessment_date=None, placed after assessed athletes.
    Deterministic sorting:
    1. Performance score descending (-performance_score)
    2. Athlete name ascending (athlete_name.lower())
    """
    athlete_map, sport_map = await _get_athlete_map_and_sports(db)

    # Filter athletes by sport
    target_athletes = []
    if sport_id:
        sport = await get_sport_by_id(db, sport_id)
        if not sport:
            raise BadRequestError("Sport not found")
        sp_str_matches = {str(sport_id)}
        for a in athlete_map.values():
            ath_sp = str(a.get("sport_id", ""))
            add_sps = {str(sid) for sid in (a.get("additional_sport_ids") or []) if sid}
            if ath_sp in sp_str_matches or (add_sps & sp_str_matches):
                target_athletes.append(a)
    else:
        target_athletes = list(athlete_map.values())

    scored_athletes = []
    unscored_athletes = []
    for ath in target_athletes:
        a_id_str = str(ath["_id"])
        assessments = await get_athlete_assessments(db, a_id_str, sort_ascending=False)
        ath_sport_id = str(ath.get("sport_id", ""))
        sport_name = sport_map.get(ath_sport_id, "")

        if not assessments:
            if include_zero:
                unscored_athletes.append({
                    "athlete_id": a_id_str,
                    "athlete_name": ath.get("full_name", "Unknown Athlete"),
                    "sport_id": ath_sport_id,
                    "sport_name": sport_name,
                    "performance_score": None,
                    "assessment_date": None,
                })
            continue

        latest = assessments[0]
        score = latest.get("overall_score")
        if score is None:
            if include_zero:
                unscored_athletes.append({
                    "athlete_id": a_id_str,
                    "athlete_name": ath.get("full_name", "Unknown Athlete"),
                    "sport_id": ath_sport_id,
                    "sport_name": sport_name,
                    "performance_score": None,
                    "assessment_date": None,
                })
            continue

        scored_athletes.append({
            "athlete_id": a_id_str,
            "athlete_name": ath.get("full_name", "Unknown Athlete"),
            "sport_id": ath_sport_id,
            "sport_name": sport_name,
            "performance_score": float(score),
            "assessment_date": latest.get("date") or latest.get("assessment_date") or latest.get("created_at"),
        })

    # Deterministic sorting
    scored_athletes.sort(
        key=lambda x: (
            -x["performance_score"],
            x["athlete_name"].lower(),
        )
    )
    unscored_athletes.sort(key=lambda x: x["athlete_name"].lower())

    all_items = scored_athletes + unscored_athletes
    ranked_items = []
    for rank, item in enumerate(all_items, start=1):
        ranked_items.append(
            PerformanceRankingItem(
                rank=rank,
                athlete_id=item["athlete_id"],
                athlete_name=item["athlete_name"],
                sport_id=item["sport_id"] or None,
                sport_name=item["sport_name"] or None,
                performance_score=round(item["performance_score"], 2) if item["performance_score"] is not None else None,
                assessment_date=item["assessment_date"],
            )
        )

    return ranked_items


# ── 3. Attendance Rankings ─────────────────────────────────────────────────────

async def get_attendance_rankings_service(
    db: AsyncIOMotorDatabase,
    sport_id: Optional[str] = None,
    include_zero: bool = False,
) -> list[AttendanceRankingItem]:
    """
    Computes attendance rankings based on Phase 3 attendance formula:
    (Present + Late) / Total Applicable * 100
    Excludes cancelled sessions.
    When include_zero is True, eligible athletes with zero applicable sessions
    are included with attendance_percentage=0.0 and total_sessions=0.
    Deterministic sorting:
    1. Attendance percentage descending (-attendance_percentage)
    2. Total sessions descending (-total_sessions)
    3. Athlete name ascending (athlete_name.lower())
    """
    athlete_map, sport_map = await _get_athlete_map_and_sports(db)

    target_athletes = []
    if sport_id:
        sport = await get_sport_by_id(db, sport_id)
        if not sport:
            raise BadRequestError("Sport not found")
        sp_str_matches = {str(sport_id)}
        for a in athlete_map.values():
            ath_sp = str(a.get("sport_id", ""))
            add_sps = {str(sid) for sid in (a.get("additional_sport_ids") or []) if sid}
            if ath_sp in sp_str_matches or (add_sps & sp_str_matches):
                target_athletes.append(a)
    else:
        target_athletes = list(athlete_map.values())

    attendance_list = []
    unattended_list = []
    for ath in target_athletes:
        a_id_str = str(ath["_id"])
        applicable_sessions = await get_athlete_applicable_sessions(db, a_id_str)
        ath_sport_id = str(ath.get("sport_id", ""))
        sport_name = sport_map.get(ath_sport_id, "")

        if not applicable_sessions:
            if include_zero:
                unattended_list.append({
                    "athlete_id": a_id_str,
                    "athlete_name": ath.get("full_name", "Unknown Athlete"),
                    "sport_id": ath_sport_id,
                    "sport_name": sport_name,
                    "attendance_percentage": 0.0,
                    "total_sessions": 0,
                    "attended_sessions": 0,
                })
            continue

        app_sess_ids = {str(s["_id"]) for s in applicable_sessions}
        all_att_records = await get_athlete_attendance_records(db, a_id_str)
        valid_att_records = [r for r in all_att_records if str(r.get("session_id", "")) in app_sess_ids]

        stats = calculate_attendance_analytics(valid_att_records, len(applicable_sessions))
        pct = stats.get("percentage")
        if pct is None:
            if include_zero:
                unattended_list.append({
                    "athlete_id": a_id_str,
                    "athlete_name": ath.get("full_name", "Unknown Athlete"),
                    "sport_id": ath_sport_id,
                    "sport_name": sport_name,
                    "attendance_percentage": 0.0,
                    "total_sessions": len(applicable_sessions),
                    "attended_sessions": 0,
                })
            continue

        attendance_list.append({
            "athlete_id": a_id_str,
            "athlete_name": ath.get("full_name", "Unknown Athlete"),
            "sport_id": ath_sport_id,
            "sport_name": sport_name,
            "attendance_percentage": float(pct),
            "total_sessions": stats["total_sessions"],
            "attended_sessions": stats["attended_sessions"],
        })

    # Deterministic sorting
    attendance_list.sort(
        key=lambda x: (
            -x["attendance_percentage"],
            -x["total_sessions"],
            x["athlete_name"].lower(),
        )
    )
    unattended_list.sort(key=lambda x: x["athlete_name"].lower())

    all_items = attendance_list + unattended_list
    ranked_items = []
    for rank, item in enumerate(all_items, start=1):
        ranked_items.append(
            AttendanceRankingItem(
                rank=rank,
                athlete_id=item["athlete_id"],
                athlete_name=item["athlete_name"],
                sport_id=item["sport_id"] or None,
                sport_name=item["sport_name"] or None,
                attendance_percentage=round(item["attendance_percentage"], 1),
                total_sessions=item["total_sessions"],
                attended_sessions=item["attended_sessions"],
            )
        )

    return ranked_items


# ── 4. Improvement Rankings ────────────────────────────────────────────────────

async def get_improvement_rankings_service(
    db: AsyncIOMotorDatabase,
    sport_id: Optional[str] = None,
) -> list[ImprovementRankingItem]:
    """
    Computes improvement rankings using Phase 5 improvement percentage.
    Deterministic sorting:
    1. Improvement percentage descending (-improvement_percentage)
    2. Athlete name ascending (athlete_name.lower())
    Only includes athletes with >= 2 assessments and valid improvement score.
    """
    athlete_map, sport_map = await _get_athlete_map_and_sports(db)

    target_athletes = []
    if sport_id:
        sport = await get_sport_by_id(db, sport_id)
        if not sport:
            raise BadRequestError("Sport not found")
        sp_oid = ObjectId(sport_id)
        for a in athlete_map.values():
            if a.get("sport_id") == sp_oid or sp_oid in a.get("additional_sport_ids", []):
                target_athletes.append(a)
    else:
        target_athletes = list(athlete_map.values())

    improvement_list = []
    for ath in target_athletes:
        a_id_str = str(ath["_id"])
        assessments = await get_athlete_assessments(db, a_id_str, sort_ascending=False)
        if len(assessments) < 2:
            continue

        latest = assessments[0]
        previous = assessments[1]
        c_score = latest.get("overall_score")
        p_score = previous.get("overall_score")
        if c_score is None or p_score is None:
            continue

        imp = calculate_improvement(c_score, p_score)
        if imp is None:
            continue

        ath_sport_id = str(ath.get("sport_id", ""))
        improvement_list.append({
            "athlete_id": a_id_str,
            "athlete_name": ath.get("full_name", "Unknown Athlete"),
            "sport_id": ath_sport_id,
            "sport_name": sport_map.get(ath_sport_id, ""),
            "improvement_percentage": float(imp),
            "current_score": float(c_score),
            "previous_score": float(p_score),
        })

    # Deterministic sorting
    improvement_list.sort(
        key=lambda x: (
            -x["improvement_percentage"],
            x["athlete_name"].lower(),
        )
    )

    ranked_items = []
    for rank, item in enumerate(improvement_list, start=1):
        ranked_items.append(
            ImprovementRankingItem(
                rank=rank,
                athlete_id=item["athlete_id"],
                athlete_name=item["athlete_name"],
                sport_id=item["sport_id"] or None,
                sport_name=item["sport_name"] or None,
                improvement_percentage=round(item["improvement_percentage"], 2),
                current_score=round(item["current_score"], 2),
                previous_score=round(item["previous_score"], 2),
            )
        )

    return ranked_items


# ── 5. Unified Rankings Dispatcher ─────────────────────────────────────────────

async def get_rankings_service(
    db: AsyncIOMotorDatabase,
    ranking_type: str = "tournament",
    sport_id: Optional[str] = None,
    include_zero: bool = True,
) -> RankingsResponse:
    norm_type = ranking_type.strip().lower()

    sport_name = None
    if sport_id:
        sport = await get_sport_by_id(db, sport_id)
        if not sport:
            raise BadRequestError("Sport not found")
        sport_name = sport.get("name")

    if norm_type == "tournament":
        items = await get_tournament_rankings_service(db, sport_id=sport_id, include_zero=include_zero)
    elif norm_type == "performance":
        items = await get_performance_rankings_service(db, sport_id=sport_id, include_zero=include_zero)
    elif norm_type == "attendance":
        items = await get_attendance_rankings_service(db, sport_id=sport_id, include_zero=include_zero)
    elif norm_type == "improvement":
        items = await get_improvement_rankings_service(db, sport_id=sport_id)
    else:
        raise BadRequestError(
            f"Invalid ranking type '{ranking_type}'. Supported types: tournament, performance, attendance, improvement"
        )

    return RankingsResponse(
        type=norm_type,
        sport_id=sport_id,
        sport_name=sport_name,
        items=items,
    )
