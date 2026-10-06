"""
create_admin.py — Create an admin user interactively.

Usage (local):
    cd backend
    python ../scripts/create_admin.py

Usage (Docker):
    docker exec -it athletix_backend python scripts/create_admin.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Allow running from either the project root or the backend directory
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv

load_dotenv(backend_dir / ".env")

import bcrypt as _bcrypt
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "athletix")


def _hash(plain: str) -> str:
    return _bcrypt.hashpw(plain.encode("utf-8"), _bcrypt.gensalt()).decode("utf-8")


async def create_admin():
    print("\n=== Athletix Admin Creation ===\n")

    email = input("Admin email: ").strip()
    if not email:
        print("Email cannot be empty.")
        return

    full_name = input("Full name: ").strip() or "Admin"

    import getpass
    password = getpass.getpass("Password (min 8 chars): ")
    if len(password) < 8:
        print("Password must be at least 8 characters.")
        return

    client = AsyncIOMotorClient(MONGO_URI)
    db = client[MONGO_DB_NAME]

    existing = await db.users.find_one({"email": email})
    if existing:
        print(f"\nA user with email '{email}' already exists.")
        client.close()
        return

    from datetime import datetime, timezone

    user_doc = {
        "email": email,
        "hashed_password": _hash(password),
        "full_name": full_name,
        "role": "admin",
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }

    result = await db.users.insert_one(user_doc)
    client.close()

    print(f"\nAdmin created successfully.")
    print(f"  ID:    {result.inserted_id}")
    print(f"  Email: {email}")
    print(f"  Name:  {full_name}")
    print(f"  Role:  admin\n")


if __name__ == "__main__":
    asyncio.run(create_admin())
