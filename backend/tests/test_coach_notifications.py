"""
Coach Notifications Tests — Phase D.
Covers coach notification reception, triggers across athlete assignments,
tournaments, training, attendance, assessments, read status mutations,
filtering, unread counts, and strict RBAC isolation.
"""
from datetime import datetime, timezone
import pytest
from bson import ObjectId

from app.repositories.notification_repository import create_notification
from app.services.notification_service import (
    get_coach_user_ids_for_athlete,
    notify_coach_athlete_assigned,
    notify_coach_tournament_registration,
    notify_coach_tournament_result,
    notify_coach_training_session,
    notify_coach_training_cancelled,
    notify_coach_attendance,
    notify_coach_assessment,
)


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── Fixtures Setup ─────────────────────────────────────────────────────────────

async def _setup_coach_fixture(db, admin_user, coach_user, athlete_user):
    now = datetime.now(timezone.utc)

    # 1. Sport
    s_res = await db.sports.insert_one({"name": "Athletics", "is_active": True, "created_at": now})
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

    # 3. Athlete
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

    # Coach-Athlete assignment
    await db.coach_athlete_assignments.insert_one({
        "coach_id": coach_id,
        "athlete_id": athlete_id,
        "status": "active",
        "created_at": now,
    })

    return {
        "sport_id": sport_id,
        "coach_id": coach_id,
        "athlete_id": athlete_id,
    }


# ── 1. Athlete Assignment Notifications ────────────────────────────────────────

@pytest.mark.asyncio
async def test_assign_athletes_to_coach_notifies_coach(
    client, db, admin_user, coach_user, athlete_user, admin_token, coach_token
):
    fixture = await _setup_coach_fixture(db, admin_user, coach_user, athlete_user)
    coach_id = str(fixture["coach_id"])
    athlete_id = str(fixture["athlete_id"])

    # Admin assigns athlete to coach via endpoint
    resp = await client.post(
        f"/api/v1/coaches/{coach_id}/athletes",
        json={"athlete_ids": [athlete_id]},
        headers=auth_headers(admin_token),
    )
    assert resp.status_code == 200

    # Coach should have received an assignment notification
    notif_resp = await client.get("/api/v1/notifications", headers=auth_headers(coach_token))
    assert notif_resp.status_code == 200
    notifs = notif_resp.json()
    assert any(
        "New Athlete Assigned" in n["title"] and athlete_user["full_name"] in n["message"]
        for n in notifs
    )


@pytest.mark.asyncio
async def test_assign_coach_to_athlete_notifies_coach(
    client, db, admin_user, coach_user, athlete_user, admin_token, coach_token
):
    now = datetime.now(timezone.utc)
    # Create an unassigned athlete
    new_ath_user = await db.users.insert_one({
        "email": "newbie@test.com",
        "full_name": "Newbie Runner",
        "role": "athlete",
        "is_active": True,
        "created_at": now,
    })
    s_res = await db.sports.insert_one({"name": "Sprint", "is_active": True, "created_at": now})
    c_res = await db.coaches.insert_one({
        "user_id": coach_user["_id"],
        "full_name": coach_user["full_name"],
        "email": coach_user["email"],
        "sport_ids": [s_res.inserted_id],
        "status": "active",
        "created_at": now,
    })
    a_res = await db.athletes.insert_one({
        "user_id": new_ath_user.inserted_id,
        "full_name": "Newbie Runner",
        "email": "newbie@test.com",
        "sport_id": s_res.inserted_id,
        "coach_id": None,
        "status": "active",
        "created_at": now,
    })
    athlete_id = str(a_res.inserted_id)
    coach_id = str(c_res.inserted_id)

    # Assign coach via /api/v1/athletes/{id}/coach
    resp = await client.patch(
        f"/api/v1/athletes/{athlete_id}/coach",
        json={"coach_id": coach_id},
        headers=auth_headers(admin_token),
    )
    assert resp.status_code == 200

    # Coach should have received notification
    notif_resp = await client.get("/api/v1/notifications", headers=auth_headers(coach_token))
    assert notif_resp.status_code == 200
    notifs = notif_resp.json()
    assert any(
        "New Athlete Assigned" in n["title"] and "Newbie Runner" in n["message"]
        for n in notifs
    )


# ── 2. Tournament Notifications ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_tournament_registration_notifies_coach(
    client, db, admin_user, coach_user, athlete_user, admin_token, coach_token
):
    fixture = await _setup_coach_fixture(db, admin_user, coach_user, athlete_user)

    # Create tournament
    t_resp = await client.post(
        "/api/v1/tournaments",
        json={
            "name": "National Sprint Cup",
            "sport_id": str(fixture["sport_id"]),
            "start_date": "2026-12-01T09:00:00",
            "end_date": "2026-12-05T18:00:00",
            "venue": "National Stadium",
        },
        headers=auth_headers(admin_token),
    )
    assert t_resp.status_code == 201
    t_id = t_resp.json()["id"]

    # Register athlete for tournament
    reg_resp = await client.post(
        f"/api/v1/tournaments/{t_id}/participants",
        json={"athlete_id": str(fixture["athlete_id"]), "event": "100m Dash"},
        headers=auth_headers(admin_token),
    )
    assert reg_resp.status_code == 201

    # Coach should receive tournament registration notification
    notif_resp = await client.get("/api/v1/notifications", headers=auth_headers(coach_token))
    assert notif_resp.status_code == 200
    notifs = notif_resp.json()
    assert any(
        "Athlete Registered for Tournament" in n["title"] and "National Sprint Cup" in n["message"]
        for n in notifs
    )


@pytest.mark.asyncio
async def test_tournament_result_notifies_coach(
    client, db, admin_user, coach_user, athlete_user, admin_token, coach_token
):
    fixture = await _setup_coach_fixture(db, admin_user, coach_user, athlete_user)

    # Create tournament & register
    t_resp = await client.post(
        "/api/v1/tournaments",
        json={
            "name": "Summer Track Meet",
            "sport_id": str(fixture["sport_id"]),
            "start_date": "2026-07-10T09:00:00",
            "end_date": "2026-07-12T18:00:00",
        },
        headers=auth_headers(admin_token),
    )
    t_id = t_resp.json()["id"]
    await client.post(
        f"/api/v1/tournaments/{t_id}/participants",
        json={"athlete_id": str(fixture["athlete_id"])},
        headers=auth_headers(admin_token),
    )

    # Record result
    res_resp = await client.post(
        f"/api/v1/tournaments/{t_id}/results",
        json={
            "athlete_id": str(fixture["athlete_id"]),
            "position": 1,
            "medal": "gold",
            "points": 10,
        },
        headers=auth_headers(admin_token),
    )
    assert res_resp.status_code == 200

    # Coach should receive result notification
    notif_resp = await client.get("/api/v1/notifications", headers=auth_headers(coach_token))
    assert notif_resp.status_code == 200
    notifs = notif_resp.json()
    assert any(
        "Athlete Tournament Result" in n["title"] and "Summer Track Meet" in n["message"]
        for n in notifs
    )


# ── 3. Training & Attendance Notifications ─────────────────────────────────────

@pytest.mark.asyncio
async def test_training_session_scheduled_notifies_coach(
    client, db, admin_user, coach_user, athlete_user, admin_token, coach_token
):
    fixture = await _setup_coach_fixture(db, admin_user, coach_user, athlete_user)

    # Admin creates training session assigned to coach
    payload = {
        "title": "Morning Endurance Session",
        "sport_id": str(fixture["sport_id"]),
        "coach_id": str(fixture["coach_id"]),
        "session_date": "2026-11-20T08:00:00",
        "start_time": "08:00",
        "end_time": "10:00",
        "athlete_ids": [str(fixture["athlete_id"])],
        "location": "Main Track",
    }
    resp = await client.post("/api/v1/training/sessions", json=payload, headers=auth_headers(admin_token))
    assert resp.status_code == 201

    # Coach should have a notification
    notif_resp = await client.get("/api/v1/notifications", headers=auth_headers(coach_token))
    assert notif_resp.status_code == 200
    notifs = notif_resp.json()
    assert any("Morning Endurance Session" in n["message"] for n in notifs)


@pytest.mark.asyncio
async def test_training_session_cancellation_notifies_coach(
    client, db, admin_user, coach_user, athlete_user, admin_token, coach_token
):
    fixture = await _setup_coach_fixture(db, admin_user, coach_user, athlete_user)

    s_doc = await db.training_sessions.insert_one({
        "title": "Evening Sprints",
        "sport_id": fixture["sport_id"],
        "coach_id": fixture["coach_id"],
        "session_date": datetime(2026, 11, 22, 17, 0),
        "athlete_ids": [fixture["athlete_id"]],
        "status": "scheduled",
    })
    session_id = str(s_doc.inserted_id)

    # Admin cancels session
    cancel_resp = await client.patch(
        f"/api/v1/training/sessions/{session_id}/status",
        json={"status": "cancelled"},
        headers=auth_headers(admin_token),
    )
    assert cancel_resp.status_code == 200

    # Coach should have cancellation notification
    notif_resp = await client.get("/api/v1/notifications", headers=auth_headers(coach_token))
    assert notif_resp.status_code == 200
    notifs = notif_resp.json()
    assert any("Evening Sprints" in n["message"] and "cancelled" in n["message"].lower() for n in notifs)


@pytest.mark.asyncio
async def test_attendance_recorded_notifies_coach(
    client, db, admin_user, coach_user, athlete_user, admin_token, coach_token
):
    fixture = await _setup_coach_fixture(db, admin_user, coach_user, athlete_user)

    s_doc = await db.training_sessions.insert_one({
        "title": "Agility Drill",
        "sport_id": fixture["sport_id"],
        "coach_id": fixture["coach_id"],
        "session_date": datetime(2026, 11, 25, 9, 0),
        "athlete_ids": [fixture["athlete_id"]],
        "status": "completed",
    })
    session_id = str(s_doc.inserted_id)

    # Admin marks attendance
    rec_resp = await client.post(
        f"/api/v1/training/sessions/{session_id}/attendance",
        json={"athlete_id": str(fixture["athlete_id"]), "status": "present", "remarks": "Excellent effort"},
        headers=auth_headers(admin_token),
    )
    assert rec_resp.status_code == 200

    # Coach receives attendance notification
    notif_resp = await client.get("/api/v1/notifications", headers=auth_headers(coach_token))
    assert notif_resp.status_code == 200
    notifs = notif_resp.json()
    assert any("Athlete Attendance Update" in n["title"] for n in notifs)


# ── 4. Performance Assessment Notifications ────────────────────────────────────

@pytest.mark.asyncio
async def test_assessment_created_by_admin_notifies_coach(
    client, db, admin_user, coach_user, athlete_user, admin_token, coach_token
):
    fixture = await _setup_coach_fixture(db, admin_user, coach_user, athlete_user)

    # Admin creates an assessment for the coach's athlete
    assess_payload = {
        "athlete_id": str(fixture["athlete_id"]),
        "sport_id": str(fixture["sport_id"]),
        "metrics": {"speed": 88.0, "stamina": 92.0},
        "remarks": "Strong endurance test",
    }
    resp = await client.post("/api/v1/assessments", json=assess_payload, headers=auth_headers(admin_token))
    assert resp.status_code == 201

    # Coach should receive notification of the assessment
    notif_resp = await client.get("/api/v1/notifications", headers=auth_headers(coach_token))
    assert notif_resp.status_code == 200
    notifs = notif_resp.json()
    assert any(
        "Athlete Assessment Recorded" in n["title"] and athlete_user["full_name"] in n["message"]
        for n in notifs
    )


# ── 5. Status Mutations, Filtering & RBAC Isolation ────────────────────────────

@pytest.mark.asyncio
async def test_coach_can_mark_notifications_read_and_all_read(
    client, db, coach_user, coach_token
):
    c_uid = str(coach_user["_id"])
    n1 = await create_notification(db, recipient_user_id=c_uid, title="Coach N1", message="Msg 1")
    n2 = await create_notification(db, recipient_user_id=c_uid, title="Coach N2", message="Msg 2")

    # Check unread count is 2
    count_resp = await client.get("/api/v1/notifications/unread-count", headers=auth_headers(coach_token))
    assert count_resp.status_code == 200
    assert count_resp.json()["unread_count"] == 2

    # Mark n1 as read
    patch_resp = await client.patch(
        f"/api/v1/notifications/{str(n1['_id'])}/read",
        headers=auth_headers(coach_token),
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["is_read"] is True

    # Unread count should now be 1
    count_resp2 = await client.get("/api/v1/notifications/unread-count", headers=auth_headers(coach_token))
    assert count_resp2.json()["unread_count"] == 1

    # Mark all read
    all_resp = await client.patch("/api/v1/notifications/read-all", headers=auth_headers(coach_token))
    assert all_resp.status_code == 200
    assert all_resp.json()["updated_count"] == 1

    # Unread count should now be 0
    count_resp3 = await client.get("/api/v1/notifications/unread-count", headers=auth_headers(coach_token))
    assert count_resp3.json()["unread_count"] == 0


@pytest.mark.asyncio
async def test_coach_and_athlete_strict_notification_isolation(
    client, db, coach_user, athlete_user, coach_token, athlete_token
):
    c_uid = str(coach_user["_id"])
    a_uid = str(athlete_user["_id"])

    # Create coach-only notification
    c_notif = await create_notification(
        db, recipient_user_id=c_uid, title="Coach Strategy", message="Confidential coaching plan"
    )
    # Create athlete-only notification
    a_notif = await create_notification(
        db, recipient_user_id=a_uid, title="Athlete Plan", message="Personal training routine"
    )

    # Coach should see coach notification but NOT athlete notification
    c_resp = await client.get("/api/v1/notifications", headers=auth_headers(coach_token))
    assert c_resp.status_code == 200
    c_items = c_resp.json()
    assert any(n["id"] == str(c_notif["_id"]) for n in c_items)
    assert not any(n["id"] == str(a_notif["_id"]) for n in c_items)

    # Athlete should see athlete notification but NOT coach notification
    a_resp = await client.get("/api/v1/notifications", headers=auth_headers(athlete_token))
    assert a_resp.status_code == 200
    a_items = a_resp.json()
    assert any(n["id"] == str(a_notif["_id"]) for n in a_items)
    assert not any(n["id"] == str(c_notif["_id"]) for n in a_items)

    # Athlete cannot mark coach notification as read
    cross_read = await client.patch(
        f"/api/v1/notifications/{str(c_notif['_id'])}/read",
        headers=auth_headers(athlete_token),
    )
    assert cross_read.status_code == 403

    # Coach cannot delete athlete notification
    cross_delete = await client.delete(
        f"/api/v1/notifications/{str(a_notif['_id'])}",
        headers=auth_headers(coach_token),
    )
    assert cross_delete.status_code == 403


@pytest.mark.asyncio
async def test_coach_notifications_support_string_and_oid_user_ids(
    client, db, coach_user, coach_token
):
    c_uid = str(coach_user["_id"])
    now = datetime.now(timezone.utc)
    # Insert notification with string user_id and recipient_user_id
    doc_str = {
        "recipient_user_id": c_uid,
        "user_id": c_uid,
        "type": "general",
        "title": "String ID Notice",
        "message": "Notification with string ID",
        "is_read": False,
        "created_at": now,
    }
    await db.notifications.insert_one(doc_str)

    resp = await client.get("/api/v1/notifications", headers=auth_headers(coach_token))
    assert resp.status_code == 200
    items = resp.json()
    assert any(n["title"] == "String ID Notice" for n in items)

    count_resp = await client.get("/api/v1/notifications/unread-count", headers=auth_headers(coach_token))
    assert count_resp.status_code == 200
    assert count_resp.json()["unread_count"] >= 1
