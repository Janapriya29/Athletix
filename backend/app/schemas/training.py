from datetime import date, datetime
from typing import Any, Optional
from pydantic import BaseModel, Field, model_validator


def _parse_time_minutes(t_str: str) -> int:
    parts = t_str.strip().split(":")
    return int(parts[0]) * 60 + int(parts[1])


class TrainingSessionCreate(BaseModel):
    title: str = Field(min_length=1, max_length=150)
    description: Optional[str] = Field(default=None, max_length=1000)
    sport_id: str
    coach_id: str
    session_date: datetime
    start_time: str = Field(pattern=r"^\d{1,2}:\d{2}$")
    end_time: str = Field(pattern=r"^\d{1,2}:\d{2}$")
    location: Optional[str] = Field(default="Academy Main Ground", max_length=200)
    athlete_ids: Optional[list[str]] = []
    status: str = Field(default="scheduled")

    @model_validator(mode="after")
    def validate_times(self) -> "TrainingSessionCreate":
        start_min = _parse_time_minutes(self.start_time)
        end_min = _parse_time_minutes(self.end_time)
        if start_min >= end_min:
            raise ValueError("Start time must be before end time")
        self.status = self.status.lower()
        if self.status not in ("scheduled", "completed", "cancelled"):
            raise ValueError("Status must be scheduled, completed, or cancelled")
        return self


class TrainingSessionUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=150)
    description: Optional[str] = Field(default=None, max_length=1000)
    sport_id: Optional[str] = None
    coach_id: Optional[str] = None
    session_date: Optional[datetime] = None
    start_time: Optional[str] = Field(default=None, pattern=r"^\d{1,2}:\d{2}$")
    end_time: Optional[str] = Field(default=None, pattern=r"^\d{1,2}:\d{2}$")
    location: Optional[str] = Field(default=None, max_length=200)
    status: Optional[str] = None

    @model_validator(mode="after")
    def validate_times(self) -> "TrainingSessionUpdate":
        if self.start_time and self.end_time:
            if _parse_time_minutes(self.start_time) >= _parse_time_minutes(self.end_time):
                raise ValueError("Start time must be before end time")
        if self.status is not None:
            self.status = self.status.lower()
            if self.status not in ("scheduled", "completed", "cancelled"):
                raise ValueError("Status must be scheduled, completed, or cancelled")
        return self


class TrainingStatusUpdate(BaseModel):
    status: str

    @model_validator(mode="after")
    def validate_status(self) -> "TrainingStatusUpdate":
        self.status = self.status.lower()
        if self.status not in ("scheduled", "completed", "cancelled"):
            raise ValueError("Status must be scheduled, completed, or cancelled")
        return self


class ParticipantAdd(BaseModel):
    athlete_id: str


class ParticipantBulk(BaseModel):
    athlete_ids: list[str]


class AttendanceRecordCreate(BaseModel):
    athlete_id: str
    status: str
    remarks: Optional[str] = Field(default=None, max_length=300)

    @model_validator(mode="after")
    def validate_status(self) -> "AttendanceRecordCreate":
        self.status = self.status.lower()
        if self.status not in ("present", "absent", "late"):
            raise ValueError("Status must be present, absent, or late")
        return self


class AttendanceBulkCreate(BaseModel):
    records: list[AttendanceRecordCreate]


class AttendanceRecordUpdate(BaseModel):
    status: str
    remarks: Optional[str] = Field(default=None, max_length=300)

    @model_validator(mode="after")
    def validate_status(self) -> "AttendanceRecordUpdate":
        self.status = self.status.lower()
        if self.status not in ("present", "absent", "late"):
            raise ValueError("Status must be present, absent, or late")
        return self


class ParticipantInfo(BaseModel):
    athlete_id: str
    full_name: str
    email: str
    sport_name: Optional[str] = None
    attendance_status: Optional[str] = None
    remarks: Optional[str] = None


class AttendanceResponse(BaseModel):
    id: str
    session_id: str
    athlete_id: str
    athlete_name: Optional[str] = None
    status: str
    marked_by: Optional[str] = None
    marked_at: Optional[datetime] = None
    remarks: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class TrainingSessionResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    sport_id: str
    sport_name: Optional[str] = None
    coach_id: str
    coach_name: Optional[str] = None
    session_date: datetime
    start_time: str
    end_time: str
    location: Optional[str] = None
    status: str
    athlete_ids: list[str] = []
    participant_count: int = 0
    participants: list[ParticipantInfo] = []
    created_at: datetime
    updated_at: Optional[datetime] = None

    @classmethod
    def from_doc(
        cls,
        doc: dict,
        sport_name: Optional[str] = None,
        coach_name: Optional[str] = None,
        participants: list[ParticipantInfo] = None,
    ) -> "TrainingSessionResponse":
        ath_ids = [str(aid) for aid in doc.get("athlete_ids", [])]
        raw_date = doc.get("session_date") or doc.get("date") or datetime.utcnow()
        if isinstance(raw_date, date) and not isinstance(raw_date, datetime):
            raw_date = datetime.combine(raw_date, datetime.min.time())

        return cls(
            id=str(doc["_id"]),
            title=doc.get("title", ""),
            description=doc.get("description") or doc.get("objectives"),
            sport_id=str(doc.get("sport_id", "")),
            sport_name=sport_name,
            coach_id=str(doc.get("coach_id", "")),
            coach_name=coach_name,
            session_date=raw_date,
            start_time=doc.get("start_time", "09:00"),
            end_time=doc.get("end_time", "10:00"),
            location=doc.get("location") or doc.get("venue") or "Academy Ground",
            status=doc.get("status", "scheduled").lower(),
            athlete_ids=ath_ids,
            participant_count=len(ath_ids),
            participants=participants or [],
            created_at=doc.get("created_at", datetime.utcnow()),
            updated_at=doc.get("updated_at"),
        )


class AthleteAttendanceSummary(BaseModel):
    total_sessions: int
    attended_sessions: int
    present_count: int
    late_count: int
    absent_count: int
    attendance_percentage: float
    warning: bool  # True if < 75%
    history: list[dict] = []


class CoachTrainingSummary(BaseModel):
    today_count: int
    upcoming_count: int
    completed_count: int
    average_attendance_percentage: float


class AdminTrainingSummary(BaseModel):
    total_sessions: int
    scheduled_count: int
    completed_count: int
    cancelled_count: int
    average_attendance_percentage: float
