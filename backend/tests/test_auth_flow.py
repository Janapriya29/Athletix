"""
Phase F1 Tests: Fix Registration and Login for All Users.
Verifies complete authentication and registration lifecycle:
1. Newly registered Athlete can log in immediately.
2. Newly registered Coach can log in once approved by Admin.
3. Authorized Admin account creation allows login.
4. Existing seeded accounts continue to authenticate.
5. Incorrect passwords and unknown emails are rejected with timing-safe error.
6. Duplicate registrations are rejected.
7. Email case and surrounding whitespace are handled consistently.
8. Role-based authorization still prevents unauthorized access.
9. Passwords remain hashed in MongoDB (no plaintext stored).
10. Example scenario (ananthika@gmail.com / ananthika) authenticates subject to approval requirements.
"""
from datetime import datetime, timezone
import bcrypt
import pytest
from bson import ObjectId


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def form_data(email: str, password: str) -> dict:
    return {"username": email, "password": password}


@pytest.mark.asyncio
async def test_newly_registered_athlete_can_login(client, db):
    payload = {
        "full_name": "New Athlete User",
        "email": "newathlete.flow@athletix.dev",
        "password": "Password123!",
        "role": "athlete",
    }
    reg_resp = await client.post("/api/v1/auth/register", json=payload)
    assert reg_resp.status_code == 201
    reg_data = reg_resp.json()
    assert reg_data["email"] == "newathlete.flow@athletix.dev"
    assert reg_data["role"] == "athlete"
    assert reg_data["is_active"] is True

    # Verify user exists in MongoDB with hashed password
    user_doc = await db.users.find_one({"email": "newathlete.flow@athletix.dev"})
    assert user_doc is not None
    assert user_doc["is_active"] is True
    assert user_doc["hashed_password"] != "Password123!"
    assert bcrypt.checkpw(b"Password123!", user_doc["hashed_password"].encode("utf-8"))

    # Linked athlete profile
    ath_doc = await db.athletes.find_one({"user_id": user_doc["_id"]})
    assert ath_doc is not None
    assert ath_doc["full_name"] == "New Athlete User"

    # Login immediately
    login_resp = await client.post(
        "/api/v1/auth/login",
        data=form_data("newathlete.flow@athletix.dev", "Password123!"),
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    assert len(token) > 20

    # Call /auth/me
    me_resp = await client.get("/api/v1/auth/me", headers=auth_headers(token))
    assert me_resp.status_code == 200
    assert me_resp.json()["role"] == "athlete"
    assert me_resp.json()["email"] == "newathlete.flow@athletix.dev"


@pytest.mark.asyncio
async def test_newly_registered_coach_approval_and_login(client, db, admin_token):
    payload = {
        "full_name": "New Coach User",
        "email": "newcoach.flow@athletix.dev",
        "password": "Password123!",
        "role": "coach",
    }
    reg_resp = await client.post("/api/v1/auth/register", json=payload)
    assert reg_resp.status_code == 201
    coach_user_id = reg_resp.json()["id"]

    # Inactive pending approval: login must fail
    unapproved_login = await client.post(
        "/api/v1/auth/login",
        data=form_data("newcoach.flow@athletix.dev", "Password123!"),
    )
    assert unapproved_login.status_code == 401
    assert "inactive" in unapproved_login.json()["detail"].lower()

    # Admin approves/activates coach
    patch_resp = await client.patch(
        f"/api/v1/users/{coach_user_id}/status",
        json={"is_active": True},
        headers=auth_headers(admin_token),
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["is_active"] is True

    # Now coach can log in
    approved_login = await client.post(
        "/api/v1/auth/login",
        data=form_data("newcoach.flow@athletix.dev", "Password123!"),
    )
    assert approved_login.status_code == 200
    token = approved_login.json()["access_token"]

    # Verify coach profile
    me_resp = await client.get("/api/v1/auth/me", headers=auth_headers(token))
    assert me_resp.status_code == 200
    assert me_resp.json()["role"] == "coach"


@pytest.mark.asyncio
async def test_admin_created_through_authorized_process_can_login(client, db, admin_token):
    # Admin creates another admin through authorized endpoint
    create_payload = {
        "full_name": "New Academy Admin",
        "email": "newadmin.flow@athletix.dev",
        "password": "Password123!",
        "role": "admin",
    }
    create_resp = await client.post(
        "/api/v1/users",
        json=create_payload,
        headers=auth_headers(admin_token),
    )
    assert create_resp.status_code == 201
    assert create_resp.json()["role"] == "admin"

    # New admin can log in
    login_resp = await client.post(
        "/api/v1/auth/login",
        data=form_data("newadmin.flow@athletix.dev", "Password123!"),
    )
    assert login_resp.status_code == 200
    new_admin_token = login_resp.json()["access_token"]

    # New admin has full admin privileges
    users_resp = await client.get("/api/v1/users", headers=auth_headers(new_admin_token))
    assert users_resp.status_code == 200
    assert isinstance(users_resp.json(), list)


@pytest.mark.asyncio
async def test_existing_seeded_account_login_works(client, admin_user):
    resp = await client.post(
        "/api/v1/auth/login",
        data=form_data("admin@test.com", "Admin@test123"),
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_incorrect_passwords_and_unknown_emails_rejected(client, admin_user):
    # Incorrect password
    wrong_pass_resp = await client.post(
        "/api/v1/auth/login",
        data=form_data("admin@test.com", "WrongPassword!"),
    )
    assert wrong_pass_resp.status_code == 401
    assert "Invalid email or password" in wrong_pass_resp.json()["detail"]

    # Unknown email
    unknown_email_resp = await client.post(
        "/api/v1/auth/login",
        data=form_data("nonexistent@athletix.dev", "Password123!"),
    )
    assert unknown_email_resp.status_code == 401
    assert "Invalid email or password" in unknown_email_resp.json()["detail"]


@pytest.mark.asyncio
async def test_duplicate_registrations_rejected(client, db):
    payload = {
        "full_name": "First Athlete",
        "email": "unique.athlete@athletix.dev",
        "password": "Password123!",
        "role": "athlete",
    }
    r1 = await client.post("/api/v1/auth/register", json=payload)
    assert r1.status_code == 201

    # Attempt second registration with same email
    r2 = await client.post("/api/v1/auth/register", json=payload)
    assert r2.status_code == 409
    assert "already exists" in r2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_email_case_and_whitespace_handled_consistently(client, db):
    payload = {
        "full_name": "Case Test User",
        "email": "  Whitespace.Case@Athletix.Dev  ",
        "password": "Password123!",
        "role": "athlete",
    }
    reg_resp = await client.post("/api/v1/auth/register", json=payload)
    assert reg_resp.status_code == 201
    assert reg_resp.json()["email"] == "whitespace.case@athletix.dev"

    # User in db stored cleanly lowercased
    user_doc = await db.users.find_one({"email": "whitespace.case@athletix.dev"})
    assert user_doc is not None

    # Login with all uppercase
    login_upper = await client.post(
        "/api/v1/auth/login",
        data=form_data("WHITESPACE.CASE@ATHLETIX.DEV", "Password123!"),
    )
    assert login_upper.status_code == 200

    # Login with leading/trailing spaces
    login_spaces = await client.post(
        "/api/v1/auth/login",
        data=form_data("  whitespace.case@athletix.dev  ", "Password123!"),
    )
    assert login_spaces.status_code == 200


@pytest.mark.asyncio
async def test_role_based_authorization_enforced(client, athlete_token, coach_token, admin_token):
    # Athlete denied admin route
    r_ath = await client.get("/api/v1/users", headers=auth_headers(athlete_token))
    assert r_ath.status_code == 403

    # Coach denied admin route
    r_coach = await client.get("/api/v1/users", headers=auth_headers(coach_token))
    assert r_coach.status_code == 403

    # Admin permitted
    r_admin = await client.get("/api/v1/users", headers=auth_headers(admin_token))
    assert r_admin.status_code == 200


@pytest.mark.asyncio
async def test_passwords_remain_hashed_in_mongodb(client, db):
    payload = {
        "full_name": "Plaintext Check",
        "email": "plaintext.check@athletix.dev",
        "password": "SuperSecretPass123!",
        "role": "athlete",
    }
    reg_resp = await client.post("/api/v1/auth/register", json=payload)
    assert reg_resp.status_code == 201

    doc = await db.users.find_one({"email": "plaintext.check@athletix.dev"})
    assert "password" not in doc
    assert "plain_password" not in doc
    assert "hashed_password" in doc
    assert doc["hashed_password"] != "SuperSecretPass123!"
    assert doc["hashed_password"].startswith("$2b$")


@pytest.mark.asyncio
async def test_ananthika_example_authentication_flow(client, db, admin_token):
    """
    Direct test of the user's example:
    - Email: ananthika@gmail.com
    - Password: ananthika
    Account must authenticate successfully, subject to activation / approval requirements.
    """
    # Register ananthika as coach (requires approval)
    reg_payload = {
        "full_name": "Ananthika Example",
        "email": "ananthika.test@gmail.com",
        "password": "ananthika",
        "role": "coach",
    }
    reg_resp = await client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_resp.status_code == 201
    user_id = reg_resp.json()["id"]

    # 1. Unapproved login attempt: credentials authenticate, but status check rejects
    unapproved_login = await client.post(
        "/api/v1/auth/login",
        data=form_data("ananthika.test@gmail.com", "ananthika"),
    )
    assert unapproved_login.status_code == 401
    assert "inactive" in unapproved_login.json()["detail"].lower()

    # 2. Wrong password on inactive account is still rejected for bad credentials
    wrong_pass_login = await client.post(
        "/api/v1/auth/login",
        data=form_data("ananthika.test@gmail.com", "wrongpassword"),
    )
    assert wrong_pass_login.status_code == 401
    assert "Invalid email or password" in wrong_pass_login.json()["detail"]

    # 3. Administrator approves the account
    patch_resp = await client.patch(
        f"/api/v1/users/{user_id}/status",
        json={"is_active": True},
        headers=auth_headers(admin_token),
    )
    assert patch_resp.status_code == 200

    # 4. Once approved, credentials authenticate and return token
    success_login = await client.post(
        "/api/v1/auth/login",
        data=form_data("ananthika.test@gmail.com", "ananthika"),
    )
    assert success_login.status_code == 200
    token = success_login.json()["access_token"]
    assert len(token) > 20

    # 5. Token is valid for authenticated endpoints
    me_resp = await client.get("/api/v1/auth/me", headers=auth_headers(token))
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "ananthika.test@gmail.com"


@pytest.mark.asyncio
async def test_approach_c_admin_creation_and_authorization(client, db, admin_token, coach_token, athlete_token):
    """
    Verifies Approach C requirements:
    1. Authorized Admin can create additional Admin accounts with arbitrary credentials.
    2. Newly created Admin account is stored with bcrypt hashed password, is_active=True, role="admin".
    3. New Admin can immediately log in with their registered credentials and access Admin routes.
    4. Non-admins (Coach, Athlete) cannot create Admin accounts.
    """
    # 1. Non-admin cannot create Admin account
    new_admin_payload = {
        "full_name": "Second Academy Admin",
        "email": "second.admin@athletix.dev",
        "password": "SecondAdminPass123!",
        "role": "admin",
    }
    r_unauth_ath = await client.post("/api/v1/users", json=new_admin_payload, headers=auth_headers(athlete_token))
    assert r_unauth_ath.status_code == 403

    r_unauth_coach = await client.post("/api/v1/users", json=new_admin_payload, headers=auth_headers(coach_token))
    assert r_unauth_coach.status_code == 403

    # 2. Authorized Admin creates additional Admin account
    r_create = await client.post("/api/v1/users", json=new_admin_payload, headers=auth_headers(admin_token))
    assert r_create.status_code == 201
    created_data = r_create.json()
    assert created_data["email"] == "second.admin@athletix.dev"
    assert created_data["role"] == "admin"
    assert created_data["is_active"] is True

    # 3. Check MongoDB storage: password hashed, active status
    user_doc = await db.users.find_one({"email": "second.admin@athletix.dev"})
    assert user_doc is not None
    assert user_doc["role"] == "admin"
    assert user_doc["is_active"] is True
    assert user_doc["status"] == "active"
    assert "password" not in user_doc
    assert bcrypt.checkpw(b"SecondAdminPass123!", user_doc["hashed_password"].encode("utf-8"))

    # 4. Newly created Admin can log in immediately
    login_resp = await client.post(
        "/api/v1/auth/login",
        data=form_data("second.admin@athletix.dev", "SecondAdminPass123!"),
    )
    assert login_resp.status_code == 200
    new_admin_token = login_resp.json()["access_token"]
    assert len(new_admin_token) > 20

    # 5. New Admin has full Admin authorization on protected routes
    users_resp = await client.get("/api/v1/users", headers=auth_headers(new_admin_token))
    assert users_resp.status_code == 200
    assert any(u["email"] == "second.admin@athletix.dev" for u in users_resp.json())
