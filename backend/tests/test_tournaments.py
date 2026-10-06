"""
Tournaments & Participation Tests — Phase 6.
Covers Minimum tournament tests (1-20):
1. Admin can create tournament
2. Coach cannot create tournament unless explicitly allowed (403)
3. Athlete cannot create tournament (403)
4. Invalid sport rejected
5. Inactive sport rejected
6. Invalid date range rejected
7. Invalid registration deadline rejected
8. Admin can view tournaments
9. Coach can view relevant tournaments
10. Athlete can view tournaments
11. Duplicate participation rejected
12. Admin can add participant
13. Coach can add assigned athlete
14. Coach cannot add unassigned athlete
15. Athlete cannot add another athlete
16. Admin can record result
17. Coach result permissions enforced
18. Athlete cannot modify result
19. Duplicate result handled
20. Tournament details return correct participants/results
"""
from datetime import datetime, timedelta, timezone
from bson import ObjectId
import pytest


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── Fixture Helper ─────────────────────────────────────────────────────────────

async def _setup_tournament_test_data(db, admin_user, coach_user, athlete_user):
    now = datetime.now(timezone.utc)

    # Sports
    sport_doc = await db.sports.insert_one({"name": "Football", "is_active": True, "created_at": now})
    football_id = sport_doc.inserted_id

    inactive_sport_doc = await db.sports.insert_one({"name": "Archery", "is_active": False, "created_at": now})
    inactive_sport_id = inactive_sport_doc.inserted_id

    # Coach profile
    coach_profile = await db.coaches.insert_one({
        "user_id": coach_user["_id"],
        "full_name": coach_user["full_name"],
        "email": coach_user["email"],
        "status": "active",
        "sport_ids": [football_id],
        "created_at": now,
    })
    coach_id = coach_profile.inserted_id

    # Athlete 1 (Assigned to coach_user)
    athlete1_profile = await db.athletes.insert_one({
        "user_id": athlete_user["_id"],
        "full_name": athlete_user["full_name"],
        "email": athlete_user["email"],
        "status": "active",
        "sport_id": football_id,
        "coach_id": coach_id,
        "created_at": now,
    })
    athlete1_id = athlete1_profile.inserted_id

    # Athlete 2 (Unassigned / different coach)
    u_ath2 = await db.users.insert_one({
        "email": "athlete2@test.com",
        "role": "athlete",
        "full_name": "Athlete Two",
        "is_active": True,
        "created_at": now,
    })
    athlete2_profile = await db.athletes.insert_one({
        "user_id": u_ath2.inserted_id,
        "full_name": "Athlete Two",
        "email": "athlete2@test.com",
        "status": "active",
        "sport_id": football_id,
        "coach_id": None,
        "created_at": now,
    })
    athlete2_id = athlete2_profile.inserted_id

    return {
        "football_id": str(football_id),
        "inactive_sport_id": str(inactive_sport_id),
        "coach_id": str(coach_id),
        "athlete1_id": str(athlete1_id),
        "athlete2_id": str(athlete2_id),
        "athlete2_user_id": str(u_ath2.inserted_id),
    }


# ── 1. Admin can create tournament ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_01_admin_can_create_tournament(client, admin_token, db, admin_user, coach_user, athlete_user):
    data = await _setup_tournament_test_data(db, admin_user, coach_user, athlete_user)
    now = datetime.now(timezone.utc)

    payload = {
        "name": "State Championship 2026",
        "description": "Annual state football tournament",
        "sport_id": data["football_id"],
        "location": "Central Stadium",
        "start_date": (now + timedelta(days=10)).isoformat(),
        "end_date": (now + timedelta(days=15)).isoformat(),
        "registration_deadline": (now + timedelta(days=5)).isoformat(),
        "status": "upcoming",
    }
    res = await client.post("/api/v1/tournaments", json=payload, headers=auth_headers(admin_token))
    assert res.status_code == 201
    body = res.json()
    assert body["name"] == "State Championship 2026"
    assert body["sport_id"] == data["football_id"]
    assert body["status"] == "upcoming"
    assert "id" in body


# ── 2. Coach cannot create tournament unless explicitly allowed ────────────────

@pytest.mark.asyncio
async def test_02_coach_cannot_create_tournament(client, coach_token, db, admin_user, coach_user, athlete_user):
    data = await _setup_tournament_test_data(db, admin_user, coach_user, athlete_user)
    now = datetime.now(timezone.utc)

    payload = {
        "name": "Coach Tournament",
        "sport_id": data["football_id"],
        "location": "Local Ground",
        "start_date": (now + timedelta(days=10)).isoformat(),
        "end_date": (now + timedelta(days=15)).isoformat(),
    }
    res = await client.post("/api/v1/tournaments", json=payload, headers=auth_headers(coach_token))
    assert res.status_code == 403


# ── 3. Athlete cannot create tournament ────────────────────────────────────────

@pytest.mark.asyncio
async def test_03_athlete_cannot_create_tournament(client, athlete_token, db, admin_user, coach_user, athlete_user):
    data = await _setup_tournament_test_data(db, admin_user, coach_user, athlete_user)
    now = datetime.now(timezone.utc)

    payload = {
        "name": "Athlete Tournament",
        "sport_id": data["football_id"],
        "location": "Local Ground",
        "start_date": (now + timedelta(days=10)).isoformat(),
        "end_date": (now + timedelta(days=15)).isoformat(),
    }
    res = await client.post("/api/v1/tournaments", json=payload, headers=auth_headers(athlete_token))
    assert res.status_code == 403


# ── 4. Invalid sport rejected ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_04_invalid_sport_rejected(client, admin_token, db, admin_user, coach_user, athlete_user):
    await _setup_tournament_test_data(db, admin_user, coach_user, athlete_user)
    now = datetime.now(timezone.utc)
    fake_sport_id = str(ObjectId())

    payload = {
        "name": "Invalid Sport Tournament",
        "sport_id": fake_sport_id,
        "location": "Local Ground",
        "start_date": (now + timedelta(days=10)).isoformat(),
        "end_date": (now + timedelta(days=15)).isoformat(),
    }
    res = await client.post("/api/v1/tournaments", json=payload, headers=auth_headers(admin_token))
    assert res.status_code == 400


# ── 5. Inactive sport rejected ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_05_inactive_sport_rejected(client, admin_token, db, admin_user, coach_user, athlete_user):
    data = await _setup_tournament_test_data(db, admin_user, coach_user, athlete_user)
    now = datetime.now(timezone.utc)

    payload = {
        "name": "Archery Cup",
        "sport_id": data["inactive_sport_id"],
        "location": "Range",
        "start_date": (now + timedelta(days=10)).isoformat(),
        "end_date": (now + timedelta(days=15)).isoformat(),
    }
    res = await client.post("/api/v1/tournaments", json=payload, headers=auth_headers(admin_token))
    assert res.status_code == 400


# ── 6. Invalid date range rejected ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_06_invalid_date_range_rejected(client, admin_token, db, admin_user, coach_user, athlete_user):
    data = await _setup_tournament_test_data(db, admin_user, coach_user, athlete_user)
    now = datetime.now(timezone.utc)

    payload = {
        "name": "Backwards Date Tournament",
        "sport_id": data["football_id"],
        "location": "Ground",
        "start_date": (now + timedelta(days=15)).isoformat(),
        "end_date": (now + timedelta(days=10)).isoformat(),  # end before start
    }
    res = await client.post("/api/v1/tournaments", json=payload, headers=auth_headers(admin_token))
    assert res.status_code in (400, 422)


# ── 7. Invalid registration deadline rejected ──────────────────────────────────

@pytest.mark.asyncio
async def test_07_invalid_registration_deadline_rejected(client, admin_token, db, admin_user, coach_user, athlete_user):
    data = await _setup_tournament_test_data(db, admin_user, coach_user, athlete_user)
    now = datetime.now(timezone.utc)

    payload = {
        "name": "Late Deadline Tournament",
        "sport_id": data["football_id"],
        "location": "Ground",
        "start_date": (now + timedelta(days=10)).isoformat(),
        "end_date": (now + timedelta(days=15)).isoformat(),
        "registration_deadline": (now + timedelta(days=12)).isoformat(),  # deadline after start
    }
    res = await client.post("/api/v1/tournaments", json=payload, headers=auth_headers(admin_token))
    assert res.status_code in (400, 422)


# ── 8. Admin can view tournaments ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_08_admin_can_view_tournaments(client, admin_token, db, admin_user, coach_user, athlete_user):
    data = await _setup_tournament_test_data(db, admin_user, coach_user, athlete_user)
    now = datetime.now(timezone.utc)

    await db.tournaments.insert_one({
        "name": "Admin View Cup",
        "sport_id": ObjectId(data["football_id"]),
        "location": "Stadium",
        "start_date": now + timedelta(days=5),
        "end_date": now + timedelta(days=8),
        "status": "upcoming",
        "created_at": now,
    })
    res = await client.get("/api/v1/tournaments", headers=auth_headers(admin_token))
    assert res.status_code == 200
    assert len(res.json()) >= 1


# ── 9. Coach can view relevant tournaments ─────────────────────────────────────

@pytest.mark.asyncio
async def test_09_coach_can_view_tournaments(client, coach_token, db, admin_user, coach_user, athlete_user):
    data = await _setup_tournament_test_data(db, admin_user, coach_user, athlete_user)
    now = datetime.now(timezone.utc)

    await db.tournaments.insert_one({
        "name": "Coach View Cup",
        "sport_id": ObjectId(data["football_id"]),
        "location": "Stadium",
        "start_date": now + timedelta(days=5),
        "end_date": now + timedelta(days=8),
        "status": "upcoming",
        "created_at": now,
    })
    res = await client.get("/api/v1/tournaments", headers=auth_headers(coach_token))
    assert res.status_code == 200
    assert any(t["name"] == "Coach View Cup" for t in res.json())


# ── 10. Athlete can view tournaments ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_10_athlete_can_view_tournaments(client, athlete_token, db, admin_user, coach_user, athlete_user):
    data = await _setup_tournament_test_data(db, admin_user, coach_user, athlete_user)
    now = datetime.now(timezone.utc)

    await db.tournaments.insert_one({
        "name": "Athlete View Cup",
        "sport_id": ObjectId(data["football_id"]),
        "location": "Stadium",
        "start_date": now + timedelta(days=5),
        "end_date": now + timedelta(days=8),
        "status": "upcoming",
        "created_at": now,
    })
    res = await client.get("/api/v1/tournaments", headers=auth_headers(athlete_token))
    assert res.status_code == 200
    assert any(t["name"] == "Athlete View Cup" for t in res.json())


# ── 11. Duplicate participation rejected ───────────────────────────────────────

@pytest.mark.asyncio
async def test_11_duplicate_participation_rejected(client, admin_token, db, admin_user, coach_user, athlete_user):
    data = await _setup_tournament_test_data(db, admin_user, coach_user, athlete_user)
    now = datetime.now(timezone.utc)

    t_res = await db.tournaments.insert_one({
        "name": "Dupe Test Cup",
        "sport_id": ObjectId(data["football_id"]),
        "location": "Stadium",
        "start_date": now + timedelta(days=5),
        "end_date": now + timedelta(days=8),
        "status": "upcoming",
        "created_at": now,
    })
    t_id = str(t_res.inserted_id)

    # First add
    payload = {"athlete_id": data["athlete1_id"], "event": "Singles"}
    res1 = await client.post(f"/api/v1/tournaments/{t_id}/participants", json=payload, headers=auth_headers(admin_token))
    assert res1.status_code == 201

    # Second add -> 400
    res2 = await client.post(f"/api/v1/tournaments/{t_id}/participants", json=payload, headers=auth_headers(admin_token))
    assert res2.status_code == 400
    assert "already registered" in res2.json()["detail"].lower()


# ── 12. Admin can add participant ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_12_admin_can_add_participant(client, admin_token, db, admin_user, coach_user, athlete_user):
    data = await _setup_tournament_test_data(db, admin_user, coach_user, athlete_user)
    now = datetime.now(timezone.utc)

    t_res = await db.tournaments.insert_one({
        "name": "Admin Participant Cup",
        "sport_id": ObjectId(data["football_id"]),
        "location": "Stadium",
        "start_date": now + timedelta(days=5),
        "end_date": now + timedelta(days=8),
        "status": "upcoming",
        "created_at": now,
    })
    t_id = str(t_res.inserted_id)

    payload = {"athlete_id": data["athlete2_id"], "event": "Main Draw"}
    res = await client.post(f"/api/v1/tournaments/{t_id}/participants", json=payload, headers=auth_headers(admin_token))
    assert res.status_code == 201
    assert res.json()["athlete_id"] == data["athlete2_id"]


# ── 13. Coach can add assigned athlete ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_13_coach_can_add_assigned_athlete(client, coach_token, db, admin_user, coach_user, athlete_user):
    data = await _setup_tournament_test_data(db, admin_user, coach_user, athlete_user)
    now = datetime.now(timezone.utc)

    t_res = await db.tournaments.insert_one({
        "name": "Coach Add Assigned Cup",
        "sport_id": ObjectId(data["football_id"]),
        "location": "Stadium",
        "start_date": now + timedelta(days=5),
        "end_date": now + timedelta(days=8),
        "status": "upcoming",
        "created_at": now,
    })
    t_id = str(t_res.inserted_id)

    payload = {"athlete_id": data["athlete1_id"], "event": "League"}
    res = await client.post(f"/api/v1/tournaments/{t_id}/participants", json=payload, headers=auth_headers(coach_token))
    assert res.status_code == 201


# ── 14. Coach cannot add unassigned athlete ────────────────────────────────────

@pytest.mark.asyncio
async def test_14_coach_cannot_add_unassigned_athlete(client, coach_token, db, admin_user, coach_user, athlete_user):
    data = await _setup_tournament_test_data(db, admin_user, coach_user, athlete_user)
    now = datetime.now(timezone.utc)

    t_res = await db.tournaments.insert_one({
        "name": "Coach Add Unassigned Cup",
        "sport_id": ObjectId(data["football_id"]),
        "location": "Stadium",
        "start_date": now + timedelta(days=5),
        "end_date": now + timedelta(days=8),
        "status": "upcoming",
        "created_at": now,
    })
    t_id = str(t_res.inserted_id)

    payload = {"athlete_id": data["athlete2_id"], "event": "League"}
    res = await client.post(f"/api/v1/tournaments/{t_id}/participants", json=payload, headers=auth_headers(coach_token))
    assert res.status_code == 403


# ── 15. Athlete cannot add another athlete ─────────────────────────────────────

@pytest.mark.asyncio
async def test_15_athlete_cannot_add_another_athlete(client, athlete_token, db, admin_user, coach_user, athlete_user):
    data = await _setup_tournament_test_data(db, admin_user, coach_user, athlete_user)
    now = datetime.now(timezone.utc)

    t_res = await db.tournaments.insert_one({
        "name": "Athlete Add Other Cup",
        "sport_id": ObjectId(data["football_id"]),
        "location": "Stadium",
        "start_date": now + timedelta(days=5),
        "end_date": now + timedelta(days=8),
        "status": "upcoming",
        "created_at": now,
    })
    t_id = str(t_res.inserted_id)

    # Athlete 1 tries to add Athlete 2
    payload = {"athlete_id": data["athlete2_id"], "event": "League"}
    res = await client.post(f"/api/v1/tournaments/{t_id}/participants", json=payload, headers=auth_headers(athlete_token))
    assert res.status_code == 403


# ── 16. Admin can record result ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_16_admin_can_record_result(client, admin_token, db, admin_user, coach_user, athlete_user):
    data = await _setup_tournament_test_data(db, admin_user, coach_user, athlete_user)
    now = datetime.now(timezone.utc)

    t_res = await db.tournaments.insert_one({
        "name": "Result Recording Cup",
        "sport_id": ObjectId(data["football_id"]),
        "location": "Stadium",
        "start_date": now + timedelta(days=1),
        "end_date": now + timedelta(days=3),
        "status": "ongoing",
        "created_at": now,
    })
    t_id = str(t_res.inserted_id)

    # Register athlete first
    await db.tournament_participants.insert_one({
        "tournament_id": t_res.inserted_id,
        "athlete_id": ObjectId(data["athlete1_id"]),
        "status": "registered",
        "created_at": now,
    })

    result_payload = {
        "athlete_id": data["athlete1_id"],
        "position": 1,
        "score": "3-1",
        "remarks": "Gold medal winning performance",
    }
    res = await client.post(f"/api/v1/tournaments/{t_id}/results", json=result_payload, headers=auth_headers(admin_token))
    assert res.status_code == 200
    body = res.json()
    assert body["position"] == 1
    assert body["medal"] == "Gold"
    assert body["points"] == 10.0
    assert body["status"] == "participated"


# ── 17. Coach result permissions enforced ──────────────────────────────────────

@pytest.mark.asyncio
async def test_17_coach_result_permissions_enforced(client, coach_token, db, admin_user, coach_user, athlete_user):
    data = await _setup_tournament_test_data(db, admin_user, coach_user, athlete_user)
    now = datetime.now(timezone.utc)

    t_res = await db.tournaments.insert_one({
        "name": "Coach Result Cup",
        "sport_id": ObjectId(data["football_id"]),
        "location": "Stadium",
        "start_date": now + timedelta(days=1),
        "end_date": now + timedelta(days=3),
        "status": "ongoing",
        "created_at": now,
    })
    t_id = str(t_res.inserted_id)

    # Register both athletes
    await db.tournament_participants.insert_many([
        {"tournament_id": t_res.inserted_id, "athlete_id": ObjectId(data["athlete1_id"]), "status": "registered", "created_at": now},
        {"tournament_id": t_res.inserted_id, "athlete_id": ObjectId(data["athlete2_id"]), "status": "registered", "created_at": now},
    ])

    # Coach can record for assigned athlete1
    res1 = await client.post(
        f"/api/v1/tournaments/{t_id}/results",
        json={"athlete_id": data["athlete1_id"], "position": 2, "remarks": "Runner up"},
        headers=auth_headers(coach_token),
    )
    assert res1.status_code == 200
    assert res1.json()["medal"] == "Silver"

    # Coach CANNOT record for unassigned athlete2
    res2 = await client.post(
        f"/api/v1/tournaments/{t_id}/results",
        json={"athlete_id": data["athlete2_id"], "position": 3},
        headers=auth_headers(coach_token),
    )
    assert res2.status_code == 403


# ── 18. Athlete cannot modify result ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_18_athlete_cannot_modify_result(client, athlete_token, db, admin_user, coach_user, athlete_user):
    data = await _setup_tournament_test_data(db, admin_user, coach_user, athlete_user)
    now = datetime.now(timezone.utc)

    t_res = await db.tournaments.insert_one({
        "name": "Athlete Result Cup",
        "sport_id": ObjectId(data["football_id"]),
        "location": "Stadium",
        "start_date": now + timedelta(days=1),
        "end_date": now + timedelta(days=3),
        "status": "ongoing",
        "created_at": now,
    })
    t_id = str(t_res.inserted_id)

    await db.tournament_participants.insert_one({
        "tournament_id": t_res.inserted_id,
        "athlete_id": ObjectId(data["athlete1_id"]),
        "status": "registered",
        "created_at": now,
    })

    res = await client.post(
        f"/api/v1/tournaments/{t_id}/results",
        json={"athlete_id": data["athlete1_id"], "position": 1},
        headers=auth_headers(athlete_token),
    )
    assert res.status_code == 403


# ── 19. Duplicate result handled ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_19_duplicate_result_handled(client, admin_token, db, admin_user, coach_user, athlete_user):
    data = await _setup_tournament_test_data(db, admin_user, coach_user, athlete_user)
    now = datetime.now(timezone.utc)

    t_res = await db.tournaments.insert_one({
        "name": "Duplicate Result Cup",
        "sport_id": ObjectId(data["football_id"]),
        "location": "Stadium",
        "start_date": now + timedelta(days=1),
        "end_date": now + timedelta(days=3),
        "status": "ongoing",
        "created_at": now,
    })
    t_id = str(t_res.inserted_id)

    await db.tournament_participants.insert_one({
        "tournament_id": t_res.inserted_id,
        "athlete_id": ObjectId(data["athlete1_id"]),
        "status": "registered",
        "created_at": now,
    })

    # Record 1
    res1 = await client.post(
        f"/api/v1/tournaments/{t_id}/results",
        json={"athlete_id": data["athlete1_id"], "position": 3, "score": "Initial"},
        headers=auth_headers(admin_token),
    )
    assert res1.status_code == 200
    assert res1.json()["medal"] == "Bronze"

    # Record 2 updates cleanly without duplicate error
    res2 = await client.post(
        f"/api/v1/tournaments/{t_id}/results",
        json={"athlete_id": data["athlete1_id"], "position": 1, "score": "Final Update"},
        headers=auth_headers(admin_token),
    )
    assert res2.status_code == 200
    assert res2.json()["position"] == 1
    assert res2.json()["medal"] == "Gold"

    # Verify still only 1 participant record
    count = await db.tournament_participants.count_documents({
        "tournament_id": t_res.inserted_id,
        "athlete_id": ObjectId(data["athlete1_id"]),
    })
    assert count == 1


# ── 20. Tournament details return correct participants/results ─────────────────

@pytest.mark.asyncio
async def test_20_tournament_details_return_correct_participants_results(client, admin_token, db, admin_user, coach_user, athlete_user):
    data = await _setup_tournament_test_data(db, admin_user, coach_user, athlete_user)
    now = datetime.now(timezone.utc)

    t_res = await db.tournaments.insert_one({
        "name": "Full Details Cup",
        "sport_id": ObjectId(data["football_id"]),
        "location": "Stadium",
        "start_date": now + timedelta(days=1),
        "end_date": now + timedelta(days=3),
        "status": "completed",
        "created_at": now,
    })
    t_id = str(t_res.inserted_id)

    await db.tournament_participants.insert_one({
        "tournament_id": t_res.inserted_id,
        "athlete_id": ObjectId(data["athlete1_id"]),
        "event": "Football Final",
        "status": "participated",
        "position": 1,
        "medal": "Gold",
        "points": 10.0,
        "score": "2-0",
        "created_at": now,
    })

    # 1. Get tournament info
    res_t = await client.get(f"/api/v1/tournaments/{t_id}", headers=auth_headers(admin_token))
    assert res_t.status_code == 200
    assert res_t.json()["participant_count"] == 1

    # 2. Get participants
    res_p = await client.get(f"/api/v1/tournaments/{t_id}/participants", headers=auth_headers(admin_token))
    assert res_p.status_code == 200
    p_list = res_p.json()
    assert len(p_list) == 1
    assert p_list[0]["athlete_name"] == athlete_user["full_name"]
    assert p_list[0]["medal"] == "Gold"

    # 3. Get results endpoint
    res_r = await client.get(f"/api/v1/tournaments/{t_id}/results", headers=auth_headers(admin_token))
    assert res_r.status_code == 200
    r_list = res_r.json()
    assert len(r_list) == 1
    assert r_list[0]["position"] == 1
