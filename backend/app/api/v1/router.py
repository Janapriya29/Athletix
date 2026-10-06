from fastapi import APIRouter

from app.api.v1.endpoints.athletes import router as athletes_router
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.coaches import router as coaches_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.sports import router as sports_router
from app.api.v1.endpoints.training import router as training_router
from app.api.v1.endpoints.users import router as users_router
from app.api.v1.endpoints.analytics import router as analytics_router
from app.api.v1.endpoints.notifications import router as notifications_router
from app.api.v1.endpoints.rankings import router as rankings_router
from app.api.v1.endpoints.reports import router as reports_router
from app.api.v1.endpoints.tournaments import router as tournaments_router

api_router = APIRouter()

api_router.include_router(health_router, prefix="")
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(sports_router)
api_router.include_router(coaches_router)
api_router.include_router(athletes_router)
api_router.include_router(training_router)
api_router.include_router(analytics_router)
api_router.include_router(tournaments_router)
api_router.include_router(rankings_router)
api_router.include_router(notifications_router)
api_router.include_router(reports_router)

