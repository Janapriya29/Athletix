"""
User management tests — Phase 2.
"""
import pytest


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_admin_can_list_users(client, admin_token, coach_user, athlete_user):
    resp = await client.get("/api/v1/users", headers=auth_headers(admin_token))
    assert resp.status_code == 200
    users = resp.json()
    assert len(users) >= 3
    for u in users:
        assert "hashed_password" not in u
        assert "password" not in u


@pytest.mark.asyncio
async def test_coach_cannot_access_user_management(client, coach_token):
    resp = await client.get("/api/v1/users", headers=auth_headers(coach_token))
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_athlete_cannot_access_user_management(client, athlete_token):
    resp = await client.get("/api/v1/users", headers=auth_headers(athlete_token))
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_create_user_with_hashed_password(client, admin_token, db):
    payload = {
        "email": "newcoach@test.com",
        "full_name": "New Coach",
        "password": "Password123!",
        "role": "coach",
    }
    resp = await client.post("/api/v1/users", json=payload, headers=auth_headers(admin_token))
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "newcoach@test.com"
    assert "password" not in data
    assert "hashed_password" not in data

    # Verify password was hashed in database, not stored in plaintext
    doc = await db.users.find_one({"email": "newcoach@test.com"})
    assert doc is not None
    assert doc["hashed_password"] != "Password123!"
    assert doc["hashed_password"].startswith("$2b$")


@pytest.mark.asyncio
async def test_admin_can_deactivate_user(client, admin_token, athlete_user, db):
    user_id = str(athlete_user["_id"])
    patch_resp = await client.patch(
        f"/api/v1/users/{user_id}/status",
        json={"is_active": False},
        headers=auth_headers(admin_token),
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["is_active"] is False

    doc = await db.users.find_one({"_id": athlete_user["_id"]})
    assert doc["is_active"] is False


@pytest.mark.asyncio
async def test_search_and_filter_users(client, admin_token):
    await client.post(
        "/api/v1/users",
        json={"email": "filter1@test.com", "full_name": "Alice Wonder", "password": "Pass@12345", "role": "coach"},
        headers=auth_headers(admin_token),
    )
    await client.post(
        "/api/v1/users",
        json={"email": "filter2@test.com", "full_name": "Bob Builder", "password": "Pass@12345", "role": "athlete"},
        headers=auth_headers(admin_token),
    )

    # Filter by role
    resp = await client.get("/api/v1/users?role=coach", headers=auth_headers(admin_token))
    roles = [u["role"] for u in resp.json()]
    assert all(r == "coach" for r in roles)

    # Search by name
    resp2 = await client.get("/api/v1/users?search=Alice", headers=auth_headers(admin_token))
    assert any(u["email"] == "filter1@test.com" for u in resp2.json())
