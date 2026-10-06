"""
Creates MongoDB indexes on application startup.
Indexes are created with if-not-exists semantics (Motor handles this safely).
"""
import logging

from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


async def create_indexes(db: AsyncIOMotorDatabase) -> None:
    # users
    await db.users.create_index("email", unique=True)

    # athletes
    await db.athletes.create_index("user_id")
    await db.athletes.create_index("sport_id")

    # coaches
    await db.coaches.create_index("user_id")

    # coach_athlete_assignments
    await db.coach_athlete_assignments.create_index([("coach_id", 1), ("athlete_id", 1)], unique=True)

    # training_sessions
    await db.training_sessions.create_index("date")
    await db.training_sessions.create_index("session_date")
    await db.training_sessions.create_index("coach_id")
    await db.training_sessions.create_index("sport_id")
    await db.training_sessions.create_index("status")

    # attendance
    await db.attendance.create_index([("session_id", 1), ("athlete_id", 1)], unique=True)
    await db.attendance.create_index("athlete_id")

    # performance_assessments
    await db.performance_assessments.create_index([("athlete_id", 1), ("date", -1)])

    # tournaments
    await db.tournaments.create_index("start_date")

    # tournament_participants
    await db.tournament_participants.create_index([("tournament_id", 1), ("athlete_id", 1)])

    # notifications
    await db.notifications.create_index([("user_id", 1), ("is_read", 1)])
    await db.notifications.create_index([("recipient_user_id", 1), ("is_read", 1)])
    await db.notifications.create_index([("created_at", -1)])

    logger.info("MongoDB indexes ensured.")
