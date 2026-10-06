"""
Training & Attendance tests — Phase 3.
Covers:
- Training session management & validation
- Participant management & integrity
- Attendance recording & updating
- Attendance percentage & warning calculations
- Role-based access control
"""
from datetime import datetime, timedelta, timezone
import pytest
from bson import ObjectId


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── Fixtures Helper ────────────────────────────────────────────────────────────

async def _setup_training_fixture(db, admin_user, coach_user, athlete_user):
    """
    Creates:
    - Active sport: "Basketball"
    - Inactive sport: "Archery"
    - Coach profile for coach_user assigned to Basketball
    - Unrelated coach: "Other Coach"
    - Athlete profile for athlete_user assigned to Basketball and coach_user
    - Unrelated athlete: "Other Athlete" assigned to Football and Other Coach
    """
    now = datetime.now(timezone.utc)

    # Sports
    s_active = await db.sports.insert_one({"name": "Basketball", "is_active": True, "created_at": now})
    sport_id = str(s_active.inserted_id)

    s_inactive = await db.sports.insert_one({"name": "Archery", "is_active": False, "created_at": now})
    inactive_sport_id = str(s_inactive.inserted_id)

    # Coach profile for coach_user
    c_res = await db.coaches.insert_one({
        "user_id": coach_user["_id"],
        "full_name": coach_user["full_name"],
        "email": coach_user["email"],
        "status": "active",
        "sport_ids": [s_active.inserted_id],
        "created_at": now,
    })
    coach_id = str(c_res.inserted_id)

    # Inactive coach
    c_inact = await db.coaches.insert_one({
        "user_id": ObjectId(),
        "full_name": "Inactive Coach",
        "email": "inactive_coach@test.com",
        "status": "inactive",
        "sport_ids": [s_active.inserted_id],
        "created_at": now,
    })
    inactive_coach_id = str(c_inact.inserted_id)

    # Other coach (different user)
    other_c = await db.coaches.insert_one({
        "user_id": ObjectId(),
        "full_name": "Other Coach",
        "email": "other_coach@test.com",
        "status": "active",
        "sport_ids": [s_active.inserted_id],
        "created_at": now,
    })
    other_coach_id = str(other_c.inserted_id)

    # Athlete profile for athlete_user
    a_res = await db.athletes.insert_one({
        "user_id": athlete_user["_id"],
        "full_name": athlete_user["full_name"],
        "email": athlete_user["email"],
        "sport_id": s_active.inserted_id,
        "coach_id": c_res.inserted_id,
        "status": "active",
        "created_at": now,
    })
    athlete_id = str(a_res.inserted_id)

    await db.coach_athlete_assignments.insert_one({
        "coach_id": c_res.inserted_id,
        "athlete_id": a_res.inserted_id,
        "assigned_at": now,
    })

    # Inactive athlete
    a_inact = await db.athletes.insert_one({
        "user_id": ObjectId(),
        "full_name": "Inactive Athlete",
        "email": "inactive_athlete@test.com",
        "sport_id": s_active.inserted_id,
        "coach_id": c_res.inserted_id,
        "status": "inactive",
        "created_at": now,
    })
    inactive_athlete_id = str(a_inact.inserted_id)

    # Unrelated athlete (coached by other_coach)
    other_a = await db.athletes.insert_one({
        "user_id": ObjectId(),
        "full_name": "Other Athlete",
        "email": "other_ath@test.com",
        "sport_id": s_active.inserted_id,
        "coach_id": other_c.inserted_id,
        "status": "active",
        "created_at": now,
    })
    other_athlete_id = str(other_a.inserted_id)

    return {
        "sport_id": sport_id,
        "inactive_sport_id": inactive_sport_id,
        "coach_id": coach_id,
        "inactive_coach_id": inactive_coach_id,
        "other_coach_id": other_coach_id,
        "athlete_id": athlete_id,
        "inactive_athlete_id": inactive_athlete_id,
        "other_athlete_id": other_athlete_id,
    }


# ── Training Session Tests ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_admin_can_create_session(client, admin_token, admin_user, coach_user, athlete_user, db):
    fx = await _setup_training_fixture(db, admin_user, coach_user, athlete_user)

    payload = {
        "title": "Admin Elite Training",
        "description": "Full court drills",
        "sport_id": fx["sport_id"],
        "coach_id": fx["coach_id"],
        "session_date": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
        "start_time": "10:00",
        "end_time": "12:00",
        "location": "Court 1",
    }
    resp = await client.post("/api/v1/training/sessions", json=payload, headers=auth_headers(admin_token))
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["title"] == "Admin Elite Training"
    assert data["sport_name"] == "Basketball"
    assert data["status"] == "scheduled"
    assert "id" in data


@pytest.mark.asyncio
async def test_coach_can_create_permitted_session(client, coach_token, admin_user, coach_user, athlete_user, db):
    fx = await _setup_training_fixture(db, admin_user, coach_user, athlete_user)

    payload = {
        "title": "Shooting Fundamentals",
        "sport_id": fx["sport_id"],
        "coach_id": fx["coach_id"],
        "session_date": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
        "start_time": "14:00",
        "end_time": "16:00",
        "location": "Gym A",
        "athlete_ids": [fx["athlete_id"]],
    }
    resp = await client.post("/api/v1/training/sessions", json=payload, headers=auth_headers(coach_token))
    assert resp.status_code == 201, resp.text
    assert resp.json()["title"] == "Shooting Fundamentals"
    assert resp.json()["participant_count"] == 1


@pytest.mark.asyncio
async def test_athlete_cannot_create_session(client, athlete_token, admin_user, coach_user, athlete_user, db):
    fx = await _setup_training_fixture(db, admin_user, coach_user, athlete_user)

    payload = {
        "title": "Athlete Rogue Session",
        "sport_id": fx["sport_id"],
        "coach_id": fx["coach_id"],
        "session_date": datetime.now(timezone.utc).isoformat(),
        "start_time": "09:00",
        "end_time": "10:00",
    }
    resp = await client.post("/api/v1/training/sessions", json=payload, headers=auth_headers(athlete_token))
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_invalid_and_inactive_sport_rejected(client, admin_token, admin_user, coach_user, athlete_user, db):
    fx = await _setup_training_fixture(db, admin_user, coach_user, athlete_user)

    # 1. Non-existent sport
    resp1 = await client.post(
        "/api/v1/training/sessions",
        json={
            "title": "Fake Sport",
            "sport_id": str(ObjectId()),
            "coach_id": fx["coach_id"],
            "session_date": datetime.now(timezone.utc).isoformat(),
            "start_time": "09:00",
            "end_time": "10:00",
        },
        headers=auth_headers(admin_token),
    )
    assert resp1.status_code == 400
    assert "Sport not found" in resp1.json()["detail"]

    # 2. Inactive sport
    resp2 = await client.post(
        "/api/v1/training/sessions",
        json={
            "title": "Inactive Sport Session",
            "sport_id": fx["inactive_sport_id"],
            "coach_id": fx["coach_id"],
            "session_date": datetime.now(timezone.utc).isoformat(),
            "start_time": "09:00",
            "end_time": "10:00",
        },
        headers=auth_headers(admin_token),
    )
    assert resp2.status_code == 400
    assert "inactive" in resp2.json()["detail"]


@pytest.mark.asyncio
async def test_invalid_and_inactive_coach_rejected(client, admin_token, admin_user, coach_user, athlete_user, db):
    fx = await _setup_training_fixture(db, admin_user, coach_user, athlete_user)

    # 1. Non-existent coach
    resp1 = await client.post(
        "/api/v1/training/sessions",
        json={
            "title": "Fake Coach",
            "sport_id": fx["sport_id"],
            "coach_id": str(ObjectId()),
            "session_date": datetime.now(timezone.utc).isoformat(),
            "start_time": "09:00",
            "end_time": "10:00",
        },
        headers=auth_headers(admin_token),
    )
    assert resp1.status_code == 400
    assert "Coach not found" in resp1.json()["detail"]

    # 2. Inactive coach
    resp2 = await client.post(
        "/api/v1/training/sessions",
        json={
            "title": "Inactive Coach Session",
            "sport_id": fx["sport_id"],
            "coach_id": fx["inactive_coach_id"],
            "session_date": datetime.now(timezone.utc).isoformat(),
            "start_time": "09:00",
            "end_time": "10:00",
        },
        headers=auth_headers(admin_token),
    )
    assert resp2.status_code == 400
    assert "inactive" in resp2.json()["detail"]


@pytest.mark.asyncio
async def test_invalid_time_range_rejected(client, admin_token, admin_user, coach_user, athlete_user, db):
    fx = await _setup_training_fixture(db, admin_user, coach_user, athlete_user)

    # End time before start time
    resp = await client.post(
        "/api/v1/training/sessions",
        json={
            "title": "Time Travel Session",
            "sport_id": fx["sport_id"],
            "coach_id": fx["coach_id"],
            "session_date": datetime.now(timezone.utc).isoformat(),
            "start_time": "15:00",
            "end_time": "14:00",
        },
        headers=auth_headers(admin_token),
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_coach_cannot_access_another_coach_session(client, coach_token, admin_user, coach_user, athlete_user, db):
    fx = await _setup_training_fixture(db, admin_user, coach_user, athlete_user)

    # Session created for other_coach
    session_res = await db.training_sessions.insert_one({
        "title": "Other Coach Private Practice",
        "sport_id": ObjectId(fx["sport_id"]),
        "coach_id": ObjectId(fx["other_coach_id"]),
        "session_date": datetime.now(timezone.utc),
        "start_time": "09:00",
        "end_time": "10:00",
        "athlete_ids": [],
        "status": "scheduled",
    })
    s_id = str(session_res.inserted_id)

    # Coach tries to GET the session
    resp = await client.get(f"/api/v1/training/sessions/{s_id}", headers=auth_headers(coach_token))
    assert resp.status_code == 403
    assert "another coach" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_admin_can_view_all_sessions(client, admin_token, admin_user, coach_user, athlete_user, db):
    fx = await _setup_training_fixture(db, admin_user, coach_user, athlete_user)

    # Insert two sessions with different coaches
    await db.training_sessions.insert_one({
        "title": "Session 1",
        "sport_id": ObjectId(fx["sport_id"]),
        "coach_id": ObjectId(fx["coach_id"]),
        "session_date": datetime.now(timezone.utc),
        "status": "scheduled",
    })
    await db.training_sessions.insert_one({
        "title": "Session 2",
        "sport_id": ObjectId(fx["sport_id"]),
        "coach_id": ObjectId(fx["other_coach_id"]),
        "session_date": datetime.now(timezone.utc),
        "status": "scheduled",
    })

    resp = await client.get("/api/v1/training/sessions", headers=auth_headers(admin_token))
    assert resp.status_code == 200
    assert len(resp.json()) >= 2


# ── Participant Tests ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_add_and_remove_participants(client, admin_token, coach_token, admin_user, coach_user, athlete_user, db):
    fx = await _setup_training_fixture(db, admin_user, coach_user, athlete_user)

    # Create session owned by coach
    s_res = await db.training_sessions.insert_one({
        "title": "Team Practice",
        "sport_id": ObjectId(fx["sport_id"]),
        "coach_id": ObjectId(fx["coach_id"]),
        "session_date": datetime.now(timezone.utc),
        "athlete_ids": [],
        "status": "scheduled",
    })
    s_id = str(s_res.inserted_id)

    # 1. Coach can add assigned athlete
    resp1 = await client.post(
        f"/api/v1/training/sessions/{s_id}/participants",
        json={"athlete_id": fx["athlete_id"]},
        headers=auth_headers(coach_token),
    )
    assert resp1.status_code == 200
    assert resp1.json()["participant_count"] == 1

    # 2. Duplicate participant rejected
    resp_dup = await client.post(
        f"/api/v1/training/sessions/{s_id}/participants",
        json={"athlete_id": fx["athlete_id"]},
        headers=auth_headers(coach_token),
    )
    assert resp_dup.status_code == 409

    # 3. Coach cannot add unrelated athlete
    resp_unrelated = await client.post(
        f"/api/v1/training/sessions/{s_id}/participants",
        json={"athlete_id": fx["other_athlete_id"]},
        headers=auth_headers(coach_token),
    )
    assert resp_unrelated.status_code == 403

    # 4. Inactive athlete rejected
    resp_inact = await client.post(
        f"/api/v1/training/sessions/{s_id}/participants",
        json={"athlete_id": fx["inactive_athlete_id"]},
        headers=auth_headers(coach_token),
    )
    assert resp_inact.status_code == 400

    # 5. Remove participant
    del_resp = await client.delete(
        f"/api/v1/training/sessions/{s_id}/participants/{fx['athlete_id']}",
        headers=auth_headers(coach_token),
    )
    assert del_resp.status_code == 200
    assert del_resp.json()["participant_count"] == 0


# ── Attendance Tests ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_record_and_update_attendance(client, coach_token, admin_token, athlete_token, admin_user, coach_user, athlete_user, db):
    fx = await _setup_training_fixture(db, admin_user, coach_user, athlete_user)

    s_res = await db.training_sessions.insert_one({
        "title": "Match Simulation",
        "sport_id": ObjectId(fx["sport_id"]),
        "coach_id": ObjectId(fx["coach_id"]),
        "session_date": datetime.now(timezone.utc),
        "athlete_ids": [ObjectId(fx["athlete_id"])],
        "status": "completed",
    })
    s_id = str(s_res.inserted_id)

    # 1. Non-participant cannot receive attendance
    resp_np = await client.post(
        f"/api/v1/training/sessions/{s_id}/attendance",
        json={"athlete_id": fx["other_athlete_id"], "status": "present"},
        headers=auth_headers(coach_token),
    )
    assert resp_np.status_code == 400
    assert "not a participant" in resp_np.json()["detail"]

    # 2. Coach records attendance: Present
    resp_att = await client.post(
        f"/api/v1/training/sessions/{s_id}/attendance",
        json={"athlete_id": fx["athlete_id"], "status": "present", "remarks": "Great hustle"},
        headers=auth_headers(coach_token),
    )
    assert resp_att.status_code == 200, resp_att.text
    data = resp_att.json()
    assert data["status"] == "present"
    assert data["remarks"] == "Great hustle"

    # 3. Update attendance to 'late' (idempotent upsert, does NOT duplicate)
    resp_upd = await client.put(
        f"/api/v1/training/sessions/{s_id}/attendance/{fx['athlete_id']}",
        json={"status": "late", "remarks": "10 min late"},
        headers=auth_headers(coach_token),
    )
    assert resp_upd.status_code == 200
    assert resp_upd.json()["status"] == "late"

    # Verify database has exactly 1 attendance record
    att_count = await db.attendance.count_documents({"session_id": ObjectId(s_id), "athlete_id": ObjectId(fx["athlete_id"])})
    assert att_count == 1

    # 4. Admin can view session attendance
    resp_admin = await client.get(f"/api/v1/training/sessions/{s_id}/attendance", headers=auth_headers(admin_token))
    assert resp_admin.status_code == 200
    assert len(resp_admin.json()) == 1

    # 5. Athlete can view own attendance summary via /training/me/attendance
    resp_ath_me = await client.get("/api/v1/training/me/attendance", headers=auth_headers(athlete_token))
    assert resp_ath_me.status_code == 200
    ath_summary = resp_ath_me.json()
    assert ath_summary["total_sessions"] == 1
    assert ath_summary["attended_sessions"] == 1  # Late counts as attended!
    assert ath_summary["late_count"] == 1
    assert ath_summary["attendance_percentage"] == 100.0


# ── Attendance Calculation & Warning Tests ────────────────────────────────────

@pytest.mark.asyncio
async def test_attendance_calculation_rules(client, athlete_token, admin_user, coach_user, athlete_user, db):
    """
    Verifies:
    - Present counts as attended
    - Late counts as attended
    - Absent does NOT count as attended
    - Cancelled sessions are excluded from total
    - Percentage calculation: (Present + Late) / Total * 100
    - < 75% triggers warning indicator
    """
    fx = await _setup_training_fixture(db, admin_user, coach_user, athlete_user)
    ath_oid = ObjectId(fx["athlete_id"])
    coach_oid = ObjectId(fx["coach_id"])
    sport_oid = ObjectId(fx["sport_id"])

    # Create 4 sessions:
    # Session 1: Completed, marked Present
    s1 = await db.training_sessions.insert_one({"title": "S1", "sport_id": sport_oid, "coach_id": coach_oid, "athlete_ids": [ath_oid], "status": "completed"})
    await db.attendance.insert_one({"session_id": s1.inserted_id, "athlete_id": ath_oid, "status": "present"})

    # Session 2: Completed, marked Late (counts as attended)
    s2 = await db.training_sessions.insert_one({"title": "S2", "sport_id": sport_oid, "coach_id": coach_oid, "athlete_ids": [ath_oid], "status": "completed"})
    await db.attendance.insert_one({"session_id": s2.inserted_id, "athlete_id": ath_oid, "status": "late"})

    # Session 3: Completed, marked Absent
    s3 = await db.training_sessions.insert_one({"title": "S3", "sport_id": sport_oid, "coach_id": coach_oid, "athlete_ids": [ath_oid], "status": "completed"})
    await db.attendance.insert_one({"session_id": s3.inserted_id, "athlete_id": ath_oid, "status": "absent"})

    # Session 4: Completed, marked Absent
    s4 = await db.training_sessions.insert_one({"title": "S4", "sport_id": sport_oid, "coach_id": coach_oid, "athlete_ids": [ath_oid], "status": "completed"})
    await db.attendance.insert_one({"session_id": s4.inserted_id, "athlete_id": ath_oid, "status": "absent"})

    # Session 5: CANCELLED session (must be excluded from total sessions!)
    s5 = await db.training_sessions.insert_one({"title": "S5", "sport_id": sport_oid, "coach_id": coach_oid, "athlete_ids": [ath_oid], "status": "cancelled"})

    # Calculation:
    # Total non-cancelled sessions = 4
    # Attended (Present + Late) = 2
    # Absent = 2
    # Percentage = 2 / 4 * 100 = 50.0%
    # Warning should be TRUE (< 75%)
    resp = await client.get("/api/v1/training/me/attendance", headers=auth_headers(athlete_token))
    assert resp.status_code == 200
    summary = resp.json()
    assert summary["total_sessions"] == 4
    assert summary["attended_sessions"] == 2
    assert summary["present_count"] == 1
    assert summary["late_count"] == 1
    assert summary["absent_count"] == 2
    assert summary["attendance_percentage"] == 50.0
    assert summary["warning"] is True


@pytest.mark.asyncio
async def test_unauthenticated_requests_rejected(client):
    resp1 = await client.get("/api/v1/training/sessions")
    assert resp1.status_code == 401
    resp2 = await client.get("/api/v1/training/me")
    assert resp2.status_code == 401
