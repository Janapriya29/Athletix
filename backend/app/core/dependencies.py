from typing import Annotated

from bson import ObjectId
from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_access_token
from app.db.database import get_database

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> dict:
    if not credentials:
        raise UnauthorizedError()

    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise UnauthorizedError("Invalid or expired token")

    user_id = payload.get("sub")
    role = payload.get("role")
    email = payload.get("email")

    if not user_id or not role:
        raise UnauthorizedError("Malformed token")

    try:
        user_oid = ObjectId(user_id)
    except Exception:
        raise UnauthorizedError("Invalid user identity in token")

    db = get_database()
    user = await db.users.find_one({"_id": user_oid})
    if not user:
        raise UnauthorizedError("User does not exist")

    # Inactive or pending users cannot access protected APIs even with a valid or stale token
    if not user.get("is_active", True) or user.get("status") in [
        "inactive",
        "pending_approval",
        "suspended",
        "rejected",
    ]:
        raise UnauthorizedError("Account is inactive or pending approval")

    return {
        "user_id": str(user["_id"]),
        "role": user.get("role", role),
        "email": user.get("email", email),
    }


def require_role(*roles: str):
    """Factory that returns a dependency enforcing one of the given roles."""

    async def role_checker(current_user: Annotated[dict, Depends(get_current_user)]) -> dict:
        if current_user["role"] not in roles:
            raise ForbiddenError()
        return current_user

    return role_checker


# Convenience role dependencies
require_admin = require_role("admin")
require_coach = require_role("admin", "coach")
require_athlete = require_role("admin", "coach", "athlete")
