from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.exceptions import ConflictError, NotFoundError
from app.repositories.user_repository import (
    count_users,
    create_user as repo_create_user,
    get_user_by_email,
    get_user_by_id,
    list_users as repo_list_users,
    set_user_status as repo_set_user_status,
    update_user as repo_update_user,
)
from app.schemas.user import UserCreate, UserResponse, UserUpdate


async def list_users_service(
    db: AsyncIOMotorDatabase,
    search: str = None,
    role: str = None,
    is_active: bool = None,
    skip: int = 0,
    limit: int = 100,
) -> list[UserResponse]:
    docs = await repo_list_users(
        db, search=search, role=role, is_active=is_active, skip=skip, limit=limit
    )
    return [UserResponse.from_doc(d) for d in docs]


async def get_user_service(db: AsyncIOMotorDatabase, user_id: str) -> UserResponse:
    doc = await get_user_by_id(db, user_id)
    if not doc:
        raise NotFoundError("User not found")
    return UserResponse.from_doc(doc)


async def create_user_service(db: AsyncIOMotorDatabase, data: UserCreate) -> UserResponse:
    from datetime import datetime, timezone

    clean_email = data.email.strip().lower()
    existing = await get_user_by_email(db, clean_email)
    if existing:
        raise ConflictError("A user with this email already exists")

    is_active = data.is_active if data.is_active is not None else True
    status = "active" if is_active else "inactive"

    doc = await repo_create_user(
        db,
        email=clean_email,
        full_name=data.full_name.strip(),
        plain_password=data.password,
        role=data.role,
        is_active=is_active,
        status=status,
    )

    now = datetime.now(timezone.utc)
    if data.role == "athlete":
        await db.athletes.insert_one({
            "user_id": doc["_id"],
            "full_name": doc["full_name"],
            "email": doc["email"],
            "sport_id": None,
            "coach_id": None,
            "status": "active" if is_active else "inactive",
            "created_at": now,
            "updated_at": now,
        })
    elif data.role == "coach":
        await db.coaches.insert_one({
            "user_id": doc["_id"],
            "full_name": doc["full_name"],
            "email": doc["email"],
            "sport_ids": [],
            "status": "active" if is_active else "inactive",
            "created_at": now,
            "updated_at": now,
        })

    return UserResponse.from_doc(doc)


async def update_user_service(
    db: AsyncIOMotorDatabase, user_id: str, data: UserUpdate
) -> UserResponse:
    existing = await get_user_by_id(db, user_id)
    if not existing:
        raise NotFoundError("User not found")

    update_dict = data.model_dump(exclude_unset=True)
    updated = await repo_update_user(db, user_id, update_dict)
    return UserResponse.from_doc(updated)


async def set_user_status_service(
    db: AsyncIOMotorDatabase, user_id: str, is_active: bool
) -> UserResponse:
    existing = await get_user_by_id(db, user_id)
    if not existing:
        raise NotFoundError("User not found")

    updated = await repo_set_user_status(db, user_id, is_active)
    return UserResponse.from_doc(updated)
