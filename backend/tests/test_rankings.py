"""
Rankings Tests — Phase 6.
Covers Minimum ranking tests (21-32):
21. Tournament ranking calculates correctly
22. Points ranking order is correct
23. Medal counts are correct
24. Performance ranking uses real Phase 5 scores
25. Attendance ranking uses Phase 3 formula
26. Cancelled sessions excluded from attendance ranking
27. Improvement ranking uses Phase 5 improvement values
28. Insufficient performance history is handled
29. Sport filtering works
30. Tie ordering is deterministic
31. Unauthenticated ranking request rejected where appropriate
32. Role restrictions work
"""
from datetime import datetime, timedelta, timezone
from bson import ObjectId
import pytest


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── Fixture Helper ─────────────────────────────────────────────────────────────

async def _setup_rankings_test_data(db, admin_user, coach_user, athlete_user):
    now = datetime.now(timezone.utc)

    # 1. Sports
    s_fb = await db.sports.insert_one({"name": "Football", "is_active": True, "created_at": now})
    football_id = s_fb.inserted_id

    s_bd = await db.sports.insert_one({"name": "Badminton", "is_active": True, "created_at": now})
    badminton_id = s_bd.inserted_id

    # 2. Coach
    coach_profile = await db.coaches.insert_one({
        "user_id": coach_user["_id"],
        "full_name": coach_user["full_name"],
        "email": coach_user["email"],
        "status": "active",
        "sport_ids": [football_id, badminton_id],
        "created_at": now,
    })
    coach_id = coach_profile.inserted_id

    # 3. Athletes
    # Athlete A (Football)
    ath_a = await db.athletes.insert_one({
        "user_id": athlete_user["_id"],
        "full_name": "Athlete Alpha",
        "email": athlete_user["email"],
        "status": "active",
        "sport_id": football_id,
        "coach_id": coach_id,
        "created_at": now,
    })

    # Athlete B (Football)
    u_b = await db.users.insert_one({
        "email": "beta@test.com",
        "role": "athlete",
        "full_name": "Athlete Beta",
        "is_active": True,
        "created_at": now,
    })
    ath_b = await db.athletes.insert_one({
        "user_id": u_b.inserted_id,
        "full_name": "Athlete Beta",
        "email": "beta@test.com",
        "status": "active",
        "sport_id": football_id,
        "coach_id": coach_id,
        "created_at": now,
    })

    # Athlete C (Badminton)
    u_c = await db.users.insert_one({
        "email": "gamma@test.com",
        "role": "athlete",
        "full_name": "Athlete Gamma",
        "is_active": True,
        "created_at": now,
    })
    ath_c = await db.athletes.insert_one({
        "user_id": u_c.inserted_id,
        "full_name": "Athlete Gamma",
        "email": "gamma@test.com",
        "status": "active",
        "sport_id": badminton_id,
        "coach_id": coach_id,
        "created_at": now,
    })

    return {
        "football_id": str(football_id),
        "badminton_id": str(badminton_id),
        "athlete_a_id": str(ath_a.inserted_id),
        "athlete_b_id": str(ath_b.inserted_id),
        "athlete_c_id": str(ath_c.inserted_id),
    }


# ── 21. Tournament ranking calculates correctly ────────────────────────────────

@pytest.mark.asyncio
async def test_21_tournament_ranking_calculates_correctly(client, admin_token, db, admin_user, coach_user, athlete_user):
    data = await _setup_rankings_test_data(db, admin_user, coach_user, athlete_user)
    now = datetime.now(timezone.utc)

    # Insert a tournament and participant results
    t_res = await db.tournaments.insert_one({
        "name": "State Cup",
        "sport_id": ObjectId(data["football_id"]),
        "start_date": now,
        "end_date": now + timedelta(days=2),
        "status": "completed",
        "created_at": now,
    })

    await db.tournament_participants.insert_one({
        "tournament_id": t_res.inserted_id,
        "athlete_id": ObjectId(data["athlete_a_id"]),
        "position": 1,
        "medal": "Gold",
        "points": 10.0,
        "status": "participated",
        "created_at": now,
    })

    res = await client.get("/api/v1/rankings/tournament", headers=auth_headers(admin_token))
    assert res.status_code == 200
    items = res.json()
    assert len(items) >= 1
    first = items[0]
    assert first["athlete_id"] == data["athlete_a_id"]
    assert first["athlete_name"] == "Athlete Alpha"
    assert first["points"] == 10.0
    assert first["gold_count"] == 1
    assert first["total_medals"] == 1
    assert first["tournaments_played"] == 1
    assert first["rank"] == 1


# ── 22. Points ranking order is correct ────────────────────────────────────────

@pytest.mark.asyncio
async def test_22_points_ranking_order_is_correct(client, admin_token, db, admin_user, coach_user, athlete_user):
    data = await _setup_rankings_test_data(db, admin_user, coach_user, athlete_user)
    now = datetime.now(timezone.utc)

    t1 = await db.tournaments.insert_one({
        "name": "Cup 1",
        "sport_id": ObjectId(data["football_id"]),
        "start_date": now,
        "end_date": now + timedelta(days=2),
        "status": "completed",
    })

    # Athlete B gets 20 points, Athlete A gets 10 points
    await db.tournament_participants.insert_many([
        {"tournament_id": t1.inserted_id, "athlete_id": ObjectId(data["athlete_b_id"]), "points": 20.0, "position": 1, "medal": "Gold"},
        {"tournament_id": t1.inserted_id, "athlete_id": ObjectId(data["athlete_a_id"]), "points": 10.0, "position": 2, "medal": "Silver"},
    ])

    res = await client.get("/api/v1/rankings/tournament", headers=auth_headers(admin_token))
    assert res.status_code == 200
    items = res.json()
    assert len(items) == 2
    assert items[0]["athlete_id"] == data["athlete_b_id"]
    assert items[0]["rank"] == 1
    assert items[0]["points"] == 20.0
    assert items[1]["athlete_id"] == data["athlete_a_id"]
    assert items[1]["rank"] == 2
    assert items[1]["points"] == 10.0


# ── 23. Medal counts are correct ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_23_medal_counts_are_correct(client, admin_token, db, admin_user, coach_user, athlete_user):
    data = await _setup_rankings_test_data(db, admin_user, coach_user, athlete_user)
    now = datetime.now(timezone.utc)

    t1 = await db.tournaments.insert_one({"name": "Cup 1", "sport_id": ObjectId(data["football_id"]), "start_date": now, "end_date": now})
    t2 = await db.tournaments.insert_one({"name": "Cup 2", "sport_id": ObjectId(data["football_id"]), "start_date": now, "end_date": now})
    t3 = await db.tournaments.insert_one({"name": "Cup 3", "sport_id": ObjectId(data["football_id"]), "start_date": now, "end_date": now})

    # Athlete A: 2 Gold, 1 Silver
    await db.tournament_participants.insert_many([
        {"tournament_id": t1.inserted_id, "athlete_id": ObjectId(data["athlete_a_id"]), "points": 10.0, "position": 1, "medal": "Gold"},
        {"tournament_id": t2.inserted_id, "athlete_id": ObjectId(data["athlete_a_id"]), "points": 10.0, "position": 1, "medal": "Gold"},
        {"tournament_id": t3.inserted_id, "athlete_id": ObjectId(data["athlete_a_id"]), "points": 5.0, "position": 2, "medal": "Silver"},
    ])

    res = await client.get("/api/v1/rankings/tournament", headers=auth_headers(admin_token))
    assert res.status_code == 200
    items = res.json()
    a_stat = next(i for i in items if i["athlete_id"] == data["athlete_a_id"])
    assert a_stat["gold_count"] == 2
    assert a_stat["silver_count"] == 1
    assert a_stat["bronze_count"] == 0
    assert a_stat["total_medals"] == 3


# ── 24. Performance ranking uses real Phase 5 scores ───────────────────────────

@pytest.mark.asyncio
async def test_24_performance_ranking_uses_real_scores(client, admin_token, db, admin_user, coach_user, athlete_user):
    data = await _setup_rankings_test_data(db, admin_user, coach_user, athlete_user)
    now = datetime.now(timezone.utc)

    # Athlete A score 92.5, Athlete B score 78.0
    await db.performance_assessments.insert_many([
        {"athlete_id": ObjectId(data["athlete_a_id"]), "overall_score": 92.5, "date": now},
        {"athlete_id": ObjectId(data["athlete_b_id"]), "overall_score": 78.0, "date": now},
    ])

    res = await client.get("/api/v1/rankings/performance", headers=auth_headers(admin_token))
    assert res.status_code == 200
    items = res.json()
    assert len(items) >= 2
    assert items[0]["athlete_id"] == data["athlete_a_id"]
    assert items[0]["performance_score"] == 92.5
    assert items[0]["rank"] == 1
    assert items[1]["athlete_id"] == data["athlete_b_id"]
    assert items[1]["performance_score"] == 78.0
    assert items[1]["rank"] == 2


# ── 25. Attendance ranking uses Phase 3 formula ────────────────────────────────

@pytest.mark.asyncio
async def test_25_attendance_ranking_uses_phase3_formula(client, admin_token, db, admin_user, coach_user, athlete_user):
    data = await _setup_rankings_test_data(db, admin_user, coach_user, athlete_user)
    now = datetime.now(timezone.utc)

    # 2 training sessions attended by Athlete A and B
    s1 = await db.training_sessions.insert_one({
        "sport_id": ObjectId(data["football_id"]),
        "status": "completed",
        "athlete_ids": [ObjectId(data["athlete_a_id"]), ObjectId(data["athlete_b_id"])],
        "session_date": now - timedelta(days=2),
    })
    s2 = await db.training_sessions.insert_one({
        "sport_id": ObjectId(data["football_id"]),
        "status": "completed",
        "athlete_ids": [ObjectId(data["athlete_a_id"]), ObjectId(data["athlete_b_id"])],
        "session_date": now - timedelta(days=1),
    })

    # Athlete A: 1 Present, 1 Late -> (1+1)/2 = 100.0%
    # Athlete B: 1 Present, 1 Absent -> 1/2 = 50.0%
    await db.attendance.insert_many([
        {"session_id": s1.inserted_id, "athlete_id": ObjectId(data["athlete_a_id"]), "status": "present"},
        {"session_id": s2.inserted_id, "athlete_id": ObjectId(data["athlete_a_id"]), "status": "late"},
        {"session_id": s1.inserted_id, "athlete_id": ObjectId(data["athlete_b_id"]), "status": "present"},
        {"session_id": s2.inserted_id, "athlete_id": ObjectId(data["athlete_b_id"]), "status": "absent"},
    ])

    res = await client.get("/api/v1/rankings/attendance", headers=auth_headers(admin_token))
    assert res.status_code == 200
    items = res.json()
    assert len(items) >= 2
    assert items[0]["athlete_id"] == data["athlete_a_id"]
    assert items[0]["attendance_percentage"] == 100.0
    assert items[1]["athlete_id"] == data["athlete_b_id"]
    assert items[1]["attendance_percentage"] == 50.0


# ── 26. Cancelled sessions excluded from attendance ranking ────────────────────

@pytest.mark.asyncio
async def test_26_cancelled_sessions_excluded_from_attendance_ranking(client, admin_token, db, admin_user, coach_user, athlete_user):
    data = await _setup_rankings_test_data(db, admin_user, coach_user, athlete_user)
    now = datetime.now(timezone.utc)

    # 1 completed session, 1 cancelled session
    s_comp = await db.training_sessions.insert_one({
        "sport_id": ObjectId(data["football_id"]),
        "status": "completed",
        "athlete_ids": [ObjectId(data["athlete_a_id"])],
        "session_date": now - timedelta(days=2),
    })
    await db.training_sessions.insert_one({
        "sport_id": ObjectId(data["football_id"]),
        "status": "cancelled",
        "athlete_ids": [ObjectId(data["athlete_a_id"])],
        "session_date": now - timedelta(days=1),
    })

    # Athlete A was present for the completed session
    await db.attendance.insert_one({
        "session_id": s_comp.inserted_id,
        "athlete_id": ObjectId(data["athlete_a_id"]),
        "status": "present",
    })

    res = await client.get("/api/v1/rankings/attendance", headers=auth_headers(admin_token))
    assert res.status_code == 200
    items = res.json()
    a_stat = next(i for i in items if i["athlete_id"] == data["athlete_a_id"])
    assert a_stat["total_sessions"] == 1  # Cancelled session excluded!
    assert a_stat["attendance_percentage"] == 100.0


# ── 27. Improvement ranking uses Phase 5 improvement values ────────────────────

@pytest.mark.asyncio
async def test_27_improvement_ranking_uses_phase5_improvement(client, admin_token, db, admin_user, coach_user, athlete_user):
    data = await _setup_rankings_test_data(db, admin_user, coach_user, athlete_user)
    now = datetime.now(timezone.utc)

    # Athlete A: 50 -> 75 => +50.0%
    # Athlete B: 50 -> 60 => +20.0%
    await db.performance_assessments.insert_many([
        {"athlete_id": ObjectId(data["athlete_a_id"]), "overall_score": 50.0, "date": now - timedelta(days=30)},
        {"athlete_id": ObjectId(data["athlete_a_id"]), "overall_score": 75.0, "date": now},
        {"athlete_id": ObjectId(data["athlete_b_id"]), "overall_score": 50.0, "date": now - timedelta(days=30)},
        {"athlete_id": ObjectId(data["athlete_b_id"]), "overall_score": 60.0, "date": now},
    ])

    res = await client.get("/api/v1/rankings/improvement", headers=auth_headers(admin_token))
    assert res.status_code == 200
    items = res.json()
    assert len(items) == 2
    assert items[0]["athlete_id"] == data["athlete_a_id"]
    assert items[0]["improvement_percentage"] == 50.0
    assert items[1]["athlete_id"] == data["athlete_b_id"]
    assert items[1]["improvement_percentage"] == 20.0


# ── 28. Insufficient performance history is handled ────────────────────────────

@pytest.mark.asyncio
async def test_28_insufficient_performance_history_handled(client, admin_token, db, admin_user, coach_user, athlete_user):
    data = await _setup_rankings_test_data(db, admin_user, coach_user, athlete_user)
    now = datetime.now(timezone.utc)

    # Athlete A has 2 assessments (eligible)
    await db.performance_assessments.insert_many([
        {"athlete_id": ObjectId(data["athlete_a_id"]), "overall_score": 50.0, "date": now - timedelta(days=30)},
        {"athlete_id": ObjectId(data["athlete_a_id"]), "overall_score": 60.0, "date": now},
    ])

    # Athlete C has only 1 assessment (insufficient)
    await db.performance_assessments.insert_one({
        "athlete_id": ObjectId(data["athlete_c_id"]),
        "overall_score": 90.0,
        "date": now,
    })

    res = await client.get("/api/v1/rankings/improvement", headers=auth_headers(admin_token))
    assert res.status_code == 200
    items = res.json()
    # Athlete C must NOT be in the improvement ranking
    assert all(i["athlete_id"] != data["athlete_c_id"] for i in items)
    assert any(i["athlete_id"] == data["athlete_a_id"] for i in items)


# ── 29. Sport filtering works ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_29_sport_filtering_works(client, admin_token, db, admin_user, coach_user, athlete_user):
    data = await _setup_rankings_test_data(db, admin_user, coach_user, athlete_user)
    now = datetime.now(timezone.utc)

    # Assessments: Athlete A (Football) and Athlete C (Badminton)
    await db.performance_assessments.insert_many([
        {"athlete_id": ObjectId(data["athlete_a_id"]), "overall_score": 85.0, "date": now},
        {"athlete_id": ObjectId(data["athlete_c_id"]), "overall_score": 95.0, "date": now},
    ])

    # 1. Filter by Football
    res_fb = await client.get(f"/api/v1/rankings/performance?sport_id={data['football_id']}", headers=auth_headers(admin_token))
    assert res_fb.status_code == 200
    fb_items = res_fb.json()
    assert len(fb_items) == 1
    assert fb_items[0]["athlete_id"] == data["athlete_a_id"]

    # 2. Filter by Badminton
    res_bd = await client.get(f"/api/v1/rankings/performance?sport_id={data['badminton_id']}", headers=auth_headers(admin_token))
    assert res_bd.status_code == 200
    bd_items = res_bd.json()
    assert len(bd_items) == 1
    assert bd_items[0]["athlete_id"] == data["athlete_c_id"]


# ── 30. Tie ordering is deterministic ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_30_tie_ordering_is_deterministic(client, admin_token, db, admin_user, coach_user, athlete_user):
    data = await _setup_rankings_test_data(db, admin_user, coach_user, athlete_user)
    now = datetime.now(timezone.utc)

    # Both Athlete Alpha and Athlete Beta have identical 10.0 points and 1 Gold medal
    t = await db.tournaments.insert_one({"name": "Tie Cup", "sport_id": ObjectId(data["football_id"]), "start_date": now, "end_date": now})
    await db.tournament_participants.insert_many([
        {"tournament_id": t.inserted_id, "athlete_id": ObjectId(data["athlete_b_id"]), "points": 10.0, "position": 1, "medal": "Gold"},
        {"tournament_id": t.inserted_id, "athlete_id": ObjectId(data["athlete_a_id"]), "points": 10.0, "position": 1, "medal": "Gold"},
    ])

    res = await client.get("/api/v1/rankings/tournament", headers=auth_headers(admin_token))
    assert res.status_code == 200
    items = res.json()
    assert len(items) == 2
    # Alphabetical tie break: "Athlete Alpha" before "Athlete Beta"
    assert items[0]["athlete_name"] == "Athlete Alpha"
    assert items[0]["rank"] == 1
    assert items[1]["athlete_name"] == "Athlete Beta"
    assert items[1]["rank"] == 2


# ── 31. Unauthenticated ranking request rejected ───────────────────────────────

@pytest.mark.asyncio
async def test_31_unauthenticated_ranking_request_rejected(client):
    res = await client.get("/api/v1/rankings")
    assert res.status_code == 401

    res_t = await client.get("/api/v1/rankings/tournament")
    assert res_t.status_code == 401


# ── 32. Role restrictions work ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_32_role_restrictions_work(client, coach_token, athlete_token, db, admin_user, coach_user, athlete_user):
    await _setup_rankings_test_data(db, admin_user, coach_user, athlete_user)

    # Coach can access rankings
    res_c = await client.get("/api/v1/rankings?type=tournament", headers=auth_headers(coach_token))
    assert res_c.status_code == 200
    assert res_c.json()["type"] == "tournament"

    # Athlete can access rankings
    res_a = await client.get("/api/v1/rankings?type=performance", headers=auth_headers(athlete_token))
    assert res_a.status_code == 200
    assert res_a.json()["type"] == "performance"
