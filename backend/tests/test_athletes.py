"""
Athlete management tests — Phase 2.
"""
import pytest
from bson import ObjectId


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_admin_can_create_and_view_athlete(client, admin_token, db):
    s_res = await db.sports.insert_one({"name": "Rowing", "is_active": True})
    sport_id = str(s_res.inserted_id)

    payload = {
        "full_name": "John Rower",
        "email": "john.rower@test.com",
        "password": "Password123!",
        "phone": "+1 555-0199",
        "gender": "male",
        "sport_id": sport_id,
        "address": "123 Water Way",
        "emergency_contact": "Mom: 555-0100",
        "status": "active",
    }
    resp = await client.post("/api/v1/athletes", json=payload, headers=auth_headers(admin_token))
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["full_name"] == "John Rower"
    assert data["sport_name"] == "Rowing"
    assert data["address"] == "123 Water Way"

    ath_id = data["id"]
    get_resp = await client.get(f"/api/v1/athletes/{ath_id}", headers=auth_headers(admin_token))
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == ath_id


@pytest.mark.asyncio
async def test_invalid_sport_rejected(client, admin_token):
    fake_sport_id = str(ObjectId())
    payload = {
        "full_name": "No Sport Guy",
        "email": "nosport@test.com",
        "sport_id": fake_sport_id,
    }
    resp = await client.post("/api/v1/athletes", json=payload, headers=auth_headers(admin_token))
    assert resp.status_code == 400
    assert "not found" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_invalid_coach_rejected(client, admin_token, db):
    s_res = await db.sports.insert_one({"name": "Golf", "is_active": True})
    sport_id = str(s_res.inserted_id)
    fake_coach_id = str(ObjectId())

    payload = {
        "full_name": "Golfer Dan",
        "email": "dan@test.com",
        "sport_id": sport_id,
        "coach_id": fake_coach_id,
    }
    resp = await client.post("/api/v1/athletes", json=payload, headers=auth_headers(admin_token))
    assert resp.status_code == 400
    assert "Coach ID" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_athlete_can_view_own_profile(client, athlete_user, athlete_token, db):
    s_res = await db.sports.insert_one({"name": "Fencing", "is_active": True})
    await db.athletes.insert_one({
        "user_id": athlete_user["_id"],
        "full_name": athlete_user["full_name"],
        "email": athlete_user["email"],
        "sport_id": s_res.inserted_id,
        "status": "active",
        "phone": "+1 1234567890",
    })

    resp = await client.get("/api/v1/athletes/me", headers=auth_headers(athlete_token))
    assert resp.status_code == 200, resp.text
    assert resp.json()["email"] == athlete_user["email"]
    assert resp.json()["phone"] == "+1 1234567890"


@pytest.mark.asyncio
async def test_athlete_cannot_view_another_athlete(client, athlete_user, athlete_token, db):
    # Athlete's own profile
    s_res = await db.sports.insert_one({"name": "Judo", "is_active": True})
    await db.athletes.insert_one({
        "user_id": athlete_user["_id"],
        "full_name": athlete_user["full_name"],
        "email": athlete_user["email"],
        "sport_id": s_res.inserted_id,
        "status": "active",
    })

    # Another athlete
    other_ath = await db.athletes.insert_one({
        "user_id": ObjectId(),
        "full_name": "Other Athlete",
        "email": "other@test.com",
        "sport_id": s_res.inserted_id,
        "status": "active",
    })

    # Try to access other athlete by ID
    resp = await client.get(f"/api/v1/athletes/{other_ath.inserted_id}", headers=auth_headers(athlete_token))
    assert resp.status_code == 403
    assert "own" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_coach_can_view_assigned_athlete_only(client, coach_user, coach_token, db):
    s_res = await db.sports.insert_one({"name": "Sprint", "is_active": True})

    # Create coach profile
    c_res = await db.coaches.insert_one({
        "user_id": coach_user["_id"],
        "full_name": coach_user["full_name"],
        "email": coach_user["email"],
        "status": "active",
        "sport_ids": [s_res.inserted_id],
    })
    coach_id = c_res.inserted_id

    # Athlete 1: assigned to coach
    ath1 = await db.athletes.insert_one({
        "user_id": ObjectId(),
        "full_name": "Assigned Athlete",
        "email": "assigned@test.com",
        "sport_id": s_res.inserted_id,
        "coach_id": coach_id,
        "status": "active",
    })
    await db.coach_athlete_assignments.insert_one({
        "coach_id": coach_id,
        "athlete_id": ath1.inserted_id,
    })

    # Athlete 2: not assigned to coach
    ath2 = await db.athletes.insert_one({
        "user_id": ObjectId(),
        "full_name": "Unassigned Athlete",
        "email": "unassigned@test.com",
        "sport_id": s_res.inserted_id,
        "coach_id": None,
        "status": "active",
    })

    # Coach accesses assigned athlete -> 200 OK
    resp1 = await client.get(f"/api/v1/athletes/{ath1.inserted_id}", headers=auth_headers(coach_token))
    assert resp1.status_code == 200
    assert resp1.json()["full_name"] == "Assigned Athlete"

    # Coach accesses unassigned athlete -> 403 Forbidden
    resp2 = await client.get(f"/api/v1/athletes/{ath2.inserted_id}", headers=auth_headers(coach_token))
    assert resp2.status_code == 403
    assert "not assigned" in resp2.json()["detail"]


@pytest.mark.asyncio
async def test_athlete_self_update_allowed_fields(client, athlete_user, athlete_token, db):
    s_res = await db.sports.insert_one({"name": "Skating", "is_active": True})
    a_res = await db.athletes.insert_one({
        "user_id": athlete_user["_id"],
        "full_name": athlete_user["full_name"],
        "email": athlete_user["email"],
        "sport_id": s_res.inserted_id,
        "status": "active",
        "phone": "+1 000-0000",
    })
    ath_id = str(a_res.inserted_id)

    # Athlete updates phone and address
    update_resp = await client.put(
        f"/api/v1/athletes/{ath_id}",
        json={"phone": "+1 999-9999", "address": "789 New St", "full_name": "Hacked Name"},
        headers=auth_headers(athlete_token),
    )
    assert update_resp.status_code == 200
    data = update_resp.json()
    assert data["phone"] == "+1 999-9999"
    assert data["address"] == "789 New St"
    # full_name should NOT have changed because non-admin athletes cannot alter full_name
    assert data["full_name"] == athlete_user["full_name"]
