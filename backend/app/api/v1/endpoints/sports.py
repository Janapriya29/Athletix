from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import get_current_user, require_admin
from app.db.database import get_database
from app.schemas.sport import (
    CategoryCreate,
    CategoryResponse,
    SportCreate,
    SportResponse,
    SportStatusUpdate,
    SportUpdate,
)
from app.services.sport_service import (
    add_category_service,
    create_sport_service,
    delete_sport_service,
    get_sport_service,
    list_categories_service,
    list_sports_service,
    set_sport_status_service,
    update_sport_service,
)

router = APIRouter(prefix="/sports", tags=["Sports"])


@router.get("", response_model=list[SportResponse])
async def list_sports(
    current_user: Annotated[dict, Depends(get_current_user)],
    search: Optional[str] = Query(default=None, description="Search by name"),
    is_active: Optional[bool] = Query(default=None, description="Filter by status"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
):
    """
    List sports.
    Admin sees all sports (or filtered by is_active).
    Coach and Athlete roles only see active sports.
    """
    db = get_database()
    return await list_sports_service(
        db,
        role=current_user["role"],
        search=search,
        is_active=is_active,
        skip=skip,
        limit=limit,
    )


@router.post("", response_model=SportResponse, status_code=status.HTTP_201_CREATED)
async def create_sport(
    body: SportCreate,
    current_user: Annotated[dict, Depends(require_admin)],
):
    """Create a new sport. Admin only."""
    db = get_database()
    return await create_sport_service(db, body)


@router.get("/{sport_id}", response_model=SportResponse)
async def get_sport(
    sport_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Get single sport with metric categories. All authenticated users."""
    db = get_database()
    return await get_sport_service(db, sport_id)


@router.put("/{sport_id}", response_model=SportResponse)
async def update_sport(
    sport_id: str,
    body: SportUpdate,
    current_user: Annotated[dict, Depends(require_admin)],
):
    """Update sport information. Admin only."""
    db = get_database()
    return await update_sport_service(db, sport_id, body)


@router.patch("/{sport_id}/status", response_model=SportResponse)
async def set_sport_status(
    sport_id: str,
    body: SportStatusUpdate,
    current_user: Annotated[dict, Depends(require_admin)],
):
    """Activate or deactivate a sport. Admin only."""
    db = get_database()
    return await set_sport_status_service(db, sport_id, body.is_active)


@router.delete("/{sport_id}")
async def delete_sport(
    sport_id: str,
    current_user: Annotated[dict, Depends(require_admin)],
):
    """
    Delete or deactivate a sport. Admin only.
    If athletes are assigned to this sport, deactivates it instead of deleting.
    """
    db = get_database()
    return await delete_sport_service(db, sport_id)


@router.get("/{sport_id}/categories", response_model=list[CategoryResponse])
async def list_categories(
    sport_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """List metric categories for a sport. All authenticated users."""
    db = get_database()
    return await list_categories_service(db, sport_id)


@router.post("/{sport_id}/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def add_category(
    sport_id: str,
    body: CategoryCreate,
    current_user: Annotated[dict, Depends(require_admin)],
):
    """Add a metric category to a sport. Admin only."""
    db = get_database()
    return await add_category_service(db, sport_id, body)
