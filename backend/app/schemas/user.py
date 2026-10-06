from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserResponse(BaseModel):
    """Returned to the client — never includes hashed_password."""
    id: str
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    @classmethod
    def from_doc(cls, doc: dict) -> "UserResponse":
        return cls(
            id=str(doc["_id"]),
            email=doc["email"],
            full_name=doc["full_name"],
            role=doc["role"],
            is_active=doc.get("is_active", True),
            created_at=doc.get("created_at", datetime.utcnow()),
            updated_at=doc.get("updated_at"),
        )


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=8, max_length=128)
    role: str = Field(pattern="^(admin|coach|athlete)$")


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=128)
    role: Optional[str] = Field(default=None, pattern="^(admin|coach|athlete)$")
    is_active: Optional[bool] = None


class UserStatusUpdate(BaseModel):
    is_active: bool
