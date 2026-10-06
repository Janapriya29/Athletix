"""
Phase 8 — Final Quality, Security, UX & Production Readiness Integration Tests.

Validates the full cross-module lifecycle and security boundaries:
1. End-to-end Cross-Module Workflow:
   Coach creates training
   -> Athlete sees training
   -> Attendance recorded
   -> Attendance analytics updated
   -> Performance assessment recorded
   -> Athlete notifications created
   -> Performance analytics updated
   -> Tournament participation
   -> Result recorded (gold medal & points)
   -> Ranking updated
   -> Result notification generated
   -> Reports reflect updated data (development summary, academy summary, CSV exports)
2. Security & RBAC boundary tests for Phase 8 quality audit.
"""
from datetime import datetime, timedelta, timezone
import pytest
from bson import ObjectId

from app.services.notification_service import notify_assessment_created


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_end_to_end_cross_module_lifecycle(
    client, db, admin_token, coach_token, athlete_token, admin_user, coach_user, athlete_user
):
    now = datetime.now(timezone.utc)

    # 1. Admin creates a Sport
    sport_payload = {
        "name": "Athletics",
        "category": "individual",
        "description": "Track and field sports",
        "is_active": True,
    }
    s_resp = await client.post("/api/v1/sports", json=sport_payload, headers=auth_headers(admin_token))
    assert s_resp.status_code == 201, s_resp.text
    sport_id = s_resp.json()["id"]

    # 2. Setup Coach and Athlete entities
    c_res = await db.coaches.insert_one({
        "user_id": coach_user["_id"],
        "full_name": coach_user["full_name"],
        "email": coach_user["email"],
        "sport_ids": [ObjectId(sport_id)],
        "status": "active",
        "created_at": now,
    })
    coach_id = str(c_res.inserted_id)

    a_res = await db.athletes.insert_one({
        "user_id": athlete_user["_id"],
        "full_name": athlete_user["full_name"],
        "email": athlete_user["email"],
        "sport_id": ObjectId(sport_id),
        "coach_id": ObjectId(coach_id),
        "status": "active",
        "created_at": now,
    })
    athlete_id = str(a_res.inserted_id)

    await db.coach_athlete_assignments.insert_one({
        "coach_id": ObjectId(coach_id),
        "athlete_id": ObjectId(athlete_id),
        "assigned_at": now,
    })

    # 3. Coach creates training session
    session_date = (now + timedelta(days=2)).replace(microsecond=0)
    session_payload = {
        "title": "Sprint Mechanics & Starts",
        "sport_id": sport_id,
        "coach_id": coach_id,
        "session_date": session_date.isoformat(),
        "start_time": "08:00",
        "end_time": "10:00",
        "location": "Main Track",
        "athlete_ids": [athlete_id],
    }
    sess_resp = await client.post(
        "/api/v1/training/sessions",
        json=session_payload,
        headers=auth_headers(coach_token),
    )
    assert sess_resp.status_code == 201, sess_resp.text
    session_id = sess_resp.json()["id"]

    # 4. Athlete sees training session in their schedule
    ath_sched = await client.get(
        f"/api/v1/training/sessions?athlete_id={athlete_id}",
        headers=auth_headers(athlete_token),
    )
    assert ath_sched.status_code == 200
    sessions_found = [s["id"] for s in ath_sched.json()]
    assert session_id in sessions_found

    # 5. Coach records attendance for athlete
    att_payload = {
        "athlete_id": athlete_id,
        "status": "present",
        "notes": "Excellent form off the blocks",
    }
    att_resp = await client.post(
        f"/api/v1/training/sessions/{session_id}/attendance",
        json=att_payload,
        headers=auth_headers(coach_token),
    )
    assert att_resp.status_code == 200, att_resp.text
    assert att_resp.json()["status"] == "present"

    # 6. Check attendance analytics updated
    att_summary = await client.get(
        f"/api/v1/training/athlete/{athlete_id}/attendance",
        headers=auth_headers(coach_token),
    )
    assert att_summary.status_code == 200
    att_data = att_summary.json()
    assert att_data["present_count"] == 1
    assert att_data["attendance_percentage"] == 100.0

    # Also check athlete can see their own attendance summary via /me/attendance
    me_att = await client.get(
        "/api/v1/training/me/attendance",
        headers=auth_headers(athlete_token),
    )
    assert me_att.status_code == 200
    assert me_att.json()["attendance_percentage"] == 100.0

    # 7. Performance assessment is created
    ass_date = now - timedelta(days=1)
    ass_doc = {
        "athlete_id": ObjectId(athlete_id),
        "coach_id": ObjectId(coach_id),
        "sport_id": ObjectId(sport_id),
        "date": ass_date,
        "overall_score": 88.5,
        "metrics": {"speed": 92.0, "acceleration": 85.0, "stamina": 88.5},
        "remarks": "Solid benchmark",
        "created_at": now,
    }
    ass_res = await db.performance_assessments.insert_one(ass_doc)
    ass_id = str(ass_res.inserted_id)

    # Trigger assessment notification
    await notify_assessment_created(
        db,
        athlete_user_id=str(athlete_user["_id"]),
        overall_score=88.5,
        assessment_id=ass_id,
    )

    # 8. Athlete checks notifications
    notif_resp = await client.get("/api/v1/notifications", headers=auth_headers(athlete_token))
    assert notif_resp.status_code == 200
    notifs = notif_resp.json()
    assert len(notifs) >= 1
    types = [n["type"] for n in notifs]
    assert "performance" in types

    # 9. Performance analytics reflects the assessment
    perf_resp = await client.get(
        f"/api/v1/analytics/athlete/{athlete_id}",
        headers=auth_headers(athlete_token),
    )
    assert perf_resp.status_code == 200
    perf_data = perf_resp.json()
    assert perf_data["athlete_id"] == athlete_id
    assert perf_data["current_performance"]["score"] == 88.5
    assert perf_data["strongest_metric"]["name"] == "speed"

    # 10. Admin creates Tournament
    tourn_start = now + timedelta(days=10)
    tourn_end = now + timedelta(days=12)
    tourn_reg = now + timedelta(days=8)
    t_payload = {
        "name": "National Youth Sprint Championship",
        "sport_id": sport_id,
        "location": "National Stadium",
        "start_date": tourn_start.isoformat(),
        "end_date": tourn_end.isoformat(),
        "registration_deadline": tourn_reg.isoformat(),
        "max_participants": 50,
        "status": "upcoming",
    }
    t_resp = await client.post("/api/v1/tournaments", json=t_payload, headers=auth_headers(admin_token))
    assert t_resp.status_code == 201, t_resp.text
    tourn_id = t_resp.json()["id"]

    # 11. Coach registers assigned athlete for tournament
    part_resp = await client.post(
        f"/api/v1/tournaments/{tourn_id}/participants",
        json={"athlete_id": athlete_id},
        headers=auth_headers(coach_token),
    )
    assert part_resp.status_code == 201, part_resp.text

    # 12. Admin records tournament result (gold medal, 10.0 points)
    res_resp = await client.post(
        f"/api/v1/tournaments/{tourn_id}/results",
        json={
            "athlete_id": athlete_id,
            "position": 1,
            "medal": "gold",
            "points": 10.0,
            "notes": "1st place 100m sprint",
        },
        headers=auth_headers(admin_token),
    )
    assert res_resp.status_code == 200, res_resp.text

    # 13. Tournament rankings reflect the points and medal
    rank_resp = await client.get("/api/v1/rankings/tournament", headers=auth_headers(athlete_token))
    assert rank_resp.status_code == 200
    rankings = rank_resp.json()
    assert len(rankings) >= 1
    top_rank = rankings[0]
    assert top_rank["athlete_id"] == athlete_id
    assert top_rank["points"] == 10.0
    assert top_rank["gold_count"] == 1
    assert top_rank["total_medals"] == 1

    # Also check unified rankings endpoint
    unified_resp = await client.get("/api/v1/rankings?type=tournament", headers=auth_headers(athlete_token))
    assert unified_resp.status_code == 200
    assert len(unified_resp.json()["items"]) >= 1

    # 14. Reports reflect updated data across modules
    # Athlete development summary
    dev_rep = await client.get(
        f"/api/v1/reports/athlete/{athlete_id}/development",
        headers=auth_headers(athlete_token),
    )
    assert dev_rep.status_code == 200
    dev_data = dev_rep.json()
    assert dev_data["athlete_id"] == athlete_id
    assert dev_data["attendance_summary"]["total_sessions"] == 1
    assert dev_data["tournaments_summary"]["total_tournaments"] == 1
    assert dev_data["tournaments_summary"]["medals_summary"]["gold"] == 1

    # Academy summary report (Admin only)
    acad_rep = await client.get(
        "/api/v1/reports/academy/summary",
        headers=auth_headers(admin_token),
    )
    assert acad_rep.status_code == 200
    acad_data = acad_rep.json()
    assert acad_data["total_athletes"] >= 1
    assert acad_data["total_coaches"] >= 1
    assert acad_data["total_sports"] >= 1
    assert acad_data["total_medals_awarded"] >= 1

    # Academy CSV reports
    att_csv = await client.get("/api/v1/reports/attendance?format=csv", headers=auth_headers(admin_token))
    assert att_csv.status_code == 200
    assert "text/csv" in att_csv.headers.get("content-type", "")

    tourn_csv = await client.get("/api/v1/reports/tournaments?format=csv", headers=auth_headers(admin_token))
    assert tourn_csv.status_code == 200
    assert "text/csv" in tourn_csv.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_cross_role_report_and_notification_isolation(
    client, db, athlete_token, coach_token, admin_token, athlete_user, coach_user
):
    now = datetime.now(timezone.utc)

    # Create unassigned athlete
    u_other = await db.users.insert_one({
        "email": "other_ath@test.com",
        "role": "athlete",
        "full_name": "Other Athlete",
        "is_active": True,
        "created_at": now,
    })
    other_ath = await db.athletes.insert_one({
        "user_id": u_other.inserted_id,
        "full_name": "Other Athlete",
        "email": "other_ath@test.com",
        "status": "active",
        "created_at": now,
    })
    other_ath_id = str(other_ath.inserted_id)

    # 1. Athlete cannot access another athlete's performance report (403)
    resp = await client.get(
        f"/api/v1/reports/athlete/{other_ath_id}/performance",
        headers=auth_headers(athlete_token),
    )
    assert resp.status_code == 403

    # 2. Coach cannot access unassigned athlete's performance report (403)
    resp = await client.get(
        f"/api/v1/reports/athlete/{other_ath_id}/performance",
        headers=auth_headers(coach_token),
    )
    assert resp.status_code == 403

    # 3. Coach/Athlete cannot access academy summary report (403)
    resp = await client.get("/api/v1/reports/academy/summary", headers=auth_headers(athlete_token))
    assert resp.status_code == 403

    resp = await client.get("/api/v1/reports/academy/summary", headers=auth_headers(coach_token))
    assert resp.status_code == 403

    # 4. Athlete cannot delete or mark as read another user's notification
    n_res = await db.notifications.insert_one({
        "recipient_user_id": u_other.inserted_id,
        "user_id": u_other.inserted_id,
        "type": "general",
        "title": "Confidential Notification",
        "message": "Only for other user",
        "is_read": False,
        "created_at": now,
    })
    n_id = str(n_res.inserted_id)

    patch_resp = await client.patch(
        f"/api/v1/notifications/{n_id}/read",
        headers=auth_headers(athlete_token),
    )
    assert patch_resp.status_code in [403, 404]

    del_resp = await client.delete(
        f"/api/v1/notifications/{n_id}",
        headers=auth_headers(athlete_token),
    )
    assert del_resp.status_code in [403, 404]


@pytest.mark.asyncio
async def test_input_validation_boundaries(client, admin_token, coach_token):
    now = datetime.now(timezone.utc)

    # 1. Tournament with end_date before start_date is rejected
    t_invalid_date = {
        "name": "Invalid Date Championship",
        "sport_id": str(ObjectId()),
        "location": "City Stadium",
        "start_date": (now + timedelta(days=10)).isoformat(),
        "end_date": (now + timedelta(days=5)).isoformat(),  # before start
        "registration_deadline": (now + timedelta(days=2)).isoformat(),
    }
    resp = await client.post("/api/v1/tournaments", json=t_invalid_date, headers=auth_headers(admin_token))
    assert resp.status_code in [400, 422]

    # 2. Tournament with registration deadline after start_date is rejected
    t_invalid_reg = {
        "name": "Invalid Reg Championship",
        "sport_id": str(ObjectId()),
        "location": "City Stadium",
        "start_date": (now + timedelta(days=5)).isoformat(),
        "end_date": (now + timedelta(days=10)).isoformat(),
        "registration_deadline": (now + timedelta(days=6)).isoformat(),  # after start
    }
    resp2 = await client.post("/api/v1/tournaments", json=t_invalid_reg, headers=auth_headers(admin_token))
    assert resp2.status_code in [400, 422]

    # 3. Training session with end_time before start_time is rejected
    invalid_session = {
        "title": "Invalid Time Session",
        "sport_id": str(ObjectId()),
        "coach_id": str(ObjectId()),
        "session_date": (now + timedelta(days=2)).isoformat(),
        "start_time": "14:00",
        "end_time": "10:00",  # before start_time
        "location": "Main Hall",
    }
    resp3 = await client.post("/api/v1/training/sessions", json=invalid_session, headers=auth_headers(coach_token))
    assert resp3.status_code in [400, 422]


@pytest.mark.asyncio
async def test_rbac_admin_endpoint_protection(client, coach_token, athlete_token):
    # Coach cannot create sports (Admin only)
    resp_coach_sport = await client.post(
        "/api/v1/sports",
        json={"name": "Handball", "category": "team"},
        headers=auth_headers(coach_token),
    )
    assert resp_coach_sport.status_code == 403

    # Athlete cannot create sports (Admin only)
    resp_ath_sport = await client.post(
        "/api/v1/sports",
        json={"name": "Handball", "category": "team"},
        headers=auth_headers(athlete_token),
    )
    assert resp_ath_sport.status_code == 403

    # Coach cannot access admin analytics summary
    resp_coach_analytics = await client.get(
        "/api/v1/analytics/admin/summary",
        headers=auth_headers(coach_token),
    )
    assert resp_coach_analytics.status_code == 403

    # Athlete cannot access admin analytics summary
    resp_ath_analytics = await client.get(
        "/api/v1/analytics/admin/summary",
        headers=auth_headers(athlete_token),
    )
    assert resp_ath_analytics.status_code == 403

