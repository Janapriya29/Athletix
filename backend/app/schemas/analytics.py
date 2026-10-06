from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class MetricScore(BaseModel):
    name: str
    score: float


class PerformanceScoreInfo(BaseModel):
    score: Optional[float] = None
    assessment_date: Optional[datetime] = None


class AttendanceAnalytics(BaseModel):
    total_sessions: int
    attended_sessions: int
    present_count: int
    late_count: int
    absent_count: int
    percentage: Optional[float] = None
    warning: bool = False


class AssessmentHistoryItem(BaseModel):
    id: str
    date: datetime
    overall_score: float
    improvement_percentage: Optional[float] = None
    trend: str
    metrics: dict[str, float] = {}
    remarks: Optional[str] = None
    coach_name: Optional[str] = None


class AthleteAnalyticsResponse(BaseModel):
    athlete_id: str
    athlete_name: str
    sport_id: Optional[str] = None
    sport_name: Optional[str] = None
    coach_id: Optional[str] = None
    coach_name: Optional[str] = None
    current_performance: Optional[PerformanceScoreInfo] = None
    previous_performance: Optional[PerformanceScoreInfo] = None
    improvement_percentage: Optional[float] = None
    trend: str  # "Improving", "Declining", "Stable", "Insufficient Data"
    strongest_metric: Optional[MetricScore] = None
    weakest_metric: Optional[MetricScore] = None
    metrics: list[MetricScore] = []
    attendance: AttendanceAnalytics
    assessment_history: list[AssessmentHistoryItem] = []


class AthleteAnalyticsSummary(BaseModel):
    athlete_id: str
    athlete_name: str
    sport_name: Optional[str] = None
    current_score: Optional[float] = None
    previous_score: Optional[float] = None
    improvement_percentage: Optional[float] = None
    trend: str
    attendance_percentage: Optional[float] = None
    attendance_warning: bool = False
    strongest_metric: Optional[MetricScore] = None
    weakest_metric: Optional[MetricScore] = None


class CoachAnalyticsSummary(BaseModel):
    total_assigned_athletes: int
    average_performance: Optional[float] = None
    average_attendance: Optional[float] = None
    improving_athletes_count: int
    declining_athletes_count: int
    stable_athletes_count: int
    athletes_below_attendance_threshold: int


class AdminAnalyticsSummary(BaseModel):
    total_athletes: int
    total_coaches: int
    total_active_sports: int
    total_assessments: int
    average_performance: Optional[float] = None
    average_attendance: Optional[float] = None
    improving_athletes_count: int
    declining_athletes_count: int
    stable_athletes_count: int
    athletes_below_attendance_threshold: int


class SportAnalyticsItem(BaseModel):
    sport_id: str
    sport_name: str
    athlete_count: int
    assessment_count: int
    average_performance: Optional[float] = None
    average_attendance: Optional[float] = None


class AdminSportsAnalyticsResponse(BaseModel):
    sports: list[SportAnalyticsItem]
