"""
Health endpoint smoke tests.
These run without a live MongoDB (the DB ping will fail gracefully and report unavailable).
"""
import pytest


@pytest.mark.asyncio
async def test_root_endpoint(client):
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Welcome to Athletix API"


@pytest.mark.asyncio
async def test_health_endpoint_reachable(client):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["app"] == "Athletix"
    assert "database" in data
