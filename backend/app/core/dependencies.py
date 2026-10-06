from typing import Annotated

from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_access_token

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

    return {"user_id": user_id, "role": role, "email": email}


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
