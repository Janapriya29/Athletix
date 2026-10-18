"""
User repository — all MongoDB queries for the users collection live here.
No business logic; just clean database operations.
"""
import re
from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.security import hash_password


async def get_user_by_email(db: AsyncIOMotorDatabase, email: str) -> Optional[dict]:
    clean_email = email.strip().lower() if isinstance(email, str) else ""
    if not clean_email:
        return None
    # 1. Exact match on normalized email
    user = await db.users.find_one({"email": clean_email})
    if user:
        return user
    # 2. Case-insensitive and whitespace-tolerant regex match fallback
    escaped = re.escape(clean_email)
    user = await db.users.find_one({"email": {"$regex": f"^\\s*{escaped}\\s*$", "$options": "i"}})
    if user:
        # Self-heal stored email for consistency
        await db.users.update_one({"_id": user["_id"]}, {"$set": {"email": clean_email}})
        user["email"] = clean_email
    return user


async def get_user_by_id(db: AsyncIOMotorDatabase, user_id: str) -> Optional[dict]:
    try:
        oid = ObjectId(user_id)
    except Exception:
        return None
    return await db.users.find_one({"_id": oid})


async def create_user(
    db: AsyncIOMotorDatabase,
    email: str,
    full_name: str,
    plain_password: str,
    role: str,
    is_active: bool = True,
    status: Optional[str] = None,
) -> dict:
    now = datetime.now(timezone.utc)
    clean_email = email.strip().lower()
    doc = {
        "email": clean_email,
        "full_name": full_name.strip(),
        "hashed_password": hash_password(plain_password),
        "role": role,
        "is_active": is_active,
        "status": status or ("active" if is_active else "pending_approval"),
        "created_at": now,
        "updated_at": now,
    }
    result = await db.users.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


async def update_user(
    db: AsyncIOMotorDatabase, user_id: str, update_data: dict
) -> Optional[dict]:
    try:
        oid = ObjectId(user_id)
    except Exception:
        return None

    update_fields = {}
    for key, val in update_data.items():
        if val is not None:
            if key == "email" and isinstance(val, str):
                update_fields[key] = val.strip().lower()
            elif isinstance(val, str):
                update_fields[key] = val.strip()
            else:
                update_fields[key] = val

    if not update_fields:
        return await db.users.find_one({"_id": oid})

    update_fields["updated_at"] = datetime.now(timezone.utc)
    await db.users.update_one({"_id": oid}, {"$set": update_fields})
    return await db.users.find_one({"_id": oid})


async def set_user_status(
    db: AsyncIOMotorDatabase, user_id: str, is_active: bool
) -> Optional[dict]:
    try:
        oid = ObjectId(user_id)
    except Exception:
        return None
    now = datetime.now(timezone.utc)
    status_str = "active" if is_active else "inactive"
    await db.users.update_one(
        {"_id": oid},
        {"$set": {"is_active": is_active, "status": status_str, "updated_at": now}}
    )
    # Also update linked coach or athlete profile status if present
    await db.coaches.update_one({"user_id": oid}, {"$set": {"status": status_str, "updated_at": now}})
    await db.athletes.update_one({"user_id": oid}, {"$set": {"status": status_str, "updated_at": now}})
    return await db.users.find_one({"_id": oid})


async def update_user_password(
    db: AsyncIOMotorDatabase, user_id: str, new_plain_password: str
) -> None:
    oid = ObjectId(user_id)
    await db.users.update_one(
        {"_id": oid},
        {
            "$set": {
                "hashed_password": hash_password(new_plain_password),
                "updated_at": datetime.now(timezone.utc),
            }
        },
    )


async def list_users(
    db: AsyncIOMotorDatabase,
    search: Optional[str] = None,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
) -> list[dict]:
    query = {}
    if search:
        pattern = re.escape(search.strip())
        query["$or"] = [
            {"email": {"$regex": pattern, "$options": "i"}},
            {"full_name": {"$regex": pattern, "$options": "i"}},
        ]
    if role:
        query["role"] = role
    if is_active is not None:
        query["is_active"] = is_active

    cursor = db.users.find(query, {"hashed_password": 0}).sort("created_at", -1).skip(skip).limit(limit)
    return await cursor.to_list(length=limit)


async def count_users(
    db: AsyncIOMotorDatabase,
    search: Optional[str] = None,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
) -> int:
    query = {}
    if search:
        pattern = re.escape(search.strip())
        query["$or"] = [
            {"email": {"$regex": pattern, "$options": "i"}},
            {"full_name": {"$regex": pattern, "$options": "i"}},
        ]
    if role:
        query["role"] = role
    if is_active is not None:
        query["is_active"] = is_active

    return await db.users.count_documents(query)
