"""
Registration & Account Access Experience tests — Phase 9.

Tests all registration behaviors and security policies:
1. Valid athlete registration creates active user + linked athlete profile
2. Duplicate email returns 409 Conflict
3. Invalid email returns 422 Unprocessable Entity
4. Weak password (<8 chars) returns 422 Unprocessable Entity
5. Missing required fields returns 422 Unprocessable Entity
6. Invalid role returns 422 Unprocessable Entity
7. Coach registration creates inactive user with pending approval + linked coach profile
8. Admin public registration creates inactive account with pending approval (privilege escalation prevented)
9. Inactive/pending user login is rejected (401 Account is inactive)
10. Admin can approve/activate coach, enabling successful login
"""
import pytest
from bson import ObjectId


def form_data(email: str, password: str) -> dict:
    return {"username": email, "password": password}


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_valid_athlete_registration(client, db):
    payload = {
        "full_name": "Marcus Sprint",
        "email": "marcus@athletix.dev",
        "password": "Password123!",
        "role": "athlete",
    }
    resp = await client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["email"] == "marcus@athletix.dev"
    assert data["role"] == "athlete"
    assert data["is_active"] is True
    assert data["status"] == "active"
    assert "created" in data["message"].lower()

    # Verify user exists in MongoDB with hashed password
    user = await db.users.find_one({"email": "marcus@athletix.dev"})
    assert user is not None
    assert user["is_active"] is True
    assert "hashed_password" in user
    assert user["hashed_password"] != "Password123!"

    # Verify linked athlete profile exists
    ath = await db.athletes.find_one({"user_id": user["_id"]})
    assert ath is not None
    assert ath["full_name"] == "Marcus Sprint"

    # Verify athlete can log in immediately
    login_resp = await client.post(
        "/api/v1/auth/login",
        data=form_data("marcus@athletix.dev", "Password123!"),
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    assert len(token) > 20


@pytest.mark.asyncio
async def test_duplicate_email_registration_rejected(client, db, athlete_user):
    payload = {
        "full_name": "Duplicate User",
        "email": athlete_user["email"],
        "password": "Password123!",
        "role": "athlete",
    }
    resp = await client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 409
    assert "already exists" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_invalid_email_registration_rejected(client):
    payload = {
        "full_name": "Bad Email",
        "email": "not-an-email",
        "password": "Password123!",
        "role": "athlete",
    }
    resp = await client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_weak_password_registration_rejected(client):
    payload = {
        "full_name": "Short Pass",
        "email": "short@athletix.dev",
        "password": "short",  # < 8 chars
        "role": "athlete",
    }
    resp = await client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_missing_required_fields_rejected(client):
    payload = {
        "email": "missing@athletix.dev",
        # missing full_name, password, role
    }
    resp = await client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_invalid_role_registration_rejected(client):
    payload = {
        "full_name": "Hacker",
        "email": "hacker@athletix.dev",
        "password": "Password123!",
        "role": "superuser",  # invalid
    }
    resp = await client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_coach_registration_approval_workflow(client, db):
    payload = {
        "full_name": "Coach Trevor",
        "email": "trevor@athletix.dev",
        "password": "Password123!",
        "role": "coach",
    }
    resp = await client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["email"] == "trevor@athletix.dev"
    assert data["role"] == "coach"
    assert data["is_active"] is False
    assert data["status"] == "pending_approval"
    assert "approval" in data["message"].lower()

    # Verify user exists in MongoDB and is inactive
    user = await db.users.find_one({"email": "trevor@athletix.dev"})
    assert user is not None
    assert user["is_active"] is False

    # Verify coach profile was created with pending status
    coach = await db.coaches.find_one({"user_id": user["_id"]})
    assert coach is not None
    assert coach["status"] == "pending"


@pytest.mark.asyncio
async def test_unauthorized_admin_privilege_escalation_prevented(client, db):
    payload = {
        "full_name": "Fake Admin",
        "email": "fakeadmin@athletix.dev",
        "password": "Password123!",
        "role": "admin",
    }
    resp = await client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    # Account must NOT be active
    assert data["is_active"] is False
    assert data["status"] == "pending_approval"

    # User in db must not be active
    user = await db.users.find_one({"email": "fakeadmin@athletix.dev"})
    assert user is not None
    assert user["is_active"] is False


@pytest.mark.asyncio
async def test_inactive_or_pending_user_cannot_login(client):
    # Register pending coach
    payload = {
        "full_name": "Pending Coach",
        "email": "pendingcoach@athletix.dev",
        "password": "Password123!",
        "role": "coach",
    }
    reg_resp = await client.post("/api/v1/auth/register", json=payload)
    assert reg_resp.status_code == 201

    # Attempt to log in immediately
    login_resp = await client.post(
        "/api/v1/auth/login",
        data=form_data("pendingcoach@athletix.dev", "Password123!"),
    )
    assert login_resp.status_code == 401
    assert "inactive" in login_resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_admin_can_approve_coach_and_enable_login(client, db, admin_token):
    # 1. Register coach
    payload = {
        "full_name": "Approved Coach",
        "email": "approved@athletix.dev",
        "password": "Password123!",
        "role": "coach",
    }
    reg_resp = await client.post("/api/v1/auth/register", json=payload)
    assert reg_resp.status_code == 201
    user_id = reg_resp.json()["id"]

    # 2. Admin activates user
    patch_resp = await client.patch(
        f"/api/v1/users/{user_id}/status",
        json={"is_active": True},
        headers=auth_headers(admin_token),
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["is_active"] is True

    # 3. Coach can now log in
    login_resp = await client.post(
        "/api/v1/auth/login",
        data=form_data("approved@athletix.dev", "Password123!"),
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    # 4. Coach can call /auth/me
    me_resp = await client.get("/api/v1/auth/me", headers=auth_headers(token))
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "approved@athletix.dev"
    assert me_resp.json()["role"] == "coach"
