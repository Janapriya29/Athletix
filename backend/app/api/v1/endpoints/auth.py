from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.dependencies import get_current_user
from app.db.database import get_database
from app.schemas.auth import ChangePasswordRequest, RegisterRequest, RegisterResponse, TokenResponse
from app.schemas.user import UserResponse
from app.services.auth_service import change_password, get_user_profile, login_user, register_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
):
    """
    Public account registration.
    - Athlete accounts are active immediately.
    - Coach and Admin accounts require administrator approval.
    """
    db = get_database()
    return await register_user(db, body)


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
):
    """
    Authenticate with email + password.
    Returns a JWT access token on success.
    FastAPI's OAuth2PasswordRequestForm maps `username` field to email.
    """
    db = get_database()
    return await login_user(db, email=form_data.username, password=form_data.password)


@router.post("/logout")
async def logout(
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """
    JWT is stateless — the server has no token to invalidate.
    The client must discard the stored token.
    This endpoint confirms the logout action and returns a clean response.
    """
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Return the authenticated user's profile."""
    db = get_database()
    return await get_user_profile(db, current_user["user_id"])


@router.post("/change-password")
async def change_password_endpoint(
    body: ChangePasswordRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Change the authenticated user's password."""
    db = get_database()
    await change_password(
        db,
        user_id=current_user["user_id"],
        current_password=body.current_password,
        new_password=body.new_password,
    )
    return {"message": "Password updated successfully"}
