from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class CoachSportInfo(BaseModel):
    id: str
    name: str


class CoachCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=128)
    email: EmailStr
    password: Optional[str] = Field(default=None, min_length=8, max_length=128)
    phone: Optional[str] = Field(default=None, max_length=32)
    specialization: Optional[str] = Field(default=None, max_length=128)
    experience_years: Optional[int] = Field(default=0, ge=0, le=70)
    sport_ids: Optional[list[str]] = []
    bio: Optional[str] = Field(default=None, max_length=1000)
    status: str = Field(default="active", pattern="^(active|inactive)$")


class CoachUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=128)
    phone: Optional[str] = Field(default=None, max_length=32)
    specialization: Optional[str] = Field(default=None, max_length=128)
    experience_years: Optional[int] = Field(default=None, ge=0, le=70)
    sport_ids: Optional[list[str]] = None
    bio: Optional[str] = Field(default=None, max_length=1000)
    status: Optional[str] = Field(default=None, pattern="^(active|inactive)$")


class CoachStatusUpdate(BaseModel):
    status: str = Field(pattern="^(active|inactive)$")


class CoachAssignAthletes(BaseModel):
    athlete_ids: list[str]


class CoachResponse(BaseModel):
    id: str
    user_id: str
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    specialization: Optional[str] = None
    experience_years: Optional[int] = 0
    sport_ids: list[str] = []
    sports: list[CoachSportInfo] = []
    bio: Optional[str] = None
    status: str = "active"
    athlete_count: int = 0
    joining_date: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    @classmethod
    def from_doc(
        cls,
        doc: dict,
        sports: list[dict] = None,
        athlete_count: int = 0,
    ) -> "CoachResponse":
        sport_infos = [
            CoachSportInfo(id=str(s["_id"]), name=s["name"])
            for s in (sports or [])
        ]
        s_ids = [str(sid) for sid in doc.get("sport_ids", [])]
        return cls(
            id=str(doc["_id"]),
            user_id=str(doc.get("user_id", "")),
            full_name=doc.get("full_name", ""),
            email=doc.get("email", ""),
            phone=doc.get("phone"),
            specialization=doc.get("specialization"),
            experience_years=doc.get("experience_years", 0),
            sport_ids=s_ids,
            sports=sport_infos,
            bio=doc.get("bio"),
            status=doc.get("status", "active"),
            athlete_count=athlete_count,
            joining_date=doc.get("joining_date"),
            created_at=doc.get("created_at", datetime.utcnow()),
            updated_at=doc.get("updated_at"),
        )
