from fastapi import APIRouter
from app.db.database import get_database

router = APIRouter()


@router.get("/health", tags=["Health"])
async def health_check():
    """
    Returns application health status and verifies MongoDB connectivity.
    """
    try:
        db = get_database()
        # Lightweight ping to verify the DB is reachable
        await db.command("ping")
        db_status = "connected"
    except Exception as exc:
        db_status = f"unavailable: {str(exc)}"

    return {
        "status": "ok",
        "app": "Athletix",
        "version": "1.0.0",
        "database": db_status,
    }
