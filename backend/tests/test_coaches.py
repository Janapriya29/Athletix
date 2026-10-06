"""
Coach management tests — Phase 2.
"""
import pytest
from bson import ObjectId


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_admin_can_create_and_view_coach(client, admin_token, db):
    # Create sport first
    sport_doc = {
        "name": "Boxing",
        "description": "Combat sport",
        "is_active": True,
    }
    s_res = await db.sports.insert_one(sport_doc)
    sport_id = str(s_res.inserted_id)

    payload = {
        "full_name": "Mike Tyson",
        "email": "mike@coach.com",
        "password": "Password123!",
        "specialization": "Heavyweight",
        "experience_years": 15,
        "sport_ids": [sport_id],
        "bio": "Legendary coach",
    }
    resp = await client.post("/api/v1/coaches", json=payload, headers=auth_headers(admin_token))
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["full_name"] == "Mike Tyson"
    assert data["email"] == "mike@coach.com"
    assert data["specialization"] == "Heavyweight"
    assert len(data["sports"]) == 1
    assert data["sports"][0]["name"] == "Boxing"

    coach_id = data["id"]
    get_resp = await client.get(f"/api/v1/coaches/{coach_id}", headers=auth_headers(admin_token))
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == coach_id


@pytest.mark.asyncio
async def test_coach_can_view_own_profile(client, coach_user, coach_token, db):
    # Insert coach profile for coach_user
    c_doc = {
        "user_id": coach_user["_id"],
        "full_name": coach_user["full_name"],
        "email": coach_user["email"],
        "specialization": "Head Coach",
        "status": "active",
        "sport_ids": [],
    }
    await db.coaches.insert_one(c_doc)

    resp = await client.get("/api/v1/coaches/me", headers=auth_headers(coach_token))
    assert resp.status_code == 200, resp.text
    assert resp.json()["email"] == coach_user["email"]


@pytest.mark.asyncio
async def test_coach_cannot_create_coach(client, coach_token):
    resp = await client.post(
        "/api/v1/coaches",
        json={"full_name": "Another Coach", "email": "another@coach.com"},
        headers=auth_headers(coach_token),
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_athlete_cannot_manage_coaches(client, athlete_token):
    resp = await client.post(
        "/api/v1/coaches",
        json={"full_name": "Coach Test", "email": "test@coach.com"},
        headers=auth_headers(athlete_token),
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_assign_and_remove_athletes(client, admin_token, db):
    # Setup coach
    c_res = await db.coaches.insert_one({
        "full_name": "Trainer Joe",
        "email": "joe@test.com",
        "status": "active",
        "sport_ids": [],
    })
    coach_id = str(c_res.inserted_id)

    # Setup athlete
    s_res = await db.sports.insert_one({"name": "Track", "is_active": True})
    a_res = await db.athletes.insert_one({
        "full_name": "Runner Fast",
        "email": "runner@test.com",
        "sport_id": s_res.inserted_id,
        "status": "active",
    })
    athlete_id = str(a_res.inserted_id)

    # Assign
    assign_resp = await client.post(
        f"/api/v1/coaches/{coach_id}/athletes",
        json={"athlete_ids": [athlete_id]},
        headers=auth_headers(admin_token),
    )
    assert assign_resp.status_code == 200

    # Verify assignment exists in db
    assignment = await db.coach_athlete_assignments.find_one({
        "coach_id": ObjectId(coach_id),
        "athlete_id": ObjectId(athlete_id),
    })
    assert assignment is not None

    # Verify coach athlete_count reflects assignment
    c_check = await client.get(f"/api/v1/coaches/{coach_id}", headers=auth_headers(admin_token))
    assert c_check.json()["athlete_count"] == 1

    # Remove assignment
    del_resp = await client.delete(
        f"/api/v1/coaches/{coach_id}/athletes/{athlete_id}",
        headers=auth_headers(admin_token),
    )
    assert del_resp.status_code == 200

    assignment_after = await db.coach_athlete_assignments.find_one({
        "coach_id": ObjectId(coach_id),
        "athlete_id": ObjectId(athlete_id),
    })
    assert assignment_after is None
