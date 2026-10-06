"""
Performance Analytics tests — Phase 5.
Covers all 25 specific test cases from the specification:
1. Athlete can access own analytics
2. Athlete cannot access another athlete's analytics (403)
3. Athlete cannot access coach analytics (403)
4. Athlete cannot access admin analytics (403)
5. Coach can access assigned athlete analytics
6. Coach cannot access unassigned athlete analytics (403)
7. Coach summary only includes assigned athletes
8. Admin can access academy analytics
9. Admin can access all athlete analytics
10. Current performance is calculated correctly
11. Previous performance is calculated correctly
12. Improvement percentage is calculated correctly
13. Zero previous score is handled safely
14. Insufficient history is handled correctly
15. Trend calculation works (Improving, Declining, Stable, Insufficient Data)
16. Strongest metric is correct
17. Weakest metric is correct
18. Attendance percentage uses existing Phase 3 logic
19. Cancelled sessions are excluded
20. Attendance warning is true below 75%
21. No attendance data is handled correctly (percentage is None, not fake 0%)
22. No assessment data is handled correctly
23. Multiple assessment history is sorted correctly
24. Sport filtering works
25. Unauthenticated analytics request returns 401
"""
from datetime import datetime, timedelta, timezone
import pytest

from app.analytics.performance import (
    calculate_attendance_analytics,
    calculate_improvement,
    calculate_trend,
    identify_strongest_metric,
    identify_weakest_metric,
)


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── Fixture setup ──────────────────────────────────────────────────────────────

async def _setup_analytics_fixture(db, admin_user, coach_user, athlete_user):
    now = datetime.now(timezone.utc)

    # 1. Sports
    s_fb = await db.sports.insert_one({"name": "Football", "is_active": True, "created_at": now})
    football_id = s_fb.inserted_id

    s_cr = await db.sports.insert_one({"name": "Cricket", "is_active": True, "created_at": now})
    cricket_id = s_cr.inserted_id

    # 2. Coaches
    c1_doc = await db.coaches.insert_one({
        "user_id": coach_user["_id"],
        "full_name": coach_user["full_name"],
        "email": coach_user["email"],
        "status": "active",
        "sport_ids": [football_id],
        "created_at": now,
    })
    coach1_id = c1_doc.inserted_id

    # Second coach
    u_c2 = await db.users.insert_one({
        "email": "coach2@test.com",
        "role": "coach",
        "full_name": "Coach Two",
        "is_active": True,
        "created_at": now,
    })
    c2_doc = await db.coaches.insert_one({
        "user_id": u_c2.inserted_id,
        "full_name": "Coach Two",
        "email": "coach2@test.com",
        "status": "active",
        "sport_ids": [cricket_id],
        "created_at": now,
    })
    coach2_id = c2_doc.inserted_id

    # 3. Athletes
    # Athlete 1 -> coach 1
    a1_doc = await db.athletes.insert_one({
        "user_id": athlete_user["_id"],
        "full_name": athlete_user["full_name"],
        "email": athlete_user["email"],
        "status": "active",
        "sport_id": football_id,
        "coach_id": coach1_id,
        "created_at": now,
    })
    athlete1_id = a1_doc.inserted_id

    await db.coach_athlete_assignments.insert_one({
        "coach_id": coach1_id,
        "athlete_id": athlete1_id,
        "assigned_at": now,
    })

    # Athlete 2 -> coach 2 (unassigned to coach 1)
    u_a2 = await db.users.insert_one({
        "email": "athlete2@test.com",
        "role": "athlete",
        "full_name": "Athlete Two",
        "is_active": True,
        "created_at": now,
    })
    a2_doc = await db.athletes.insert_one({
        "user_id": u_a2.inserted_id,
        "full_name": "Athlete Two",
        "email": "athlete2@test.com",
        "status": "active",
        "sport_id": cricket_id,
        "coach_id": coach2_id,
        "created_at": now,
    })
    athlete2_id = a2_doc.inserted_id

    await db.coach_athlete_assignments.insert_one({
        "coach_id": coach2_id,
        "athlete_id": athlete2_id,
        "assigned_at": now,
    })

    # 4. Assessments for Athlete 1
    d1 = now - timedelta(days=60)
    d2 = now - timedelta(days=30)
    d3 = now - timedelta(days=5)

    await db.performance_assessments.insert_many([
        {
            "athlete_id": athlete1_id,
            "coach_id": coach1_id,
            "sport_id": football_id,
            "date": d1,
            "overall_score": 70.0,
            "metrics": {"speed": 70.0, "passing": 65.0, "shooting": 75.0},
            "remarks": "Initial assessment",
            "created_at": d1,
        },
        {
            "athlete_id": athlete1_id,
            "coach_id": coach1_id,
            "sport_id": football_id,
            "date": d2,
            "overall_score": 77.0,
            "metrics": {"speed": 75.0, "passing": 72.0, "shooting": 84.0},
            "remarks": "Mid-term check",
            "created_at": d2,
        },
        {
            "athlete_id": athlete1_id,
            "coach_id": coach1_id,
            "sport_id": football_id,
            "date": d3,
            "overall_score": 84.0,
            "metrics": {"speed": 82.0, "passing": 79.0, "shooting": 91.0},
            "remarks": "Latest assessment",
            "created_at": d3,
        },
    ])

    # 5. Training sessions and attendance for Athlete 1
    sess1 = await db.training_sessions.insert_one({
        "title": "Tactical 1",
        "sport_id": football_id,
        "coach_id": coach1_id,
        "session_date": now - timedelta(days=15),
        "status": "completed",
        "athlete_ids": [athlete1_id],
        "created_at": now,
    })
    sess2 = await db.training_sessions.insert_one({
        "title": "Tactical 2",
        "sport_id": football_id,
        "coach_id": coach1_id,
        "session_date": now - timedelta(days=10),
        "status": "completed",
        "athlete_ids": [athlete1_id],
        "created_at": now,
    })
    sess3 = await db.training_sessions.insert_one({
        "title": "Tactical 3",
        "sport_id": football_id,
        "coach_id": coach1_id,
        "session_date": now - timedelta(days=5),
        "status": "completed",
        "athlete_ids": [athlete1_id],
        "created_at": now,
    })
    # Cancelled session (must be excluded from attendance calculation)
    await db.training_sessions.insert_one({
        "title": "Rain Cancelled",
        "sport_id": football_id,
        "coach_id": coach1_id,
        "session_date": now - timedelta(days=2),
        "status": "cancelled",
        "athlete_ids": [athlete1_id],
        "created_at": now,
    })

    # Attendance records: 1 Present, 1 Late, 1 Absent
    await db.attendance.insert_many([
        {"session_id": sess1.inserted_id, "athlete_id": athlete1_id, "status": "present", "created_at": now},
        {"session_id": sess2.inserted_id, "athlete_id": athlete1_id, "status": "late", "created_at": now},
        {"session_id": sess3.inserted_id, "athlete_id": athlete1_id, "status": "absent", "created_at": now},
    ])

    return {
        "football_id": str(football_id),
        "cricket_id": str(cricket_id),
        "coach1_id": str(coach1_id),
        "coach2_id": str(coach2_id),
        "athlete1_id": str(athlete1_id),
        "athlete2_id": str(athlete2_id),
    }


# ── The 25 Tests ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_1_athlete_can_access_own_analytics(client, db, admin_user, coach_user, athlete_user, athlete_token):
    """1. Athlete can access own analytics"""
    fix = await _setup_analytics_fixture(db, admin_user, coach_user, athlete_user)
    resp = await client.get("/api/v1/analytics/athlete/me", headers=auth_headers(athlete_token))
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["athlete_id"] == fix["athlete1_id"]
    assert data["athlete_name"] == athlete_user["full_name"]


@pytest.mark.asyncio
async def test_2_athlete_cannot_access_another_athlete_analytics(client, db, admin_user, coach_user, athlete_user, athlete_token):
    """2. Athlete cannot access another athlete's analytics (403 Forbidden)"""
    fix = await _setup_analytics_fixture(db, admin_user, coach_user, athlete_user)
    resp = await client.get(f"/api/v1/analytics/athlete/{fix['athlete2_id']}", headers=auth_headers(athlete_token))
    assert resp.status_code == 403
    assert "own analytics" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_3_athlete_cannot_access_coach_analytics(client, db, admin_user, coach_user, athlete_user, athlete_token):
    """3. Athlete cannot access coach analytics (403 Forbidden)"""
    await _setup_analytics_fixture(db, admin_user, coach_user, athlete_user)
    resp = await client.get("/api/v1/analytics/coach/summary", headers=auth_headers(athlete_token))
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_4_athlete_cannot_access_admin_analytics(client, db, admin_user, coach_user, athlete_user, athlete_token):
    """4. Athlete cannot access admin analytics (403 Forbidden)"""
    await _setup_analytics_fixture(db, admin_user, coach_user, athlete_user)
    resp = await client.get("/api/v1/analytics/admin/summary", headers=auth_headers(athlete_token))
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_5_coach_can_access_assigned_athlete_analytics(client, db, admin_user, coach_user, athlete_user, coach_token):
    """5. Coach can access assigned athlete analytics"""
    fix = await _setup_analytics_fixture(db, admin_user, coach_user, athlete_user)
    resp = await client.get(f"/api/v1/analytics/coach/athletes/{fix['athlete1_id']}", headers=auth_headers(coach_token))
    assert resp.status_code == 200, resp.text
    assert resp.json()["athlete_id"] == fix["athlete1_id"]


@pytest.mark.asyncio
async def test_6_coach_cannot_access_unassigned_athlete_analytics(client, db, admin_user, coach_user, athlete_user, coach_token):
    """6. Coach cannot access unassigned athlete analytics (403 Forbidden)"""
    fix = await _setup_analytics_fixture(db, admin_user, coach_user, athlete_user)
    resp = await client.get(f"/api/v1/analytics/coach/athletes/{fix['athlete2_id']}", headers=auth_headers(coach_token))
    assert resp.status_code == 403
    assert "assigned athletes" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_7_coach_summary_only_includes_assigned_athletes(client, db, admin_user, coach_user, athlete_user, coach_token):
    """7. Coach summary only includes assigned athletes"""
    await _setup_analytics_fixture(db, admin_user, coach_user, athlete_user)
    resp = await client.get("/api/v1/analytics/coach/summary", headers=auth_headers(coach_token))
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["total_assigned_athletes"] == 1
    assert data["average_performance"] == 84.0


@pytest.mark.asyncio
async def test_8_admin_can_access_academy_analytics(client, db, admin_user, coach_user, athlete_user, admin_token):
    """8. Admin can access academy analytics"""
    await _setup_analytics_fixture(db, admin_user, coach_user, athlete_user)
    resp = await client.get("/api/v1/analytics/admin/summary", headers=auth_headers(admin_token))
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["total_athletes"] == 2
    assert data["total_coaches"] == 2
    assert data["total_active_sports"] == 2
    assert data["total_assessments"] == 3


@pytest.mark.asyncio
async def test_9_admin_can_access_all_athlete_analytics(client, db, admin_user, coach_user, athlete_user, admin_token):
    """9. Admin can access all athlete analytics"""
    fix = await _setup_analytics_fixture(db, admin_user, coach_user, athlete_user)
    resp1 = await client.get(f"/api/v1/analytics/athlete/{fix['athlete1_id']}", headers=auth_headers(admin_token))
    assert resp1.status_code == 200
    resp2 = await client.get(f"/api/v1/analytics/athlete/{fix['athlete2_id']}", headers=auth_headers(admin_token))
    assert resp2.status_code == 200


@pytest.mark.asyncio
async def test_10_current_performance_calculated_correctly(client, db, admin_user, coach_user, athlete_user, athlete_token):
    """10. Current performance is calculated correctly from latest completed assessment"""
    await _setup_analytics_fixture(db, admin_user, coach_user, athlete_user)
    resp = await client.get("/api/v1/analytics/athlete/me", headers=auth_headers(athlete_token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["current_performance"]["score"] == 84.0


@pytest.mark.asyncio
async def test_11_previous_performance_calculated_correctly(client, db, admin_user, coach_user, athlete_user, athlete_token):
    """11. Previous performance is calculated correctly from immediately previous assessment"""
    await _setup_analytics_fixture(db, admin_user, coach_user, athlete_user)
    resp = await client.get("/api/v1/analytics/athlete/me", headers=auth_headers(athlete_token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["previous_performance"]["score"] == 77.0


def test_12_improvement_percentage_calculated_correctly():
    """12. Improvement percentage is calculated correctly: ((curr - prev) / prev) * 100"""
    # 77 to 84 = 9.09%
    assert calculate_improvement(84.0, 77.0) == 9.09
    # 80 to 70 = -12.5%
    assert calculate_improvement(70.0, 80.0) == -12.5


def test_13_zero_previous_score_handled_safely():
    """13. Zero previous score is handled safely"""
    assert calculate_improvement(80.0, 0) is None
    assert calculate_improvement(80.0, -10.0) is None


def test_14_insufficient_history_handled_correctly():
    """14. Insufficient history handled correctly"""
    assert calculate_improvement(80.0, None) is None
    assert calculate_trend(80.0, None) == "Insufficient Data"


def test_15_trend_calculation_works():
    """15. Trend calculation works (Improving, Declining, Stable, Insufficient Data)"""
    assert calculate_trend(85.0, 80.0) == "Improving"
    assert calculate_trend(75.0, 80.0) == "Declining"
    assert calculate_trend(80.0, 80.0) == "Stable"
    assert calculate_trend(None, 80.0) == "Insufficient Data"


def test_16_strongest_metric_is_correct():
    """16. Strongest metric is correct from latest assessment metrics"""
    metrics = {"speed": 82.0, "passing": 79.0, "shooting": 91.0}
    res = identify_strongest_metric(metrics)
    assert res["name"] == "shooting"
    assert res["score"] == 91.0


def test_17_weakest_metric_is_correct():
    """17. Weakest metric is correct from latest assessment metrics"""
    metrics = {"speed": 82.0, "passing": 79.0, "shooting": 91.0}
    res = identify_weakest_metric(metrics)
    assert res["name"] == "passing"
    assert res["score"] == 79.0


@pytest.mark.asyncio
async def test_18_attendance_percentage_phase3_logic(client, db, admin_user, coach_user, athlete_user, athlete_token):
    """18. Attendance percentage uses existing Phase 3 logic: (Present + Late) / Total Applicable * 100"""
    await _setup_analytics_fixture(db, admin_user, coach_user, athlete_user)
    resp = await client.get("/api/v1/analytics/athlete/me", headers=auth_headers(athlete_token))
    assert resp.status_code == 200
    att = resp.json()["attendance"]
    # 1 present + 1 late out of 3 applicable sessions = 66.7%
    assert att["attended_sessions"] == 2
    assert att["total_sessions"] == 3
    assert att["percentage"] == 66.7


@pytest.mark.asyncio
async def test_19_cancelled_sessions_are_excluded(client, db, admin_user, coach_user, athlete_user, athlete_token):
    """19. Cancelled sessions are excluded from total applicable sessions count"""
    await _setup_analytics_fixture(db, admin_user, coach_user, athlete_user)
    resp = await client.get("/api/v1/analytics/athlete/me", headers=auth_headers(athlete_token))
    assert resp.status_code == 200
    att = resp.json()["attendance"]
    # 4 sessions created in fixture, 1 is cancelled -> total applicable is 3
    assert att["total_sessions"] == 3


@pytest.mark.asyncio
async def test_20_attendance_warning_below_75_percent(client, db, admin_user, coach_user, athlete_user, athlete_token):
    """20. Attendance warning is true below 75%"""
    await _setup_analytics_fixture(db, admin_user, coach_user, athlete_user)
    resp = await client.get("/api/v1/analytics/athlete/me", headers=auth_headers(athlete_token))
    assert resp.status_code == 200
    att = resp.json()["attendance"]
    assert att["warning"] is True


@pytest.mark.asyncio
async def test_21_no_attendance_data_handled_correctly(client, db, admin_user, coach_user, athlete_user, admin_token):
    """21. No attendance data is handled correctly (percentage is None, not fake 0%)"""
    fix = await _setup_analytics_fixture(db, admin_user, coach_user, athlete_user)
    resp = await client.get(f"/api/v1/analytics/athlete/{fix['athlete2_id']}", headers=auth_headers(admin_token))
    assert resp.status_code == 200
    att = resp.json()["attendance"]
    assert att["total_sessions"] == 0
    assert att["percentage"] is None
    assert att["warning"] is False


@pytest.mark.asyncio
async def test_22_no_assessment_data_handled_correctly(client, db, admin_user, coach_user, athlete_user, admin_token):
    """22. No assessment data is handled correctly"""
    fix = await _setup_analytics_fixture(db, admin_user, coach_user, athlete_user)
    resp = await client.get(f"/api/v1/analytics/athlete/{fix['athlete2_id']}", headers=auth_headers(admin_token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["current_performance"] is None
    assert data["previous_performance"] is None
    assert data["improvement_percentage"] is None
    assert data["trend"] == "Insufficient Data"
    assert data["assessment_history"] == []


@pytest.mark.asyncio
async def test_23_multiple_assessment_history_sorted_correctly(client, db, admin_user, coach_user, athlete_user, athlete_token):
    """23. Multiple assessment history is sorted correctly chronologically descending"""
    await _setup_analytics_fixture(db, admin_user, coach_user, athlete_user)
    resp = await client.get("/api/v1/analytics/athlete/me", headers=auth_headers(athlete_token))
    assert resp.status_code == 200
    history = resp.json()["assessment_history"]
    assert len(history) == 3
    assert history[0]["overall_score"] == 84.0
    assert history[1]["overall_score"] == 77.0
    assert history[2]["overall_score"] == 70.0


@pytest.mark.asyncio
async def test_24_sport_filtering_works(client, db, admin_user, coach_user, athlete_user, admin_token, coach_token):
    """24. Sport filtering works for admin sports breakdown and coach athletes filter"""
    fix = await _setup_analytics_fixture(db, admin_user, coach_user, athlete_user)

    # Admin sports endpoint
    resp_adm = await client.get("/api/v1/analytics/admin/sports", headers=auth_headers(admin_token))
    assert resp_adm.status_code == 200
    sports = resp_adm.json()["sports"]
    football = next(s for s in sports if s["sport_name"] == "Football")
    assert football["athlete_count"] == 1
    assert football["assessment_count"] == 3

    # Coach filter by sport
    resp_c = await client.get(
        f"/api/v1/analytics/coach/athletes?sport_id={fix['football_id']}",
        headers=auth_headers(coach_token),
    )
    assert resp_c.status_code == 200
    assert len(resp_c.json()) == 1


@pytest.mark.asyncio
async def test_25_unauthenticated_analytics_request_returns_401(client, db, admin_user, coach_user, athlete_user):
    """25. Unauthenticated analytics request returns 401"""
    fix = await _setup_analytics_fixture(db, admin_user, coach_user, athlete_user)
    assert (await client.get("/api/v1/analytics/athlete/me")).status_code == 401
    assert (await client.get(f"/api/v1/analytics/athlete/{fix['athlete1_id']}")).status_code == 401
    assert (await client.get("/api/v1/analytics/coach/summary")).status_code == 401
    assert (await client.get("/api/v1/analytics/admin/summary")).status_code == 401
