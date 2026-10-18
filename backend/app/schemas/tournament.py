from datetime import datetime
from typing import Optional
from pydantic import BaseModel, model_validator


class TournamentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    sport_id: str
    location: Optional[str] = None
    venue: Optional[str] = None
    start_date: datetime
    end_date: datetime
    registration_deadline: Optional[datetime] = None
    status: str = "upcoming"

    @model_validator(mode="after")
    def validate_tournament_fields(self):
        if not self.name or not self.name.strip():
            raise ValueError("Tournament name is required")
        self.name = self.name.strip()

        if not self.sport_id or not self.sport_id.strip():
            raise ValueError("Sport ID is required")
        self.sport_id = self.sport_id.strip()

        # Date validations
        if self.end_date < self.start_date:
            raise ValueError("End date cannot be before start date")

        if self.registration_deadline and self.registration_deadline > self.start_date:
            raise ValueError("Registration deadline cannot be after start date")

        # Canonicalize status
        self.status = (self.status or "upcoming").strip().lower()
        if self.status not in ("upcoming", "ongoing", "completed", "cancelled"):
            raise ValueError("Status must be one of: upcoming, ongoing, completed, cancelled")

        # Sync location & venue
        loc = self.location or self.venue or "Main Sports Complex"
        self.location = loc.strip()
        self.venue = loc.strip()
        return self


class TournamentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    sport_id: Optional[str] = None
    location: Optional[str] = None
    venue: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    registration_deadline: Optional[datetime] = None
    status: Optional[str] = None

    @model_validator(mode="after")
    def validate_update(self):
        if self.name is not None:
            if not self.name.strip():
                raise ValueError("Tournament name cannot be empty")
            self.name = self.name.strip()

        if self.start_date and self.end_date:
            if self.end_date < self.start_date:
                raise ValueError("End date cannot be before start date")

        if self.registration_deadline and self.start_date:
            if self.registration_deadline > self.start_date:
                raise ValueError("Registration deadline cannot be after start date")

        if self.status is not None:
            self.status = self.status.strip().lower()
            if self.status not in ("upcoming", "ongoing", "completed", "cancelled"):
                raise ValueError("Status must be one of: upcoming, ongoing, completed, cancelled")

        if self.location or self.venue:
            loc = self.location or self.venue
            self.location = loc.strip()
            self.venue = loc.strip()

        return self


class TournamentResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    sport_id: str
    sport_name: Optional[str] = None
    location: Optional[str] = None
    venue: Optional[str] = None
    start_date: datetime
    end_date: datetime
    registration_deadline: Optional[datetime] = None
    status: str
    participant_count: int = 0
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class ParticipantAdd(BaseModel):
    athlete_id: str
    event: Optional[str] = None


class ParticipantResponse(BaseModel):
    id: str
    tournament_id: str
    athlete_id: str
    athlete_name: str
    sport_name: Optional[str] = None
    event: Optional[str] = None
    status: str = "registered"
    position: Optional[int] = None
    rank: Optional[int] = None
    score: Optional[str] = None
    points: Optional[float] = None
    medal: Optional[str] = None
    remarks: Optional[str] = None
    registered_at: datetime


def calculate_tournament_points(
    position: Optional[int] = None,
    medal: Optional[str] = None,
    explicit_points: Optional[float] = None,
) -> Optional[float]:
    """
    Calculate tournament points according to Phase B rules:
    - 1st place or Gold medal = 10.0 points
    - 2nd place or Silver medal = 7.0 points
    - 3rd place or Bronze medal = 5.0 points
    - 4th–10th place = max(1, 11 - finishing position) points
    - If user explicitly enters points, preserve the entered value.
    - If neither a valid position nor a recognized medal is provided and points are empty, do not invent points.
    """
    if explicit_points is not None:
        try:
            return float(explicit_points)
        except (ValueError, TypeError):
            pass

    normalized_medal = (medal.strip().lower() if isinstance(medal, str) and medal.strip() else "")

    if position == 1 or normalized_medal == "gold":
        return 10.0
    if position == 2 or normalized_medal == "silver":
        return 7.0
    if position == 3 or normalized_medal == "bronze":
        return 5.0
    if position is not None and 4 <= position <= 10:
        return float(max(1, 11 - position))

    return None


class ResultRecordCreate(BaseModel):
    athlete_id: str
    position: Optional[int] = None
    rank: Optional[int] = None
    score: Optional[str] = None
    points: Optional[float] = None
    medal: Optional[str] = None
    performance_notes: Optional[str] = None
    remarks: Optional[str] = None

    @model_validator(mode="after")
    def sync_aliases(self):
        if self.position is None and self.rank is not None:
            self.position = self.rank
        elif self.position is not None and self.rank is None:
            self.rank = self.position

        if self.remarks is None and self.performance_notes is not None:
            self.remarks = self.performance_notes
        elif self.remarks is not None and self.performance_notes is None:
            self.performance_notes = self.remarks

        if self.medal:
            m = self.medal.strip().lower()
            if m in ("gold", "silver", "bronze"):
                self.medal = m.capitalize()
            elif m in ("none", ""):
                self.medal = None

        # Automatically determine medal if not given but position is 1, 2, or 3
        if not self.medal and self.position:
            if self.position == 1:
                self.medal = "Gold"
            elif self.position == 2:
                self.medal = "Silver"
            elif self.position == 3:
                self.medal = "Bronze"

        # Automatically calculate default points if not provided
        if self.points is None:
            self.points = calculate_tournament_points(
                position=self.position,
                medal=self.medal,
                explicit_points=self.points,
            )

        return self


class ResultRecordUpdate(BaseModel):
    position: Optional[int] = None
    rank: Optional[int] = None
    score: Optional[str] = None
    points: Optional[float] = None
    medal: Optional[str] = None
    performance_notes: Optional[str] = None
    remarks: Optional[str] = None

    @model_validator(mode="after")
    def sync_aliases(self):
        if self.position is None and self.rank is not None:
            self.position = self.rank
        elif self.position is not None and self.rank is None:
            self.rank = self.position

        if self.remarks is None and self.performance_notes is not None:
            self.remarks = self.performance_notes
        elif self.remarks is not None and self.performance_notes is None:
            self.performance_notes = self.remarks

        if self.medal:
            m = self.medal.strip().lower()
            if m in ("gold", "silver", "bronze"):
                self.medal = m.capitalize()
            elif m in ("none", ""):
                self.medal = None

        if not self.medal and self.position:
            if self.position == 1:
                self.medal = "Gold"
            elif self.position == 2:
                self.medal = "Silver"
            elif self.position == 3:
                self.medal = "Bronze"

        if self.points is None:
            self.points = calculate_tournament_points(
                position=self.position,
                medal=self.medal,
                explicit_points=self.points,
            )

        return self


class AthleteTournamentHistoryItem(BaseModel):
    tournament_id: str
    tournament_name: str
    sport_name: Optional[str] = None
    location: Optional[str] = None
    start_date: datetime
    end_date: datetime
    tournament_status: str
    participation_status: str = "registered"
    event: Optional[str] = None
    position: Optional[int] = None
    medal: Optional[str] = None
    score: Optional[str] = None
    points: Optional[float] = None
    remarks: Optional[str] = None
