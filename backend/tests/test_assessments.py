"""
Performance Assessments Tests — Phase C.
Covers:
1. Coach can create assessment for assigned athlete
2. Coach cannot create assessment for unassigned athlete (403)
3. Athlete cannot create assessment (403)
4. Invalid metric scores (< 0 or > 100) rejected (422)
5. Empty metrics rejected (422)
6. Overall score calculated automatically if omitted (arithmetic mean)
7. Custom overall score preserved if provided
8. Athlete notification created on assessment
9. Athlete can view own assessment history
10. Athlete cannot view another athlete's assessment history (403)
11. Admin can create and list all assessments
12. New assessment updates athlete analytics and rankings
"""
from datetime import datetime, timedelta, timezone
from bson import ObjectId
import pytest


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _setup_assessment_fixture(db, admin_user, coach_user, athlete_user):
    now = datetime.now(timezone.utc)

    # 1. Sports
    s_doc = await db.sports.insert_one({"name": "Football", "is_active": True, "created_at": now})
    football_id = s_doc.inserted_id

    s2_doc = await db.sports.insert_one({"name": "Cricket", "is_active": True, "created_at": now})
    cricket_id = s2_doc.inserted_id

    # 2. Coaches
    coach_profile = await db.coaches.insert_one({
        "user_id": coach_user["_id"],
        "full_name": coach_user["full_name"],
        "email": coach_user["email"],
        "status": "active",
        "sport_ids": [football_id],
        "created_at": now,
    })
    coach_id = coach_profile.inserted_id

    # Coach 2
    u_c2 = await db.users.insert_one({
        "email": "coach2_c@test.com",
        "role": "coach",
        "full_name": "Coach Two C",
        "is_active": True,
        "created_at": now,
    })
    coach2_profile = await db.coaches.insert_one({
        "user_id": u_c2.inserted_id,
        "full_name": "Coach Two C",
        "email": "coach2_c@test.com",
        "status": "active",
        "sport_ids": [cricket_id],
        "created_at": now,
    })
    coach2_id = coach2_profile.inserted_id

    # 3. Athletes
    # Athlete 1 -> assigned to coach 1
    athlete1_profile = await db.athletes.insert_one({
        "user_id": athlete_user["_id"],
        "full_name": athlete_user["full_name"],
        "email": athlete_user["email"],
        "status": "active",
        "sport_id": football_id,
        "coach_id": coach_id,
        "created_at": now,
    })
    athlete1_id = athlete1_profile.inserted_id

    await db.coach_athlete_assignments.insert_one({
        "coach_id": coach_id,
        "athlete_id": athlete1_id,
        "assigned_at": now,
    })

    # Athlete 2 -> assigned to coach 2
    u_a2 = await db.users.insert_one({
        "email": "athlete2_c@test.com",
        "role": "athlete",
        "full_name": "Athlete Two C",
        "is_active": True,
        "created_at": now,
    })
    athlete2_profile = await db.athletes.insert_one({
        "user_id": u_a2.inserted_id,
        "full_name": "Athlete Two C",
        "email": "athlete2_c@test.com",
        "status": "active",
        "sport_id": cricket_id,
        "coach_id": coach2_id,
        "created_at": now,
    })
    athlete2_id = athlete2_profile.inserted_id

    await db.coach_athlete_assignments.insert_one({
        "coach_id": coach2_id,
        "athlete_id": athlete2_id,
        "assigned_at": now,
    })

    return {
        "football_id": str(football_id),
        "cricket_id": str(cricket_id),
        "coach_id": str(coach_id),
        "coach2_id": str(coach2_id),
        "athlete1_id": str(athlete1_id),
        "athlete2_id": str(athlete2_id),
    }


@pytest.mark.asyncio
async def test_coach_can_create_assessment_for_assigned_athlete(
    client, db, admin_user, coach_user, athlete_user, coach_token
):
    ctx = await _setup_assessment_fixture(db, admin_user, coach_user, athlete_user)

    payload = {
        "athlete_id": ctx["athlete1_id"],
        "sport_id": ctx["football_id"],
        "metrics": {"speed": 80.0, "passing": 70.0},
        "remarks": "Solid performance in practice",
    }
    resp = await client.post("/api/v1/assessments", json=payload, headers=auth_headers(coach_token))
    assert resp.status_code == 201
    data = resp.json()
    assert data["athlete_id"] == ctx["athlete1_id"]
    assert data["overall_score"] == 75.0
    assert data["metrics"]["speed"] == 80.0
    assert data["metrics"]["passing"] == 70.0
    assert data["remarks"] == "Solid performance in practice"
    assert data["athlete_name"] == athlete_user["full_name"]


@pytest.mark.asyncio
async def test_coach_cannot_create_assessment_for_unassigned_athlete(
    client, db, admin_user, coach_user, athlete_user, coach_token
):
    ctx = await _setup_assessment_fixture(db, admin_user, coach_user, athlete_user)

    # Athlete 2 is assigned to coach 2, not coach 1
    payload = {
        "athlete_id": ctx["athlete2_id"],
        "sport_id": ctx["cricket_id"],
        "metrics": {"batting": 85.0},
    }
    resp = await client.post("/api/v1/assessments", json=payload, headers=auth_headers(coach_token))
    assert resp.status_code == 403
    assert "not assigned" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_athlete_cannot_create_assessment(
    client, db, admin_user, coach_user, athlete_user, athlete_token
):
    ctx = await _setup_assessment_fixture(db, admin_user, coach_user, athlete_user)

    payload = {
        "athlete_id": ctx["athlete1_id"],
        "metrics": {"speed": 90.0},
    }
    resp = await client.post("/api/v1/assessments", json=payload, headers=auth_headers(athlete_token))
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_invalid_metric_score_rejected(
    client, db, admin_user, coach_user, athlete_user, coach_token
):
    ctx = await _setup_assessment_fixture(db, admin_user, coach_user, athlete_user)

    # Metric score > 100
    payload = {
        "athlete_id": ctx["athlete1_id"],
        "metrics": {"speed": 105.0},
    }
    resp = await client.post("/api/v1/assessments", json=payload, headers=auth_headers(coach_token))
    assert resp.status_code in (422, 400)

    # Metric score < 0
    payload2 = {
        "athlete_id": ctx["athlete1_id"],
        "metrics": {"speed": -5.0},
    }
    resp2 = await client.post("/api/v1/assessments", json=payload2, headers=auth_headers(coach_token))
    assert resp2.status_code in (422, 400)


@pytest.mark.asyncio
async def test_empty_metrics_rejected(
    client, db, admin_user, coach_user, athlete_user, coach_token
):
    ctx = await _setup_assessment_fixture(db, admin_user, coach_user, athlete_user)

    payload = {
        "athlete_id": ctx["athlete1_id"],
        "metrics": {},
    }
    resp = await client.post("/api/v1/assessments", json=payload, headers=auth_headers(coach_token))
    assert resp.status_code in (422, 400)


@pytest.mark.asyncio
async def test_overall_score_calculated_automatically_if_omitted(
    client, db, admin_user, coach_user, athlete_user, coach_token
):
    ctx = await _setup_assessment_fixture(db, admin_user, coach_user, athlete_user)

    # 60 + 80 + 100 = 240 / 3 = 80.0
    payload = {
        "athlete_id": ctx["athlete1_id"],
        "metrics": {"speed": 60.0, "passing": 80.0, "shooting": 100.0},
    }
    resp = await client.post("/api/v1/assessments", json=payload, headers=auth_headers(coach_token))
    assert resp.status_code == 201
    assert resp.json()["overall_score"] == 80.0


@pytest.mark.asyncio
async def test_custom_overall_score_preserved_if_provided(
    client, db, admin_user, coach_user, athlete_user, coach_token
):
    ctx = await _setup_assessment_fixture(db, admin_user, coach_user, athlete_user)

    payload = {
        "athlete_id": ctx["athlete1_id"],
        "metrics": {"speed": 60.0, "passing": 80.0, "shooting": 100.0},
        "overall_score": 85.5,
    }
    resp = await client.post("/api/v1/assessments", json=payload, headers=auth_headers(coach_token))
    assert resp.status_code == 201
    assert resp.json()["overall_score"] == 85.5


@pytest.mark.asyncio
async def test_notification_created_on_assessment(
    client, db, admin_user, coach_user, athlete_user, coach_token, athlete_token
):
    ctx = await _setup_assessment_fixture(db, admin_user, coach_user, athlete_user)

    payload = {
        "athlete_id": ctx["athlete1_id"],
        "metrics": {"speed": 92.0, "passing": 88.0},
    }
    resp = await client.post("/api/v1/assessments", json=payload, headers=auth_headers(coach_token))
    assert resp.status_code == 201

    # Check notification in db
    notif = await db.notifications.find_one({
        "recipient_user_id": athlete_user["_id"],
        "related_entity_type": "assessment",
    })
    assert notif is not None
    assert "assessment" in notif["title"].lower() or "assessment" in notif["message"].lower()

    # Check notification via athlete endpoint
    notif_resp = await client.get("/api/v1/notifications", headers=auth_headers(athlete_token))
    assert notif_resp.status_code == 200
    notifs = notif_resp.json()
    assert any(n.get("related_entity_type") == "assessment" for n in notifs)


@pytest.mark.asyncio
async def test_athlete_can_view_own_assessments(
    client, db, admin_user, coach_user, athlete_user, coach_token, athlete_token
):
    ctx = await _setup_assessment_fixture(db, admin_user, coach_user, athlete_user)

    # Coach creates assessment
    payload = {
        "athlete_id": ctx["athlete1_id"],
        "metrics": {"speed": 75.0},
        "remarks": "Self check viewable",
    }
    create_resp = await client.post("/api/v1/assessments", json=payload, headers=auth_headers(coach_token))
    assert create_resp.status_code == 201
    ass_id = create_resp.json()["id"]

    # Athlete lists assessments
    list_resp = await client.get("/api/v1/assessments", headers=auth_headers(athlete_token))
    assert list_resp.status_code == 200
    items = list_resp.json()
    assert len(items) >= 1
    assert any(item["id"] == ass_id for item in items)

    # Athlete gets history for own id
    hist_resp = await client.get(f"/api/v1/assessments/athlete/{ctx['athlete1_id']}", headers=auth_headers(athlete_token))
    assert hist_resp.status_code == 200
    assert len(hist_resp.json()) >= 1


@pytest.mark.asyncio
async def test_athlete_cannot_view_other_athlete_assessments(
    client, db, admin_user, coach_user, athlete_user, athlete_token
):
    ctx = await _setup_assessment_fixture(db, admin_user, coach_user, athlete_user)

    # Athlete 1 tries to view Athlete 2's assessments
    resp = await client.get(f"/api/v1/assessments/athlete/{ctx['athlete2_id']}", headers=auth_headers(athlete_token))
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_create_and_view_all_assessments(
    client, db, admin_user, coach_user, athlete_user, admin_token
):
    ctx = await _setup_assessment_fixture(db, admin_user, coach_user, athlete_user)

    # Admin creates assessment for Athlete 2
    payload = {
        "athlete_id": ctx["athlete2_id"],
        "sport_id": ctx["cricket_id"],
        "metrics": {"batting": 90.0, "bowling": 85.0},
        "remarks": "Admin recorded assessment",
    }
    resp = await client.post("/api/v1/assessments", json=payload, headers=auth_headers(admin_token))
    assert resp.status_code == 201
    assert resp.json()["overall_score"] == 87.5

    # Admin lists all assessments
    list_resp = await client.get("/api/v1/assessments", headers=auth_headers(admin_token))
    assert list_resp.status_code == 200
    items = list_resp.json()
    assert any(i["athlete_id"] == ctx["athlete2_id"] for i in items)


@pytest.mark.asyncio
async def test_assessment_updates_analytics_and_rankings(
    client, db, admin_user, coach_user, athlete_user, coach_token, admin_token
):
    ctx = await _setup_assessment_fixture(db, admin_user, coach_user, athlete_user)

    # Create assessment with score 88.0
    payload = {
        "athlete_id": ctx["athlete1_id"],
        "metrics": {"speed": 88.0, "endurance": 88.0},
    }
    resp = await client.post("/api/v1/assessments", json=payload, headers=auth_headers(coach_token))
    assert resp.status_code == 201

    # Check athlete analytics endpoint
    an_resp = await client.get(f"/api/v1/analytics/athlete/{ctx['athlete1_id']}", headers=auth_headers(coach_token))
    assert an_resp.status_code == 200
    an_data = an_resp.json()
    assert an_data["current_performance"]["score"] == 88.0

    # Check performance rankings endpoint
    rnk_resp = await client.get("/api/v1/rankings/performance", headers=auth_headers(admin_token))
    assert rnk_resp.status_code == 200
    rnk_items = rnk_resp.json()
    found = [r for r in rnk_items if r["athlete_id"] == ctx["athlete1_id"]]
    assert len(found) == 1
    assert found[0]["performance_score"] == 88.0
