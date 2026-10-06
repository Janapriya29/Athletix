from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.repositories.sport_repository import (
    add_sport_category,
    count_athletes_by_sport,
    count_sports,
    create_sport as repo_create_sport,
    delete_sport as repo_delete_sport,
    get_sport_by_id,
    get_sport_by_name,
    get_sport_categories,
    list_sports as repo_list_sports,
    update_sport as repo_update_sport,
)
from app.schemas.sport import (
    CategoryCreate,
    CategoryResponse,
    SportCreate,
    SportResponse,
    SportUpdate,
)


async def list_sports_service(
    db: AsyncIOMotorDatabase,
    role: str,
    search: str = None,
    is_active: bool = None,
    skip: int = 0,
    limit: int = 100,
) -> list[SportResponse]:
    # Non-admin users can only view active sports
    if role != "admin":
        is_active = True

    docs = await repo_list_sports(db, search=search, is_active=is_active, skip=skip, limit=limit)
    result = []
    for doc in docs:
        s_id = str(doc["_id"])
        ath_count = await count_athletes_by_sport(db, s_id)
        cats = await get_sport_categories(db, s_id)
        result.append(SportResponse.from_doc(doc, athlete_count=ath_count, categories=cats))
    return result


async def get_sport_service(db: AsyncIOMotorDatabase, sport_id: str) -> SportResponse:
    doc = await get_sport_by_id(db, sport_id)
    if not doc:
        raise NotFoundError(f"Sport with ID '{sport_id}' not found")
    ath_count = await count_athletes_by_sport(db, sport_id)
    cats = await get_sport_categories(db, sport_id)
    return SportResponse.from_doc(doc, athlete_count=ath_count, categories=cats)


async def create_sport_service(db: AsyncIOMotorDatabase, data: SportCreate) -> SportResponse:
    existing = await get_sport_by_name(db, data.name)
    if existing:
        raise ConflictError(f"Sport with name '{data.name}' already exists")

    doc = await repo_create_sport(
        db,
        name=data.name,
        description=data.description,
        category_type=data.category_type,
        is_active=data.is_active,
    )
    return SportResponse.from_doc(doc, athlete_count=0, categories=[])


async def update_sport_service(
    db: AsyncIOMotorDatabase, sport_id: str, data: SportUpdate
) -> SportResponse:
    existing = await get_sport_by_id(db, sport_id)
    if not existing:
        raise NotFoundError(f"Sport with ID '{sport_id}' not found")

    if data.name and data.name.strip().lower() != existing["name"].lower():
        dup = await get_sport_by_name(db, data.name)
        if dup and str(dup["_id"]) != sport_id:
            raise ConflictError(f"Sport with name '{data.name}' already exists")

    updated = await repo_update_sport(db, sport_id, data.model_dump(exclude_unset=True))
    ath_count = await count_athletes_by_sport(db, sport_id)
    cats = await get_sport_categories(db, sport_id)
    return SportResponse.from_doc(updated, athlete_count=ath_count, categories=cats)


async def set_sport_status_service(
    db: AsyncIOMotorDatabase, sport_id: str, is_active: bool
) -> SportResponse:
    existing = await get_sport_by_id(db, sport_id)
    if not existing:
        raise NotFoundError(f"Sport with ID '{sport_id}' not found")

    updated = await repo_update_sport(db, sport_id, {"is_active": is_active})
    ath_count = await count_athletes_by_sport(db, sport_id)
    cats = await get_sport_categories(db, sport_id)
    return SportResponse.from_doc(updated, athlete_count=ath_count, categories=cats)


async def delete_sport_service(db: AsyncIOMotorDatabase, sport_id: str) -> dict:
    existing = await get_sport_by_id(db, sport_id)
    if not existing:
        raise NotFoundError(f"Sport with ID '{sport_id}' not found")

    ath_count = await count_athletes_by_sport(db, sport_id)
    if ath_count > 0:
        # Prefer deactivation over destructive deletion when sport is referenced by athletes
        await repo_update_sport(db, sport_id, {"is_active": False})
        return {
            "message": f"Sport has {ath_count} athlete(s) assigned. Deactivated instead of deleted.",
            "deactivated": True,
        }

    await repo_delete_sport(db, sport_id)
    return {"message": "Sport deleted successfully", "deleted": True}


async def add_category_service(
    db: AsyncIOMotorDatabase, sport_id: str, data: CategoryCreate
) -> CategoryResponse:
    existing = await get_sport_by_id(db, sport_id)
    if not existing:
        raise NotFoundError(f"Sport with ID '{sport_id}' not found")

    doc = await add_sport_category(db, sport_id, data.name, data.description)
    return CategoryResponse.from_doc(doc)


async def list_categories_service(
    db: AsyncIOMotorDatabase, sport_id: str
) -> list[CategoryResponse]:
    existing = await get_sport_by_id(db, sport_id)
    if not existing:
        raise NotFoundError(f"Sport with ID '{sport_id}' not found")

    docs = await get_sport_categories(db, sport_id)
    return [CategoryResponse.from_doc(d) for d in docs]
