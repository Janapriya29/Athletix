"""
Notifications tests — Phase 7.
Covers in-app notification flows, triggers, queries, mutations, RBAC, and duplicate prevention.
"""
from datetime import datetime, timezone
import pytest
from bson import ObjectId

from app.repositories.notification_repository import create_notification
from app.services.notification_service import (
    notify_assessment_created,
    notify_attendance_recorded,
    notify_training_cancelled,
    notify_training_created,
    notify_tournament_registration,
    notify_tournament_result,
)


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── Fixtures Setup ─────────────────────────────────────────────────────────────

async def _setup_notif_fixture(db, admin_user, coach_user, athlete_user):
    now = datetime.now(timezone.utc)

    # 1. Sport
    s_res = await db.sports.insert_one({"name": "Football", "is_active": True, "created_at": now})
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


# ── 1. Event Triggers ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_training_session_creation_notifies_participants(
    client, db, admin_user, coach_user, athlete_user, coach_token, athlete_token
):
    fixture = await _setup_notif_fixture(db, admin_user, coach_user, athlete_user)

    # Create training session
    payload = {
        "title": "Tactical Drill",
        "sport_id": str(fixture["sport_id"]),
        "coach_id": str(fixture["coach_id"]),
        "session_date": "2026-11-10T10:00:00",
        "start_time": "10:00",
        "end_time": "12:00",
        "athlete_ids": [str(fixture["athlete_id"])],
        "location": "Pitch 1",
    }
    resp = await client.post("/api/v1/training/sessions", json=payload, headers=auth_headers(coach_token))
    assert resp.status_code == 201

    # Athlete should have a notification
    res_notif = await client.get("/api/v1/notifications", headers=auth_headers(athlete_token))
    assert res_notif.status_code == 200
    notifs = res_notif.json()
    assert len(notifs) >= 1
    assert any("Tactical Drill" in n["title"] or "Training Session Scheduled" in n["title"] for n in notifs)
    assert notifs[0]["type"] == "training"


@pytest.mark.asyncio
async def test_training_session_cancellation_notifies_participants(
    client, db, admin_user, coach_user, athlete_user, coach_token, athlete_token
):
    fixture = await _setup_notif_fixture(db, admin_user, coach_user, athlete_user)

    # Create session directly
    s_doc = await db.training_sessions.insert_one({
        "title": "Speed Drill",
        "sport_id": fixture["sport_id"],
        "coach_id": fixture["coach_id"],
        "session_date": datetime(2026, 11, 15, 10, 0),
        "athlete_ids": [fixture["athlete_id"]],
        "status": "scheduled",
    })
    session_id = str(s_doc.inserted_id)

    # Cancel session
    cancel_resp = await client.patch(
        f"/api/v1/training/sessions/{session_id}/status",
        json={"status": "cancelled"},
        headers=auth_headers(coach_token),
    )
    assert cancel_resp.status_code == 200

    # Athlete should have cancellation notification
    res_notif = await client.get("/api/v1/notifications", headers=auth_headers(athlete_token))
    assert res_notif.status_code == 200
    notifs = res_notif.json()
    assert any("Cancelled" in n["title"] for n in notifs)


@pytest.mark.asyncio
async def test_attendance_recorded_notifies_athlete(
    client, db, admin_user, coach_user, athlete_user, coach_token, athlete_token
):
    fixture = await _setup_notif_fixture(db, admin_user, coach_user, athlete_user)

    s_doc = await db.training_sessions.insert_one({
        "title": "Morning Fitness",
        "sport_id": fixture["sport_id"],
        "coach_id": fixture["coach_id"],
        "session_date": datetime(2026, 11, 12, 8, 0),
        "athlete_ids": [fixture["athlete_id"]],
        "status": "completed",
    })
    session_id = str(s_doc.inserted_id)

    # Record attendance
    rec_resp = await client.post(
        f"/api/v1/training/sessions/{session_id}/attendance",
        json={"athlete_id": str(fixture["athlete_id"]), "status": "present", "remarks": "On time"},
        headers=auth_headers(coach_token),
    )
    assert rec_resp.status_code == 200

    # Verify notification received
    res_notif = await client.get("/api/v1/notifications", headers=auth_headers(athlete_token))
    assert res_notif.status_code == 200
    notifs = res_notif.json()
    assert any("Attendance Recorded" in n["title"] for n in notifs)


@pytest.mark.asyncio
async def test_assessment_created_notifies_athlete(
    client, db, admin_user, coach_user, athlete_user, athlete_token
):
    fixture = await _setup_notif_fixture(db, admin_user, coach_user, athlete_user)

    # Directly trigger notify_assessment_created
    await notify_assessment_created(
        db,
        athlete_user_id=str(athlete_user["_id"]),
        overall_score=85.5,
        assessment_id="test_assessment_1",
    )

    res_notif = await client.get("/api/v1/notifications", headers=auth_headers(athlete_token))
    assert res_notif.status_code == 200
    notifs = res_notif.json()
    assert len(notifs) == 1
    assert notifs[0]["type"] == "performance"
    assert "85.5" in notifs[0]["message"]


@pytest.mark.asyncio
async def test_tournament_registration_notifies_athlete(
    client, db, admin_user, coach_user, athlete_user, admin_token, athlete_token
):
    fixture = await _setup_notif_fixture(db, admin_user, coach_user, athlete_user)

    # Create tournament
    t_resp = await client.post(
        "/api/v1/tournaments",
        json={
            "name": "State Championship 2026",
            "sport_id": str(fixture["sport_id"]),
            "start_date": "2026-12-01T09:00:00",
            "end_date": "2026-12-05T18:00:00",
            "venue": "City Stadium",
        },
        headers=auth_headers(admin_token),
    )
    assert t_resp.status_code == 201
    t_id = t_resp.json()["id"]

    # Register athlete
    reg_resp = await client.post(
        f"/api/v1/tournaments/{t_id}/participants",
        json={"athlete_id": str(fixture["athlete_id"]), "event": "Singles"},
        headers=auth_headers(admin_token),
    )
    assert reg_resp.status_code == 201

    # Check athlete received notification
    res_notif = await client.get("/api/v1/notifications", headers=auth_headers(athlete_token))
    assert res_notif.status_code == 200
    notifs = res_notif.json()
    assert any("State Championship 2026" in n["message"] for n in notifs)


@pytest.mark.asyncio
async def test_tournament_result_notifies_athlete(
    client, db, admin_user, coach_user, athlete_user, admin_token, athlete_token
):
    fixture = await _setup_notif_fixture(db, admin_user, coach_user, athlete_user)

    # Create tournament & register
    t_resp = await client.post(
        "/api/v1/tournaments",
        json={
            "name": "Winter Open 2026",
            "sport_id": str(fixture["sport_id"]),
            "start_date": "2026-12-10T09:00:00",
            "end_date": "2026-12-12T18:00:00",
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
        json={"athlete_id": str(fixture["athlete_id"]), "position": 1, "medal": "gold", "points": 100},
        headers=auth_headers(admin_token),
    )
    assert res_resp.status_code == 200

    # Verify notification
    res_notif = await client.get("/api/v1/notifications", headers=auth_headers(athlete_token))
    assert res_notif.status_code == 200
    notifs = res_notif.json()
    assert any("Winter Open 2026" in n["message"] and "gold" in n["message"].lower() for n in notifs)


# ── 2. Queries, Isolation & Counts ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_athlete_can_fetch_own_notifications(
    client, db, athlete_user, athlete_token
):
    await create_notification(
        db,
        recipient_user_id=str(athlete_user["_id"]),
        title="Welcome",
        message="Welcome to Athletix!",
        type="general",
    )
    resp = await client.get("/api/v1/notifications", headers=auth_headers(athlete_token))
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["title"] == "Welcome"


@pytest.mark.asyncio
async def test_athlete_cannot_see_other_user_notifications(
    client, db, coach_user, athlete_user, athlete_token
):
    # Create notification for coach
    await create_notification(
        db,
        recipient_user_id=str(coach_user["_id"]),
        title="Coach Meeting",
        message="Staff meeting at 5 PM",
        type="general",
    )
    # Athlete queries their notifications
    resp = await client.get("/api/v1/notifications", headers=auth_headers(athlete_token))
    assert resp.status_code == 200
    assert len(resp.json()) == 0


@pytest.mark.asyncio
async def test_coach_can_fetch_own_notifications(
    client, db, coach_user, coach_token
):
    await create_notification(
        db,
        recipient_user_id=str(coach_user["_id"]),
        title="Schedule Update",
        message="Schedule has been updated",
        type="training",
    )
    resp = await client.get("/api/v1/notifications", headers=auth_headers(coach_token))
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["title"] == "Schedule Update"


@pytest.mark.asyncio
async def test_admin_can_fetch_own_notifications(
    client, db, admin_user, admin_token
):
    await create_notification(
        db,
        recipient_user_id=str(admin_user["_id"]),
        title="System Notice",
        message="System backup complete",
        type="general",
    )
    resp = await client.get("/api/v1/notifications", headers=auth_headers(admin_token))
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["title"] == "System Notice"


@pytest.mark.asyncio
async def test_unread_count_accurate(
    client, db, athlete_user, athlete_token
):
    u_id = str(athlete_user["_id"])
    await create_notification(db, recipient_user_id=u_id, title="N1", message="M1")
    await create_notification(db, recipient_user_id=u_id, title="N2", message="M2")

    resp = await client.get("/api/v1/notifications/unread-count", headers=auth_headers(athlete_token))
    assert resp.status_code == 200
    assert resp.json()["unread_count"] == 2


# ── 3. Read Status Mutations & Ownership ───────────────────────────────────────

@pytest.mark.asyncio
async def test_mark_notification_as_read(
    client, db, athlete_user, athlete_token
):
    doc = await create_notification(
        db,
        recipient_user_id=str(athlete_user["_id"]),
        title="New Msg",
        message="Test content",
    )
    notif_id = str(doc["_id"])

    # Mark as read
    patch_resp = await client.patch(
        f"/api/v1/notifications/{notif_id}/read",
        headers=auth_headers(athlete_token),
    )
    assert patch_resp.status_code == 200
    body = patch_resp.json()
    assert body["is_read"] is True
    assert body["read_at"] is not None

    # Unread count should now be 0
    count_resp = await client.get("/api/v1/notifications/unread-count", headers=auth_headers(athlete_token))
    assert count_resp.json()["unread_count"] == 0


@pytest.mark.asyncio
async def test_mark_notification_as_read_forbidden_for_other_user(
    client, db, coach_user, athlete_user, athlete_token
):
    doc = await create_notification(
        db,
        recipient_user_id=str(coach_user["_id"]),
        title="Coach Secret",
        message="For coach only",
    )
    notif_id = str(doc["_id"])

    # Athlete attempts to mark coach's notification as read
    patch_resp = await client.patch(
        f"/api/v1/notifications/{notif_id}/read",
        headers=auth_headers(athlete_token),
    )
    assert patch_resp.status_code == 403


@pytest.mark.asyncio
async def test_mark_all_as_read(
    client, db, athlete_user, athlete_token
):
    u_id = str(athlete_user["_id"])
    await create_notification(db, recipient_user_id=u_id, title="1", message="M1")
    await create_notification(db, recipient_user_id=u_id, title="2", message="M2")
    await create_notification(db, recipient_user_id=u_id, title="3", message="M3")

    resp = await client.patch("/api/v1/notifications/read-all", headers=auth_headers(athlete_token))
    assert resp.status_code == 200
    assert resp.json()["updated_count"] == 3

    # Check unread count
    count_resp = await client.get("/api/v1/notifications/unread-count", headers=auth_headers(athlete_token))
    assert count_resp.json()["unread_count"] == 0


@pytest.mark.asyncio
async def test_delete_notification_and_ownership_check(
    client, db, coach_user, athlete_user, athlete_token
):
    coach_doc = await create_notification(
        db, recipient_user_id=str(coach_user["_id"]), title="C", message="Msg"
    )
    ath_doc = await create_notification(
        db, recipient_user_id=str(athlete_user["_id"]), title="A", message="Msg"
    )

    # Athlete attempts to delete coach notification -> 403
    del_forbidden = await client.delete(
        f"/api/v1/notifications/{str(coach_doc['_id'])}",
        headers=auth_headers(athlete_token),
    )
    assert del_forbidden.status_code == 403

    # Athlete deletes own notification -> 200
    del_ok = await client.delete(
        f"/api/v1/notifications/{str(ath_doc['_id'])}",
        headers=auth_headers(athlete_token),
    )
    assert del_ok.status_code == 200


@pytest.mark.asyncio
async def test_filter_notifications_by_type_and_unread(
    client, db, athlete_user, athlete_token
):
    u_id = str(athlete_user["_id"])
    n1 = await create_notification(db, recipient_user_id=u_id, title="T1", message="M1", type="training")
    n2 = await create_notification(db, recipient_user_id=u_id, title="P1", message="M2", type="performance")
    
    # Mark n1 as read
    await client.patch(f"/api/v1/notifications/{str(n1['_id'])}/read", headers=auth_headers(athlete_token))

    # Filter unread
    res_unread = await client.get("/api/v1/notifications?unread=true", headers=auth_headers(athlete_token))
    assert res_unread.status_code == 200
    items = res_unread.json()
    assert len(items) == 1
    assert items[0]["title"] == "P1"

    # Filter type=training
    res_type = await client.get("/api/v1/notifications?type=training", headers=auth_headers(athlete_token))
    assert res_type.status_code == 200
    assert len(res_type.json()) == 1
    assert res_type.json()[0]["title"] == "T1"


@pytest.mark.asyncio
async def test_duplicate_notification_prevention(
    client, db, athlete_user, athlete_token
):
    u_id = str(athlete_user["_id"])
    # Insert first
    first = await create_notification(
        db,
        recipient_user_id=u_id,
        title="Training Session",
        message="Session at 10 AM",
        type="training",
        related_entity_type="training_session",
        related_entity_id="sess_123",
    )
    assert first is not None

    # Insert duplicate with same entity info
    second = await create_notification(
        db,
        recipient_user_id=u_id,
        title="Training Session Duplicate",
        message="Session at 10 AM",
        type="training",
        related_entity_type="training_session",
        related_entity_id="sess_123",
    )
    assert second["_id"] == first["_id"]

    # Verify database has exactly 1 notification
    count = await db.notifications.count_documents({"recipient_user_id": ObjectId(u_id)})
    assert count == 1


@pytest.mark.asyncio
async def test_unauthenticated_notification_request_fails(client):
    resp = await client.get("/api/v1/notifications")
    assert resp.status_code == 401
