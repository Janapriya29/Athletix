"""
Reports tests — Phase 7.
Covers:
1. Athlete can access own performance report
2. Athlete cannot access another athlete's performance report (403)
3. Coach can access assigned athlete's performance report
4. Coach cannot access unassigned athlete's performance report (403)
5. Admin can access any athlete's performance report
6. Athlete can access own attendance report
7. Athlete attendance report correctly calculates percentages and warning (<75%)
8. Athlete attendance report excludes cancelled sessions
9. Athlete can access own tournaments report with medals and points tally
10. Athlete can access own development summary report
11. Admin can access academy summary report
12. Coach/Athlete cannot access academy summary report (403)
13. Academy attendance report returns list of athletes with stats
14. Academy attendance report supports CSV format export (format=csv)
15. Academy tournaments report returns tournament records with medalists
16. Academy tournaments report supports CSV format export (format=csv)
17. Unauthenticated report requests return 401
"""
from datetime import datetime, timezone
import pytest
from bson import ObjectId


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── Fixtures Setup ─────────────────────────────────────────────────────────────

async def _setup_report_fixtures(db, admin_user, coach_user, athlete_user):
    now = datetime.now(timezone.utc)

    # 1. Sport
    s_res = await db.sports.insert_one({"name": "Football", "is_active": True, "created_at": now})
    sport_id = s_res.inserted_id

    # 2. Coach
    c_res = await db.coaches.insert_one({
        "user_id": coach_user["_id"],
        "full_name": coach_user["full_name"],
        "email": coach_user["email"],
        "sport_ids": [sport_id],
        "status": "active",
        "created_at": now,
    })
    coach_id = c_res.inserted_id

    # 3. Assigned Athlete
    a_res = await db.athletes.insert_one({
        "user_id": athlete_user["_id"],
        "full_name": athlete_user["full_name"],
        "email": athlete_user["email"],
        "sport_id": sport_id,
        "coach_id": coach_id,
        "status": "active",
        "created_at": now,
    })
    athlete_id = a_res.inserted_id

    await db.coach_athlete_assignments.insert_one({
        "coach_id": coach_id,
        "athlete_id": athlete_id,
        "status": "active",
        "created_at": now,
    })

    # 4. Another unassigned athlete
    other_u_res = await db.users.insert_one({
        "email": "other_ath@test.com",
        "hashed_password": "dummy",
        "role": "athlete",
        "full_name": "Other Athlete",
        "is_active": True,
        "created_at": now,
    })
    other_user_id = other_u_res.inserted_id
    other_a_res = await db.athletes.insert_one({
        "user_id": other_user_id,
        "full_name": "Other Athlete",
        "email": "other_ath@test.com",
        "sport_id": sport_id,
        "coach_id": None,
        "status": "active",
        "created_at": now,
    })
    other_athlete_id = other_a_res.inserted_id

    # Seed assessments for athlete
    await db.performance_assessments.insert_one({
        "athlete_id": athlete_id,
        "date": datetime(2026, 10, 1, 10, 0),
        "overall_score": 70.0,
        "metrics": {"speed": 70.0, "stamina": 70.0},
    })
    await db.performance_assessments.insert_one({
        "athlete_id": athlete_id,
        "date": datetime(2026, 10, 5, 10, 0),
        "overall_score": 84.0,
        "metrics": {"speed": 90.0, "stamina": 78.0},
    })

    # Seed training sessions & attendance
    s1 = await db.training_sessions.insert_one({
        "title": "S1",
        "sport_id": sport_id,
        "coach_id": coach_id,
        "session_date": datetime(2026, 10, 2, 9, 0),
        "athlete_ids": [athlete_id],
        "status": "completed",
    })
    s2 = await db.training_sessions.insert_one({
        "title": "S2",
        "sport_id": sport_id,
        "coach_id": coach_id,
        "session_date": datetime(2026, 10, 3, 9, 0),
        "athlete_ids": [athlete_id],
        "status": "completed",
    })
    s_cancelled = await db.training_sessions.insert_one({
        "title": "S Cancelled",
        "sport_id": sport_id,
        "coach_id": coach_id,
        "session_date": datetime(2026, 10, 4, 9, 0),
        "athlete_ids": [athlete_id],
        "status": "cancelled",
    })

    await db.attendance.insert_one({
        "session_id": s1.inserted_id,
        "athlete_id": athlete_id,
        "status": "present",
    })
    await db.attendance.insert_one({
        "session_id": s2.inserted_id,
        "athlete_id": athlete_id,
        "status": "absent",
    })

    # Seed tournament & participant
    t_res = await db.tournaments.insert_one({
        "name": "State Trophy 2026",
        "sport_id": sport_id,
        "status": "completed",
        "start_date": datetime(2026, 10, 1, 9, 0),
        "end_date": datetime(2026, 10, 3, 18, 0),
    })
    await db.tournament_participants.insert_one({
        "tournament_id": t_res.inserted_id,
        "athlete_id": athlete_id,
        "event": "Football 7s",
        "position": 1,
        "medal": "Gold",
        "points": 25.0,
        "status": "participated",
    })

    return {
        "sport_id": sport_id,
        "coach_id": coach_id,
        "athlete_id": athlete_id,
        "other_athlete_id": other_athlete_id,
        "tournament_id": t_res.inserted_id,
    }


# ── Tests ──────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_athlete_can_access_own_performance_report(
    client, db, admin_user, coach_user, athlete_user, athlete_token
):
    fx = await _setup_report_fixtures(db, admin_user, coach_user, athlete_user)
    resp = await client.get(
        f"/api/v1/reports/athlete/{str(fx['athlete_id'])}/performance",
        headers=auth_headers(athlete_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["athlete_name"] == athlete_user["full_name"]
    assert data["current_score"] == 84.0
    assert data["previous_score"] == 70.0
    assert data["improvement_pct"] == 20.0
    assert data["trend"] == "Improving"
    assert data["strongest_metric"] == "speed"
    assert data["total_assessments"] == 2


@pytest.mark.asyncio
async def test_athlete_cannot_access_other_performance_report(
    client, db, admin_user, coach_user, athlete_user, athlete_token
):
    fx = await _setup_report_fixtures(db, admin_user, coach_user, athlete_user)
    resp = await client.get(
        f"/api/v1/reports/athlete/{str(fx['other_athlete_id'])}/performance",
        headers=auth_headers(athlete_token),
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_coach_can_access_assigned_athlete_performance_report(
    client, db, admin_user, coach_user, athlete_user, coach_token
):
    fx = await _setup_report_fixtures(db, admin_user, coach_user, athlete_user)
    resp = await client.get(
        f"/api/v1/reports/athlete/{str(fx['athlete_id'])}/performance",
        headers=auth_headers(coach_token),
    )
    assert resp.status_code == 200
    assert resp.json()["current_score"] == 84.0


@pytest.mark.asyncio
async def test_coach_cannot_access_unassigned_athlete_performance_report(
    client, db, admin_user, coach_user, athlete_user, coach_token
):
    fx = await _setup_report_fixtures(db, admin_user, coach_user, athlete_user)
    resp = await client.get(
        f"/api/v1/reports/athlete/{str(fx['other_athlete_id'])}/performance",
        headers=auth_headers(coach_token),
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_access_any_athlete_performance_report(
    client, db, admin_user, coach_user, athlete_user, admin_token
):
    fx = await _setup_report_fixtures(db, admin_user, coach_user, athlete_user)
    resp = await client.get(
        f"/api/v1/reports/athlete/{str(fx['other_athlete_id'])}/performance",
        headers=auth_headers(admin_token),
    )
    assert resp.status_code == 200
    assert resp.json()["athlete_name"] == "Other Athlete"


@pytest.mark.asyncio
async def test_athlete_can_access_own_attendance_report(
    client, db, admin_user, coach_user, athlete_user, athlete_token
):
    fx = await _setup_report_fixtures(db, admin_user, coach_user, athlete_user)
    resp = await client.get(
        f"/api/v1/reports/athlete/{str(fx['athlete_id'])}/attendance",
        headers=auth_headers(athlete_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_sessions"] == 2  # excludes cancelled
    assert data["attended_sessions"] == 1
    assert data["present_count"] == 1
    assert data["absent_count"] == 1
    assert data["attendance_percentage"] == 50.0
    assert data["warning"] is True  # 50% < 75%


@pytest.mark.asyncio
async def test_attendance_report_excludes_cancelled_sessions(
    client, db, admin_user, coach_user, athlete_user, athlete_token
):
    fx = await _setup_report_fixtures(db, admin_user, coach_user, athlete_user)
    resp = await client.get(
        f"/api/v1/reports/athlete/{str(fx['athlete_id'])}/attendance",
        headers=auth_headers(athlete_token),
    )
    assert resp.status_code == 200
    # S_cancelled is not counted in total_sessions
    assert resp.json()["total_sessions"] == 2


@pytest.mark.asyncio
async def test_athlete_can_access_own_tournaments_report(
    client, db, admin_user, coach_user, athlete_user, athlete_token
):
    fx = await _setup_report_fixtures(db, admin_user, coach_user, athlete_user)
    resp = await client.get(
        f"/api/v1/reports/athlete/{str(fx['athlete_id'])}/tournaments",
        headers=auth_headers(athlete_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_tournaments"] == 1
    assert data["total_points"] == 25.0
    assert data["medals_summary"]["gold"] == 1
    assert data["medals_summary"]["total"] == 1
    assert len(data["history"]) == 1
    assert data["history"][0]["tournament_name"] == "State Trophy 2026"


@pytest.mark.asyncio
async def test_athlete_can_access_own_development_summary(
    client, db, admin_user, coach_user, athlete_user, athlete_token
):
    fx = await _setup_report_fixtures(db, admin_user, coach_user, athlete_user)
    resp = await client.get(
        f"/api/v1/reports/athlete/{str(fx['athlete_id'])}/development",
        headers=auth_headers(athlete_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["athlete_name"] == athlete_user["full_name"]
    assert data["attendance_summary"]["attendance_percentage"] == 50.0
    assert data["performance_summary"]["current_score"] == 84.0
    assert data["tournaments_summary"]["total_points"] == 25.0


@pytest.mark.asyncio
async def test_admin_can_access_academy_summary(
    client, db, admin_user, coach_user, athlete_user, admin_token
):
    await _setup_report_fixtures(db, admin_user, coach_user, athlete_user)
    resp = await client.get("/api/v1/reports/academy/summary", headers=auth_headers(admin_token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_athletes"] == 2
    assert data["total_coaches"] == 1
    assert data["total_sports"] == 1
    assert data["total_assessments"] == 2
    assert data["total_tournaments"] == 1
    assert data["total_medals_awarded"] == 1


@pytest.mark.asyncio
async def test_coach_and_athlete_cannot_access_academy_summary(
    client, db, admin_user, coach_user, athlete_user, coach_token, athlete_token
):
    await _setup_report_fixtures(db, admin_user, coach_user, athlete_user)
    resp_coach = await client.get("/api/v1/reports/academy/summary", headers=auth_headers(coach_token))
    assert resp_coach.status_code == 403

    resp_ath = await client.get("/api/v1/reports/academy/summary", headers=auth_headers(athlete_token))
    assert resp_ath.status_code == 403


@pytest.mark.asyncio
async def test_academy_attendance_report_json(
    client, db, admin_user, coach_user, athlete_user, admin_token
):
    await _setup_report_fixtures(db, admin_user, coach_user, athlete_user)
    resp = await client.get("/api/v1/reports/attendance", headers=auth_headers(admin_token))
    assert resp.status_code == 200
    items = resp.json()
    assert isinstance(items, list)
    assert len(items) >= 1
    ath_item = next((i for i in items if i["athlete_name"] == athlete_user["full_name"]), None)
    assert ath_item is not None
    assert ath_item["total_sessions"] == 2
    assert ath_item["attendance_percentage"] == 50.0


@pytest.mark.asyncio
async def test_academy_attendance_report_csv_export(
    client, db, admin_user, coach_user, athlete_user, admin_token
):
    await _setup_report_fixtures(db, admin_user, coach_user, athlete_user)
    resp = await client.get("/api/v1/reports/attendance?format=csv", headers=auth_headers(admin_token))
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    text = resp.text
    assert "Athlete Name" in text
    assert athlete_user["full_name"] in text
    assert "50.0%" in text


@pytest.mark.asyncio
async def test_academy_tournaments_report_json(
    client, db, admin_user, coach_user, athlete_user, admin_token
):
    await _setup_report_fixtures(db, admin_user, coach_user, athlete_user)
    resp = await client.get("/api/v1/reports/tournaments", headers=auth_headers(admin_token))
    assert resp.status_code == 200
    items = resp.json()
    assert isinstance(items, list)
    assert len(items) == 1
    assert items[0]["tournament_name"] == "State Trophy 2026"
    assert items[0]["gold_medalist"] == athlete_user["full_name"]


@pytest.mark.asyncio
async def test_academy_tournaments_report_csv_export(
    client, db, admin_user, coach_user, athlete_user, admin_token
):
    await _setup_report_fixtures(db, admin_user, coach_user, athlete_user)
    resp = await client.get("/api/v1/reports/tournaments?format=csv", headers=auth_headers(admin_token))
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    text = resp.text
    assert "Tournament Name" in text
    assert "State Trophy 2026" in text
    assert athlete_user["full_name"] in text


@pytest.mark.asyncio
async def test_unauthenticated_reports_request_fails(client):
    resp = await client.get("/api/v1/reports/academy/summary")
    assert resp.status_code == 401
