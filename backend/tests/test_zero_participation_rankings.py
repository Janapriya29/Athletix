"""
Phase E Tests: Rankings and Zero-Participation Athlete Visibility.
Verifies that:
1. Eligible athletes with zero tournament participation or no assessments are represented appropriately.
2. No points, medals, or assessment scores are invented.
3. Legacy behavior (include_zero=False) remains preserved where requested.
4. Ties and missing data are handled deterministically.
5. Multi-sport eligible athletes are included under their relevant sports.
"""
from datetime import datetime, timedelta, timezone
from bson import ObjectId
import pytest


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _setup_phase_e_data(db, admin_user, coach_user, athlete_user):
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
    # Athlete Alpha (Football - Participating)
    ath_a = await db.athletes.insert_one({
        "user_id": athlete_user["_id"],
        "full_name": "Athlete Alpha",
        "email": athlete_user["email"],
        "status": "active",
        "sport_id": football_id,
        "coach_id": coach_id,
        "created_at": now,
    })

    # Athlete Beta (Football - Zero participation)
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

    # Athlete Charlie (Football - Zero participation, name for tie-breaker check)
    u_c = await db.users.insert_one({
        "email": "charlie@test.com",
        "role": "athlete",
        "full_name": "Athlete Charlie",
        "is_active": True,
        "created_at": now,
    })
    ath_c = await db.athletes.insert_one({
        "user_id": u_c.inserted_id,
        "full_name": "Athlete Charlie",
        "email": "charlie@test.com",
        "status": "active",
        "sport_id": football_id,
        "coach_id": coach_id,
        "created_at": now,
    })

    # Athlete Delta (Badminton primary, Football additional - Zero participation)
    u_d = await db.users.insert_one({
        "email": "delta@test.com",
        "role": "athlete",
        "full_name": "Athlete Delta",
        "is_active": True,
        "created_at": now,
    })
    ath_d = await db.athletes.insert_one({
        "user_id": u_d.inserted_id,
        "full_name": "Athlete Delta",
        "email": "delta@test.com",
        "status": "active",
        "sport_id": badminton_id,
        "additional_sport_ids": [football_id],
        "coach_id": coach_id,
        "created_at": now,
    })

    return {
        "football_id": str(football_id),
        "badminton_id": str(badminton_id),
        "athlete_a_id": str(ath_a.inserted_id),
        "athlete_b_id": str(ath_b.inserted_id),
        "athlete_c_id": str(ath_c.inserted_id),
        "athlete_d_id": str(ath_d.inserted_id),
        "coach_id": str(coach_id),
    }


@pytest.mark.asyncio
async def test_tournament_rankings_include_zero_participation(client, admin_token, db, admin_user, coach_user, athlete_user):
    data = await _setup_phase_e_data(db, admin_user, coach_user, athlete_user)
    now = datetime.now(timezone.utc)

    # Athlete Alpha participates in a tournament and earns Gold (10 pts)
    t_res = await db.tournaments.insert_one({
        "name": "Football Championship",
        "sport_id": ObjectId(data["football_id"]),
        "start_date": now,
        "end_date": now + timedelta(days=2),
        "status": "completed",
        "created_at": now,
    })
    await db.tournament_participants.insert_one({
        "tournament_id": t_res.inserted_id,
        "athlete_id": ObjectId(data["athlete_a_id"]),
        "points": 10.0,
        "medal": "gold",
        "created_at": now,
    })

    # 1. Unified endpoint defaults to include_zero=True
    resp = await client.get(
        f"/api/v1/rankings?type=tournament&sport_id={data['football_id']}",
        headers=auth_headers(admin_token),
    )
    assert resp.status_code == 200
    items = resp.json()["items"]
    # Alpha (10 pts), Beta (0 pts), Charlie (0 pts), Delta (0 pts - multi-sport eligible)
    assert len(items) == 4
    assert items[0]["athlete_name"] == "Athlete Alpha"
    assert items[0]["points"] == 10.0
    assert items[0]["gold_count"] == 1
    assert items[0]["tournaments_played"] == 1
    assert items[0]["rank"] == 1

    # Remaining 3 zero-participation athletes have 0 pts and 0 medals
    for zero_item in items[1:]:
        assert zero_item["points"] == 0.0
        assert zero_item["gold_count"] == 0
        assert zero_item["silver_count"] == 0
        assert zero_item["bronze_count"] == 0
        assert zero_item["total_medals"] == 0
        assert zero_item["tournaments_played"] == 0

    # Check alphabetical tie-breaker among the zero-participation athletes:
    # Athlete Beta, Athlete Charlie, Athlete Delta
    assert items[1]["athlete_name"] == "Athlete Beta"
    assert items[2]["athlete_name"] == "Athlete Charlie"
    assert items[3]["athlete_name"] == "Athlete Delta"

    # 2. When include_zero=False is explicitly requested on unified endpoint
    resp_no_zero = await client.get(
        f"/api/v1/rankings?type=tournament&sport_id={data['football_id']}&include_zero=false",
        headers=auth_headers(admin_token),
    )
    assert resp_no_zero.status_code == 200
    no_zero_items = resp_no_zero.json()["items"]
    assert len(no_zero_items) == 1
    assert no_zero_items[0]["athlete_name"] == "Athlete Alpha"

    # 3. Direct /api/v1/rankings/tournament endpoint defaults to include_zero=False for backwards compat
    resp_direct = await client.get(
        f"/api/v1/rankings/tournament?sport_id={data['football_id']}",
        headers=auth_headers(admin_token),
    )
    assert resp_direct.status_code == 200
    assert len(resp_direct.json()) == 1

    # 4. Direct /api/v1/rankings/tournament?include_zero=true includes all eligible athletes
    resp_direct_all = await client.get(
        f"/api/v1/rankings/tournament?sport_id={data['football_id']}&include_zero=true",
        headers=auth_headers(admin_token),
    )
    assert resp_direct_all.status_code == 200
    assert len(resp_direct_all.json()) == 4


@pytest.mark.asyncio
async def test_performance_rankings_include_unassessed_athletes(client, admin_token, db, admin_user, coach_user, athlete_user):
    data = await _setup_phase_e_data(db, admin_user, coach_user, athlete_user)
    now = datetime.now(timezone.utc)

    # Athlete Alpha has a verified assessment
    await db.performance_assessments.insert_one({
        "athlete_id": ObjectId(data["athlete_a_id"]),
        "coach_id": ObjectId(data["coach_id"]),
        "sport_id": ObjectId(data["football_id"]),
        "assessment_date": now,
        "overall_score": 88.5,
        "metric_scores": {"speed": 90.0, "stamina": 87.0},
        "created_at": now,
    })

    # Unified rankings include_zero=True (default)
    resp = await client.get(
        f"/api/v1/rankings?type=performance&sport_id={data['football_id']}",
        headers=auth_headers(admin_token),
    )
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 4

    # Assessed athlete is rank 1
    assert items[0]["athlete_name"] == "Athlete Alpha"
    assert items[0]["performance_score"] == 88.5
    assert items[0]["assessment_date"] is not None

    # Unassessed athletes appear at the bottom with None scores and dates
    for unassessed in items[1:]:
        assert unassessed["performance_score"] is None
        assert unassessed["assessment_date"] is None

    # Deterministic alphabetical ordering for unassessed
    assert items[1]["athlete_name"] == "Athlete Beta"
    assert items[2]["athlete_name"] == "Athlete Charlie"
    assert items[3]["athlete_name"] == "Athlete Delta"

    # With include_zero=False, only assessed athlete appears
    resp_no_zero = await client.get(
        f"/api/v1/rankings?type=performance&sport_id={data['football_id']}&include_zero=false",
        headers=auth_headers(admin_token),
    )
    assert resp_no_zero.status_code == 200
    assert len(resp_no_zero.json()["items"]) == 1


@pytest.mark.asyncio
async def test_attendance_rankings_include_zero_session_athletes(client, admin_token, db, admin_user, coach_user, athlete_user):
    data = await _setup_phase_e_data(db, admin_user, coach_user, athlete_user)
    now = datetime.now(timezone.utc)

    # Schedule a training session in football
    session_res = await db.training_sessions.insert_one({
        "sport_id": ObjectId(data["football_id"]),
        "coach_id": ObjectId(data["coach_id"]),
        "title": "Tactics Practice",
        "athlete_ids": [ObjectId(data["athlete_a_id"])],
        "session_date": now - timedelta(days=1),
        "status": "completed",
        "created_at": now,
    })

    # Only Athlete Alpha attended
    await db.attendance.insert_one({
        "session_id": session_res.inserted_id,
        "athlete_id": ObjectId(data["athlete_a_id"]),
        "status": "present",
        "created_at": now,
    })

    # Unified rankings include_zero=True (default)
    resp = await client.get(
        f"/api/v1/rankings?type=attendance&sport_id={data['football_id']}",
        headers=auth_headers(admin_token),
    )
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 4

    # Athlete Alpha has 100% attendance
    assert items[0]["athlete_name"] == "Athlete Alpha"
    assert items[0]["attendance_percentage"] == 100.0
    assert items[0]["attended_sessions"] == 1
    assert items[0]["total_sessions"] == 1

    # Zero-session athletes
    for zero_item in items[1:]:
        assert zero_item["attendance_percentage"] == 0.0
        assert zero_item["attended_sessions"] == 0
        assert zero_item["total_sessions"] == 0

    # With include_zero=False, only Alpha is returned
    resp_no_zero = await client.get(
        f"/api/v1/rankings?type=attendance&sport_id={data['football_id']}&include_zero=false",
        headers=auth_headers(admin_token),
    )
    assert resp_no_zero.status_code == 200
    assert len(resp_no_zero.json()["items"]) == 1


@pytest.mark.asyncio
async def test_tournament_rankings_ties_and_deterministic_order(client, admin_token, db, admin_user, coach_user, athlete_user):
    data = await _setup_phase_e_data(db, admin_user, coach_user, athlete_user)
    now = datetime.now(timezone.utc)

    # Both Athlete Alpha and Athlete Beta have identical points (10.0) and gold medals (1)
    t1 = await db.tournaments.insert_one({
        "name": "State Tourney 1",
        "sport_id": ObjectId(data["football_id"]),
        "start_date": now,
        "end_date": now + timedelta(days=2),
        "status": "completed",
        "created_at": now,
    })
    await db.tournament_participants.insert_many([
        {
            "tournament_id": t1.inserted_id,
            "athlete_id": ObjectId(data["athlete_a_id"]),
            "points": 10.0,
            "medal": "gold",
            "created_at": now,
        },
        {
            "tournament_id": t1.inserted_id,
            "athlete_id": ObjectId(data["athlete_b_id"]),
            "points": 10.0,
            "medal": "gold",
            "created_at": now,
        },
    ])

    resp = await client.get(
        f"/api/v1/rankings?type=tournament&sport_id={data['football_id']}",
        headers=auth_headers(admin_token),
    )
    assert resp.status_code == 200
    items = resp.json()["items"]

    # Alpha and Beta tie in points, gold, silver, bronze, tournaments
    # Deterministic tie break: Athlete Alpha before Athlete Beta by alphabetical order
    assert items[0]["athlete_name"] == "Athlete Alpha"
    assert items[0]["rank"] == 1
    assert items[1]["athlete_name"] == "Athlete Beta"
    assert items[1]["rank"] == 2

    # Zero participation athletes Charlie and Delta follow
    assert items[2]["athlete_name"] == "Athlete Charlie"
    assert items[2]["points"] == 0.0
    assert items[2]["rank"] == 3
    assert items[3]["athlete_name"] == "Athlete Delta"
    assert items[3]["points"] == 0.0
    assert items[3]["rank"] == 4


@pytest.mark.asyncio
async def test_rankings_rbac_and_all_sports(client, coach_token, athlete_token, db, admin_user, coach_user, athlete_user):
    data = await _setup_phase_e_data(db, admin_user, coach_user, athlete_user)

    # 1. Coach can read tournament rankings with include_zero=true across all sports
    resp_coach = await client.get(
        "/api/v1/rankings?type=tournament",
        headers=auth_headers(coach_token),
    )
    assert resp_coach.status_code == 200
    coach_items = resp_coach.json()["items"]
    # All 4 athletes in the academy appear
    assert len(coach_items) == 4

    # 2. Athlete can read rankings
    resp_ath = await client.get(
        "/api/v1/rankings?type=performance",
        headers=auth_headers(athlete_token),
    )
    assert resp_ath.status_code == 200
    ath_items = resp_ath.json()["items"]
    assert len(ath_items) == 4
