"""
Shared pytest fixtures for Athletix backend tests.

Strategy:
- Each test gets a fresh function-scoped Motor client and database.
- The app's get_database() is monkeypatched to return the test DB so the
  app's lifespan MongoDB connection is bypassed cleanly.
- Tests run against athletix_test — the development DB is never touched.
- Collections are wiped before each test for full isolation.
"""
import os
import pytest

# Must be set before any app module is imported so pydantic-settings picks them up
os.environ["MONGO_URI"] = "mongodb://localhost:27017"
os.environ["MONGO_DB_NAME"] = "athletix_test"
os.environ["JWT_SECRET"] = "test-secret-do-not-use-in-production"

from httpx import ASGITransport, AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient

# Import app AFTER env vars are set
import app.db.database as _db_module
from app.main import app
from app.core.security import hash_password

# Hardcode test DB name to guarantee isolation regardless of Settings cache
_TEST_MONGO_URI = "mongodb://localhost:27017"
_TEST_DB_NAME = "athletix_test"


# ── Per-test database ──────────────────────────────────────────────────────────

@pytest.fixture
async def db():
    """
    Fresh Motor database for each test.
    Patches app.db.database._client so get_database() returns the test DB.
    Drops all collections before each test.
    """
    client = AsyncIOMotorClient(_TEST_MONGO_URI)
    database = client[_TEST_DB_NAME]

    # Drop all collections for clean state
    for coll in await database.list_collection_names():
        await database.drop_collection(coll)

    # Create indexes
    from app.db.indexes import create_indexes
    await create_indexes(database)

    # Patch the module-level client so get_database() works inside the app
    _db_module._client = client

    yield database

    # Cleanup
    _db_module._client = None
    client.close()


# ── HTTP client ────────────────────────────────────────────────────────────────

@pytest.fixture
async def client(db):
    """
    Async test client. Depends on db so the database is always patched first.
    lifespan=False prevents the app from trying to connect to MongoDB itself.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


# ── User factories ─────────────────────────────────────────────────────────────

async def _create_test_user(
    db,
    email: str,
    password: str,
    role: str,
    full_name: str = None,
    is_active: bool = True,
) -> dict:
    from datetime import datetime, timezone
    doc = {
        "email": email,
        "full_name": full_name or f"Test {role.capitalize()}",
        "hashed_password": hash_password(password),
        "role": role,
        "is_active": is_active,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    result = await db.users.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


@pytest.fixture
async def admin_user(db):
    return await _create_test_user(db, "admin@test.com", "Admin@test123", "admin")


@pytest.fixture
async def coach_user(db):
    return await _create_test_user(db, "coach@test.com", "Coach@test123", "coach")


@pytest.fixture
async def athlete_user(db):
    return await _create_test_user(db, "athlete@test.com", "Athlete@test123", "athlete")


@pytest.fixture
async def inactive_user(db):
    return await _create_test_user(
        db, "inactive@test.com", "Inactive@test123", "athlete", is_active=False
    )


# ── Token helpers ──────────────────────────────────────────────────────────────

def _make_token(user_doc: dict) -> str:
    from app.core.security import create_access_token
    return create_access_token({
        "sub": str(user_doc["_id"]),
        "role": user_doc["role"],
        "email": user_doc["email"],
    })


@pytest.fixture
async def admin_token(admin_user):
    return _make_token(admin_user)


@pytest.fixture
async def coach_token(coach_user):
    return _make_token(coach_user)


@pytest.fixture
async def athlete_token(athlete_user):
    return _make_token(athlete_user)
