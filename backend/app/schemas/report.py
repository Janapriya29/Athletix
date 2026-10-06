from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel


class AthletePerformanceReport(BaseModel):
    athlete_id: str
    athlete_name: str
    sport_id: Optional[str] = None
    sport_name: Optional[str] = None
    current_score: Optional[float] = None
    previous_score: Optional[float] = None
    improvement_pct: Optional[float] = None
    trend: str
    strongest_metric: Optional[str] = None
    weakest_metric: Optional[str] = None
    total_assessments: int = 0
    assessment_history: list[dict[str, Any]] = []
    generated_at: datetime


class AthleteAttendanceReport(BaseModel):
    athlete_id: str
    athlete_name: str
    sport_id: Optional[str] = None
    sport_name: Optional[str] = None
    total_sessions: int = 0
    attended_sessions: int = 0
    present_count: int = 0
    late_count: int = 0
    absent_count: int = 0
    attendance_percentage: Optional[float] = None
    warning: bool = False
    records: list[dict[str, Any]] = []
    generated_at: datetime


class AthleteTournamentReportItem(BaseModel):
    tournament_id: str
    tournament_name: str
    sport_name: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    event: Optional[str] = None
    status: str = "registered"
    position: Optional[int] = None
    score: Optional[str] = None
    points: Optional[float] = None
    medal: Optional[str] = None
    remarks: Optional[str] = None


class AthleteTournamentsReport(BaseModel):
    athlete_id: str
    athlete_name: str
    sport_name: Optional[str] = None
    total_tournaments: int = 0
    total_points: float = 0.0
    medals_summary: dict[str, int] = {"gold": 0, "silver": 0, "bronze": 0, "total": 0}
    history: list[AthleteTournamentReportItem] = []
    generated_at: datetime


class AthleteDevelopmentSummaryReport(BaseModel):
    athlete_id: str
    athlete_name: str
    email: str
    sport_name: Optional[str] = None
    coach_name: Optional[str] = None
    status: str = "active"
    attendance_summary: dict[str, Any]
    performance_summary: dict[str, Any]
    tournaments_summary: dict[str, Any]
    generated_at: datetime


class AcademySummaryReport(BaseModel):
    total_athletes: int
    total_coaches: int
    total_sports: int
    total_training_sessions: int
    total_attendance_records: int
    average_attendance_percentage: Optional[float] = None
    total_assessments: int
    average_performance_score: Optional[float] = None
    total_tournaments: int
    total_tournament_participants: int
    total_medals_awarded: int
    generated_at: datetime


class AcademyAttendanceReportItem(BaseModel):
    athlete_id: str
    athlete_name: str
    sport_name: Optional[str] = None
    coach_name: Optional[str] = None
    total_sessions: int
    attended_sessions: int
    attendance_percentage: Optional[float] = None
    warning: bool = False


class AcademyTournamentReportItem(BaseModel):
    tournament_id: str
    tournament_name: str
    sport_name: Optional[str] = None
    status: str
    start_date: Optional[datetime] = None
    total_participants: int
    gold_medalist: Optional[str] = None
    silver_medalist: Optional[str] = None
    bronze_medalist: Optional[str] = None
