"""
Users endpoint — provides user management with role-based access control.

GET   /users              Admin only — list/search/filter users
POST  /users              Admin only — create a user
GET   /users/{id}         Admin only (any user) or authenticated user (own profile)
PUT   /users/{id}         Admin only — update user details
PATCH /users/{id}/status  Admin only — activate/deactivate user
"""
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import get_current_user, require_admin
from app.core.exceptions import ForbiddenError
from app.db.database import get_database
from app.schemas.user import UserCreate, UserResponse, UserStatusUpdate, UserUpdate
from app.services.user_service import (
    create_user_service,
    get_user_service,
    list_users_service,
    set_user_status_service,
    update_user_service,
)

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=list[UserResponse])
async def list_all_users(
    current_user: Annotated[dict, Depends(require_admin)],
    search: Optional[str] = Query(default=None, description="Search by name or email"),
    role: Optional[str] = Query(default=None, description="Filter by role"),
    is_active: Optional[bool] = Query(default=None, description="Filter by active status"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
):
    """List all users with search and filtering. Admin only."""
    db = get_database()
    return await list_users_service(
        db, search=search, role=role, is_active=is_active, skip=skip, limit=limit
    )


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_new_user(
    body: UserCreate,
    current_user: Annotated[dict, Depends(require_admin)],
):
    """Create a user. Admin only."""
    db = get_database()
    return await create_user_service(db, body)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """
    Get a user by ID.
    Admin can fetch any user.
    Non-admin users can only fetch their own profile.
    """
    if current_user["role"] != "admin" and current_user["user_id"] != user_id:
        raise ForbiddenError("You can only view your own profile")

    db = get_database()
    return await get_user_service(db, user_id)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    body: UserUpdate,
    current_user: Annotated[dict, Depends(require_admin)],
):
    """Update user information (name, role, status). Admin only."""
    db = get_database()
    return await update_user_service(db, user_id, body)


@router.patch("/{user_id}/status", response_model=UserResponse)
async def set_user_status(
    user_id: str,
    body: UserStatusUpdate,
    current_user: Annotated[dict, Depends(require_admin)],
):
    """Activate or deactivate a user account. Admin only."""
    db = get_database()
    return await set_user_status_service(db, user_id, body.is_active)
