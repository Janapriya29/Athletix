from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel


class TournamentRankingItem(BaseModel):
    rank: int
    athlete_id: str
    athlete_name: str
    sport_id: Optional[str] = None
    sport_name: Optional[str] = None
    points: float = 0.0
    gold_count: int = 0
    silver_count: int = 0
    bronze_count: int = 0
    total_medals: int = 0
    tournaments_played: int = 0


class PerformanceRankingItem(BaseModel):
    rank: int
    athlete_id: str
    athlete_name: str
    sport_id: Optional[str] = None
    sport_name: Optional[str] = None
    performance_score: float
    assessment_date: Optional[datetime] = None


class AttendanceRankingItem(BaseModel):
    rank: int
    athlete_id: str
    athlete_name: str
    sport_id: Optional[str] = None
    sport_name: Optional[str] = None
    attendance_percentage: float
    total_sessions: int
    attended_sessions: int


class ImprovementRankingItem(BaseModel):
    rank: int
    athlete_id: str
    athlete_name: str
    sport_id: Optional[str] = None
    sport_name: Optional[str] = None
    improvement_percentage: float
    current_score: float
    previous_score: float


class RankingsResponse(BaseModel):
    type: str  # "tournament" | "performance" | "attendance" | "improvement"
    sport_id: Optional[str] = None
    sport_name: Optional[str] = None
    items: list[Any] = []
