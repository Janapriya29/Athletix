"""
Authentication tests — Phase 1.

Tests 1–14 from the specification. All run against a real MongoDB
test database (athletix_test). No mocking of auth logic.
"""
import pytest
from datetime import timedelta


# ── Helper ─────────────────────────────────────────────────────────────────────

def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def form_data(email: str, password: str) -> dict:
    return {"username": email, "password": password}


# ── 1. Valid login ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_login_valid(client, admin_user):
    resp = await client.post("/api/v1/auth/login", data=form_data("admin@test.com", "Admin@test123"))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"
    assert len(body["access_token"]) > 20


# ── 2. Wrong password ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_login_wrong_password(client, admin_user):
    resp = await client.post("/api/v1/auth/login", data=form_data("admin@test.com", "WrongPassword!"))
    assert resp.status_code == 401
    assert "Invalid" in resp.json()["detail"]


# ── 3. Unknown email ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_login_unknown_email(client, db):
    resp = await client.post("/api/v1/auth/login", data=form_data("nobody@test.com", "SomePass@123"))
    assert resp.status_code == 401


# ── 4. Missing credentials ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_login_missing_credentials(client):
    # No body at all
    resp = await client.post("/api/v1/auth/login", data={})
    assert resp.status_code == 422  # FastAPI validation error


# ── 5. GET /me with valid token ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_me_valid_token(client, admin_user, admin_token):
    resp = await client.get("/api/v1/auth/me", headers=auth_headers(admin_token))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["email"] == "admin@test.com"
    assert body["role"] == "admin"
    assert "hashed_password" not in body
    assert "id" in body


# ── 6. GET /me without token ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_me_no_token(client):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


# ── 7. Invalid JWT ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_me_invalid_token(client):
    resp = await client.get("/api/v1/auth/me", headers=auth_headers("not.a.real.token"))
    assert resp.status_code == 401


# ── 8. Expired token ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_me_expired_token(client, admin_user):
    from app.core.security import create_access_token
    expired = create_access_token(
        data={"sub": str(admin_user["_id"]), "role": "admin", "email": "admin@test.com"},
        expires_delta=timedelta(seconds=-1),  # already expired
    )
    resp = await client.get("/api/v1/auth/me", headers=auth_headers(expired))
    assert resp.status_code == 401


# ── 9. Admin role can access admin-only endpoint ───────────────────────────────

@pytest.mark.asyncio
async def test_admin_can_list_users(client, admin_user, admin_token):
    resp = await client.get("/api/v1/users", headers=auth_headers(admin_token))
    assert resp.status_code == 200
    users = resp.json()
    assert isinstance(users, list)
    assert any(u["email"] == "admin@test.com" for u in users)


# ── 10. Coach denied from admin-only endpoint ──────────────────────────────────

@pytest.mark.asyncio
async def test_coach_denied_admin_endpoint(client, coach_user, coach_token):
    resp = await client.get("/api/v1/users", headers=auth_headers(coach_token))
    assert resp.status_code == 403


# ── 11. Athlete denied from admin-only endpoint ────────────────────────────────

@pytest.mark.asyncio
async def test_athlete_denied_admin_endpoint(client, athlete_user, athlete_token):
    resp = await client.get("/api/v1/users", headers=auth_headers(athlete_token))
    assert resp.status_code == 403


# ── 12. Athlete cannot access another athlete's user record ────────────────────

@pytest.mark.asyncio
async def test_athlete_cannot_access_other_user(client, db, athlete_user, athlete_token):
    from tests.conftest import _create_test_user
    other = await _create_test_user(db, "other@test.com", "Other@pass123", "athlete")
    other_id = str(other["_id"])
    resp = await client.get(f"/api/v1/users/{other_id}", headers=auth_headers(athlete_token))
    assert resp.status_code == 403


# ── 13. Change password — correct current password ─────────────────────────────

@pytest.mark.asyncio
async def test_change_password_success(client, admin_user, admin_token):
    resp = await client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "Admin@test123", "new_password": "NewAdmin@456"},
        headers=auth_headers(admin_token),
    )
    assert resp.status_code == 200
    assert "updated" in resp.json()["message"].lower()

    # Verify old password no longer works
    resp2 = await client.post("/api/v1/auth/login", data=form_data("admin@test.com", "Admin@test123"))
    assert resp2.status_code == 401

    # Verify new password works
    resp3 = await client.post("/api/v1/auth/login", data=form_data("admin@test.com", "NewAdmin@456"))
    assert resp3.status_code == 200


# ── 14. Change password — wrong current password ───────────────────────────────

@pytest.mark.asyncio
async def test_change_password_wrong_current(client, admin_user, admin_token):
    resp = await client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "WrongPassword!", "new_password": "NewAdmin@456"},
        headers=auth_headers(admin_token),
    )
    assert resp.status_code == 400
    assert "incorrect" in resp.json()["detail"].lower()


# ── 15. Inactive user cannot log in ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_inactive_user_cannot_login(client, inactive_user):
    resp = await client.post("/api/v1/auth/login", data=form_data("inactive@test.com", "Inactive@test123"))
    assert resp.status_code == 401
    assert "inactive" in resp.json()["detail"].lower()


# ── 16. Logout returns success for authenticated user ──────────────────────────

@pytest.mark.asyncio
async def test_logout_authenticated(client, admin_user, admin_token):
    resp = await client.post("/api/v1/auth/logout", headers=auth_headers(admin_token))
    assert resp.status_code == 200
    assert "Logged out" in resp.json()["message"]


# ── 17. Logout requires authentication ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_logout_unauthenticated(client):
    resp = await client.post("/api/v1/auth/logout")
    assert resp.status_code == 401


# ── Phase G Security Regressions: Inactive & Stale Token Gating ────────────────

@pytest.mark.asyncio
async def test_inactive_user_token_blocked_from_protected_apis(client, inactive_user):
    from app.core.security import create_access_token
    token = create_access_token({
        "sub": str(inactive_user["_id"]),
        "role": inactive_user["role"],
        "email": inactive_user["email"],
    })
    resp = await client.get("/api/v1/auth/me", headers=auth_headers(token))
    assert resp.status_code == 401
    assert "inactive" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_dynamically_deactivated_user_token_immediately_revoked(
    client, db, athlete_user, athlete_token
):
    # Verify active token works initially
    resp = await client.get("/api/v1/auth/me", headers=auth_headers(athlete_token))
    assert resp.status_code == 200

    # Deactivate user in database
    await db.users.update_one(
        {"_id": athlete_user["_id"]},
        {"$set": {"is_active": False, "status": "inactive"}},
    )

    # Pre-existing token must be rejected immediately
    revoked_resp = await client.get("/api/v1/auth/me", headers=auth_headers(athlete_token))
    assert revoked_resp.status_code == 401
    assert "inactive" in revoked_resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_pending_approval_user_token_blocked(client, db):
    from datetime import datetime, timezone
    from app.core.security import create_access_token, hash_password
    now = datetime.now(timezone.utc)
    res = await db.users.insert_one({
        "email": "pending_coach@test.com",
        "full_name": "Pending Coach",
        "hashed_password": hash_password("CoachPassword123"),
        "role": "coach",
        "is_active": False,
        "status": "pending_approval",
        "created_at": now,
        "updated_at": now,
    })
    token = create_access_token({
        "sub": str(res.inserted_id),
        "role": "coach",
        "email": "pending_coach@test.com",
    })

    resp = await client.get("/api/v1/auth/me", headers=auth_headers(token))
    assert resp.status_code == 401
    assert "inactive" in resp.json()["detail"].lower() or "pending" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_nonexistent_user_token_rejected(client):
    from app.core.security import create_access_token
    fake_token = create_access_token({
        "sub": "507f1f77bcf86cd799439011",
        "role": "athlete",
        "email": "ghost@test.com",
    })
    resp = await client.get("/api/v1/auth/me", headers=auth_headers(fake_token))
    assert resp.status_code == 401
    assert "does not exist" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_malformed_user_id_in_token_rejected(client):
    from app.core.security import create_access_token
    bad_id_token = create_access_token({
        "sub": "not-a-valid-object-id-12345",
        "role": "athlete",
        "email": "badid@test.com",
    })
    resp = await client.get("/api/v1/auth/me", headers=auth_headers(bad_id_token))
    assert resp.status_code == 401
    assert "invalid" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_invalid_email_timing_mitigation(client):
    resp = await client.post(
        "/api/v1/auth/login",
        data=form_data("nonexistent_user_never_registered@test.com", "SomePassword123"),
    )
    assert resp.status_code == 401
    assert "invalid email or password" in resp.json()["detail"].lower()

