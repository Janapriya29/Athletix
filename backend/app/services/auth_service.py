"""
Auth service — business logic for authentication operations.
Coordinates between the repository, security utilities, and schema validation.
"""
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.exceptions import BadRequestError, ConflictError, UnauthorizedError
from app.core.security import create_access_token, verify_password
from app.repositories.user_repository import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    update_user_password,
)
from app.schemas.auth import RegisterRequest, RegisterResponse, TokenResponse
from app.schemas.user import UserResponse


async def login_user(db: AsyncIOMotorDatabase, email: str, password: str) -> TokenResponse:
    """Validate credentials and return a JWT token."""
    user = await get_user_by_email(db, email)

    # Use a consistent error for both wrong email and wrong password
    # to avoid leaking which field was incorrect (timing-safe messaging)
    if user is None or not verify_password(password, user["hashed_password"]):
        raise UnauthorizedError("Invalid email or password")

    if not user.get("is_active", True):
        raise UnauthorizedError("Account is inactive")

    token = create_access_token(
        data={
            "sub": str(user["_id"]),
            "role": user["role"],
            "email": user["email"],
        }
    )
    return TokenResponse(access_token=token)


async def get_user_profile(db: AsyncIOMotorDatabase, user_id: str) -> UserResponse:
    """Return the full profile for the authenticated user."""
    user = await get_user_by_id(db, user_id)
    if user is None:
        raise UnauthorizedError("User not found")
    return UserResponse.from_doc(user)


async def change_password(
    db: AsyncIOMotorDatabase,
    user_id: str,
    current_password: str,
    new_password: str,
) -> None:
    """Verify the current password then store the new hash."""
    user = await get_user_by_id(db, user_id)
    if user is None:
        raise UnauthorizedError("User not found")

    if not verify_password(current_password, user["hashed_password"]):
        raise BadRequestError("Current password is incorrect")

    if current_password == new_password:
        raise BadRequestError("New password must differ from the current password")

    await update_user_password(db, user_id, new_password)


async def register_user(db: AsyncIOMotorDatabase, data: RegisterRequest) -> RegisterResponse:
    """
    Public account registration.
    - Athlete: Active immediately, athlete record created.
    - Coach: Inactive pending Admin approval, coach record created.
    - Admin: Inactive pending approval; arbitrary public admin escalation prevented.
    """
    existing = await get_user_by_email(db, data.email)
    if existing:
        raise ConflictError("A user with this email already exists")

    role = data.role.strip().lower()
    now = datetime.now(timezone.utc)

    if role == "athlete":
        is_active = True
        status = "active"
        message = "Your Athletix account has been created."
    elif role == "coach":
        is_active = False
        status = "pending_approval"
        message = "Your Coach account request has been submitted for Admin approval."
    elif role == "admin":
        is_active = False
        status = "pending_approval"
        message = "Your Admin access request requires administrator approval."
    else:
        raise BadRequestError(f"Unsupported role '{role}'")

    user_doc = await create_user(
        db,
        email=data.email,
        full_name=data.full_name,
        plain_password=data.password,
        role=role,
        is_active=is_active,
    )

    if role == "athlete":
        await db.athletes.insert_one({
            "user_id": user_doc["_id"],
            "full_name": user_doc["full_name"],
            "email": user_doc["email"],
            "sport_id": None,
            "coach_id": None,
            "status": "active",
            "created_at": now,
            "updated_at": now,
        })
    elif role == "coach":
        await db.coaches.insert_one({
            "user_id": user_doc["_id"],
            "full_name": user_doc["full_name"],
            "email": user_doc["email"],
            "sport_ids": [],
            "status": "pending",
            "created_at": now,
            "updated_at": now,
        })

    return RegisterResponse(
        id=str(user_doc["_id"]),
        email=user_doc["email"],
        full_name=user_doc["full_name"],
        role=user_doc["role"],
        is_active=is_active,
        status=status,
        message=message,
    )

