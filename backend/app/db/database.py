from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import settings

# Module-level client — initialized on startup, closed on shutdown
_client: AsyncIOMotorClient | None = None


async def connect_to_mongo() -> None:
    global _client
    _client = AsyncIOMotorClient(settings.MONGO_URI)
    # Verify the connection is live
    await _client.admin.command("ping")


async def close_mongo_connection() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None


def get_database() -> AsyncIOMotorDatabase:
    if _client is None:
        raise RuntimeError("MongoDB client is not initialized. Call connect_to_mongo() first.")
    return _client[settings.MONGO_DB_NAME]
