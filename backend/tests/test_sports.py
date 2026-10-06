"""
Sports management tests — Phase 2.
"""
import pytest


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_admin_can_create_sport(client, admin_token):
    payload = {"name": "Tennis", "description": "Racket sport", "category_type": "Racquet"}
    resp = await client.post("/api/v1/sports", json=payload, headers=auth_headers(admin_token))
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["name"] == "Tennis"
    assert data["description"] == "Racket sport"
    assert data["is_active"] is True
    assert "id" in data


@pytest.mark.asyncio
async def test_duplicate_sport_rejected(client, admin_token):
    payload = {"name": "Swimming", "description": "Water sport"}
    resp1 = await client.post("/api/v1/sports", json=payload, headers=auth_headers(admin_token))
    assert resp1.status_code == 201

    # Case-insensitive duplicate
    resp2 = await client.post(
        "/api/v1/sports",
        json={"name": "swimming", "description": "Another water sport"},
        headers=auth_headers(admin_token),
    )
    assert resp2.status_code == 409
    assert "already exists" in resp2.json()["detail"]


@pytest.mark.asyncio
async def test_coach_cannot_create_sport(client, coach_token):
    resp = await client.post(
        "/api/v1/sports",
        json={"name": "Handball"},
        headers=auth_headers(coach_token),
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_athlete_cannot_create_sport(client, athlete_token):
    resp = await client.post(
        "/api/v1/sports",
        json={"name": "Handball"},
        headers=auth_headers(athlete_token),
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_unauthenticated_sports_rejected(client):
    resp = await client.get("/api/v1/sports")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_admin_can_update_sport(client, admin_token):
    create_resp = await client.post(
        "/api/v1/sports",
        json={"name": "Volleyball", "description": "Team sport"},
        headers=auth_headers(admin_token),
    )
    sport_id = create_resp.json()["id"]

    update_resp = await client.put(
        f"/api/v1/sports/{sport_id}",
        json={"description": "Updated team volleyball"},
        headers=auth_headers(admin_token),
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["description"] == "Updated team volleyball"


@pytest.mark.asyncio
async def test_admin_can_deactivate_sport(client, admin_token, athlete_token):
    create_resp = await client.post(
        "/api/v1/sports",
        json={"name": "Archery"},
        headers=auth_headers(admin_token),
    )
    sport_id = create_resp.json()["id"]

    # Deactivate
    patch_resp = await client.patch(
        f"/api/v1/sports/{sport_id}/status",
        json={"is_active": False},
        headers=auth_headers(admin_token),
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["is_active"] is False

    # Athlete should NOT see inactive sport in list
    list_resp = await client.get("/api/v1/sports", headers=auth_headers(athlete_token))
    names = [s["name"] for s in list_resp.json()]
    assert "Archery" not in names


@pytest.mark.asyncio
async def test_list_sports_search(client, admin_token):
    await client.post("/api/v1/sports", json={"name": "Baseball"}, headers=auth_headers(admin_token))
    await client.post("/api/v1/sports", json={"name": "Basketball Pro"}, headers=auth_headers(admin_token))

    resp = await client.get("/api/v1/sports?search=base", headers=auth_headers(admin_token))
    assert resp.status_code == 200
    names = [s["name"] for s in resp.json()]
    assert "Baseball" in names
