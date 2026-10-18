from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class AthleteCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=128)
    email: EmailStr
    password: Optional[str] = Field(default=None, min_length=8, max_length=128)
    phone: Optional[str] = Field(default=None, max_length=32)
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = Field(default=None, pattern="^(male|female|other)$")
    sport_id: str
    additional_sport_ids: Optional[list[str]] = []
    coach_id: Optional[str] = None
    address: Optional[str] = Field(default=None, max_length=256)
    emergency_contact: Optional[str] = Field(default=None, max_length=256)
    joining_date: Optional[datetime] = None
    status: str = Field(default="active", pattern="^(active|inactive)$")


class AthleteUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=128)
    phone: Optional[str] = Field(default=None, max_length=32)
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = Field(default=None, pattern="^(male|female|other)$")
    sport_id: Optional[str] = None
    additional_sport_ids: Optional[list[str]] = None
    coach_id: Optional[str] = None
    address: Optional[str] = Field(default=None, max_length=256)
    emergency_contact: Optional[str] = Field(default=None, max_length=256)
    status: Optional[str] = Field(default=None, pattern="^(active|inactive)$")


class AthleteSelfUpdate(BaseModel):
    phone: Optional[str] = Field(default=None, max_length=32)
    address: Optional[str] = Field(default=None, max_length=256)
    emergency_contact: Optional[str] = Field(default=None, max_length=256)


class AthleteStatusUpdate(BaseModel):
    status: str = Field(pattern="^(active|inactive)$")


class AthleteAssignCoach(BaseModel):
    coach_id: Optional[str] = None


class AthleteAssignSport(BaseModel):
    sport_id: str
    additional_sport_ids: Optional[list[str]] = []


class AssignedCoachInfo(BaseModel):
    coach_id: str
    full_name: str
    email: str
    phone: Optional[str] = None
    specialization: Optional[str] = None
    bio: Optional[str] = None


class AthleteResponse(BaseModel):
    id: str
    user_id: str
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None
    sport_id: Optional[str] = ""
    sport_name: Optional[str] = None
    additional_sport_ids: list[str] = []
    coach_id: Optional[str] = None
    coach_name: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    joining_date: Optional[datetime] = None
    status: str = "active"
    created_at: datetime
    updated_at: Optional[datetime] = None

    @classmethod
    def from_doc(
        cls,
        doc: dict,
        sport_name: Optional[str] = None,
        coach_name: Optional[str] = None,
    ) -> "AthleteResponse":
        additional_ids = [
            str(sid) for sid in doc.get("additional_sport_ids", [])
            if sid and str(sid) != "None"
        ]
        sport_val = doc.get("sport_id")
        sport_str = str(sport_val) if sport_val and str(sport_val) != "None" else ""
        return cls(
            id=str(doc["_id"]),
            user_id=str(doc.get("user_id", "")),
            full_name=doc.get("full_name", ""),
            email=doc.get("email", ""),
            phone=doc.get("phone"),
            date_of_birth=doc.get("date_of_birth"),
            gender=doc.get("gender"),
            sport_id=sport_str,
            sport_name=sport_name,
            additional_sport_ids=additional_ids,
            coach_id=str(doc["coach_id"]) if doc.get("coach_id") else None,
            coach_name=coach_name,
            address=doc.get("address"),
            emergency_contact=doc.get("emergency_contact"),
            joining_date=doc.get("joining_date"),
            status=doc.get("status", "active"),
            created_at=doc.get("created_at", datetime.utcnow()),
            updated_at=doc.get("updated_at"),
        )
