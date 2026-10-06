import re
from datetime import datetime, timezone
from typing import Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase


async def get_sport_by_id(db: AsyncIOMotorDatabase, sport_id: str) -> Optional[dict]:
    try:
        oid = ObjectId(sport_id)
    except Exception:
        return None
    return await db.sports.find_one({"_id": oid})


async def get_sport_by_name(db: AsyncIOMotorDatabase, name: str) -> Optional[dict]:
    # Case-insensitive match
    return await db.sports.find_one({"name": {"$regex": f"^{re.escape(name.strip())}$", "$options": "i"}})


async def list_sports(
    db: AsyncIOMotorDatabase,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
) -> list[dict]:
    query = {}
    if search:
        query["name"] = {"$regex": re.escape(search.strip()), "$options": "i"}
    if is_active is not None:
        query["is_active"] = is_active

    cursor = db.sports.find(query).sort("name", 1).skip(skip).limit(limit)
    return await cursor.to_list(length=limit)


async def count_sports(
    db: AsyncIOMotorDatabase,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
) -> int:
    query = {}
    if search:
        query["name"] = {"$regex": re.escape(search.strip()), "$options": "i"}
    if is_active is not None:
        query["is_active"] = is_active
    return await db.sports.count_documents(query)


async def create_sport(
    db: AsyncIOMotorDatabase,
    name: str,
    description: Optional[str] = None,
    category_type: Optional[str] = None,
    is_active: bool = True,
) -> dict:
    now = datetime.now(timezone.utc)
    doc = {
        "name": name.strip(),
        "description": description.strip() if description else None,
        "category_type": category_type.strip() if category_type else None,
        "is_active": is_active,
        "created_at": now,
        "updated_at": now,
    }
    result = await db.sports.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


async def update_sport(
    db: AsyncIOMotorDatabase,
    sport_id: str,
    update_data: dict,
) -> Optional[dict]:
    try:
        oid = ObjectId(sport_id)
    except Exception:
        return None

    update_fields = {}
    for key, val in update_data.items():
        if val is not None:
            update_fields[key] = val.strip() if isinstance(val, str) else val

    if not update_fields:
        return await db.sports.find_one({"_id": oid})

    update_fields["updated_at"] = datetime.now(timezone.utc)
    await db.sports.update_one({"_id": oid}, {"$set": update_fields})
    return await db.sports.find_one({"_id": oid})


async def count_athletes_by_sport(db: AsyncIOMotorDatabase, sport_id: str) -> int:
    try:
        oid = ObjectId(sport_id)
    except Exception:
        return 0
    # Athlete can have sport_id or additional_sport_ids
    return await db.athletes.count_documents({"$or": [{"sport_id": oid}, {"additional_sport_ids": oid}]})


async def delete_sport(db: AsyncIOMotorDatabase, sport_id: str) -> bool:
    try:
        oid = ObjectId(sport_id)
    except Exception:
        return False
    result = await db.sports.delete_one({"_id": oid})
    return result.deleted_count > 0


async def get_sport_categories(db: AsyncIOMotorDatabase, sport_id: str) -> list[dict]:
    try:
        oid = ObjectId(sport_id)
    except Exception:
        return []
    cursor = db.categories.find({"sport_id": oid}).sort("name", 1)
    return await cursor.to_list(length=100)


async def add_sport_category(
    db: AsyncIOMotorDatabase,
    sport_id: str,
    name: str,
    description: Optional[str] = None,
) -> dict:
    oid = ObjectId(sport_id)
    now = datetime.now(timezone.utc)
    doc = {
        "sport_id": oid,
        "name": name.strip(),
        "description": description.strip() if description else None,
        "created_at": now,
    }
    result = await db.categories.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc
