from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class SportCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    category_type: Optional[str] = Field(default=None, max_length=100)
    is_active: bool = True


class SportUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    category_type: Optional[str] = Field(default=None, max_length=100)
    is_active: Optional[bool] = None


class SportStatusUpdate(BaseModel):
    is_active: bool


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)


class CategoryResponse(BaseModel):
    id: str
    sport_id: str
    name: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None

    @classmethod
    def from_doc(cls, doc: dict) -> "CategoryResponse":
        return cls(
            id=str(doc["_id"]),
            sport_id=str(doc.get("sport_id", "")),
            name=doc["name"],
            description=doc.get("description"),
            created_at=doc.get("created_at"),
        )


class SportResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    category_type: Optional[str] = None
    is_active: bool
    athlete_count: int = 0
    categories: list[CategoryResponse] = []
    created_at: datetime
    updated_at: Optional[datetime] = None

    @classmethod
    def from_doc(cls, doc: dict, athlete_count: int = 0, categories: list[dict] = None) -> "SportResponse":
        cats = [CategoryResponse.from_doc(c) for c in (categories or [])]
        return cls(
            id=str(doc["_id"]),
            name=doc["name"],
            description=doc.get("description"),
            category_type=doc.get("category_type"),
            is_active=doc.get("is_active", True),
            athlete_count=athlete_count,
            categories=cats,
            created_at=doc.get("created_at", datetime.utcnow()),
            updated_at=doc.get("updated_at"),
        )
