from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, model_validator


class AssessmentCreate(BaseModel):
    athlete_id: str
    sport_id: Optional[str] = None
    coach_id: Optional[str] = None
    date: Optional[datetime] = None
    metrics: dict[str, float]
    overall_score: Optional[float] = None
    remarks: Optional[str] = None

    @model_validator(mode="after")
    def validate_assessment(self):
        if not self.athlete_id or not self.athlete_id.strip():
            raise ValueError("athlete_id is required")
        self.athlete_id = self.athlete_id.strip()

        if self.sport_id:
            self.sport_id = self.sport_id.strip()

        if self.coach_id:
            self.coach_id = self.coach_id.strip()

        if not self.metrics:
            raise ValueError("At least one metric is required")

        validated_metrics = {}
        for name, val in self.metrics.items():
            name_clean = str(name).strip()
            if not name_clean:
                continue
            try:
                score = float(val)
            except (ValueError, TypeError):
                raise ValueError(f"Metric '{name}' must have a numeric score")
            if score < 0.0 or score > 100.0:
                raise ValueError(f"Metric '{name}' score must be between 0 and 100")
            validated_metrics[name_clean] = round(score, 2)

        if not validated_metrics:
            raise ValueError("At least one valid metric is required")
        self.metrics = validated_metrics

        if self.overall_score is not None:
            try:
                ov = float(self.overall_score)
            except (ValueError, TypeError):
                raise ValueError("overall_score must be a number")
            if ov < 0.0 or ov > 100.0:
                raise ValueError("overall_score must be between 0 and 100")
            self.overall_score = round(ov, 2)

        if self.remarks:
            self.remarks = self.remarks.strip()

        return self


class AssessmentResponse(BaseModel):
    id: str
    athlete_id: str
    athlete_name: Optional[str] = None
    coach_id: Optional[str] = None
    coach_name: Optional[str] = None
    sport_id: Optional[str] = None
    sport_name: Optional[str] = None
    date: datetime
    metrics: dict[str, float]
    overall_score: float
    remarks: Optional[str] = None
    created_at: datetime

    @classmethod
    def from_doc(
        cls,
        doc: dict,
        athlete_name: Optional[str] = None,
        coach_name: Optional[str] = None,
        sport_name: Optional[str] = None,
    ) -> "AssessmentResponse":
        raw_metrics = doc.get("metrics") or {}
        norm_metrics = {str(k): round(float(v), 2) for k, v in raw_metrics.items() if v is not None}
        return cls(
            id=str(doc["_id"]),
            athlete_id=str(doc["athlete_id"]),
            athlete_name=athlete_name,
            coach_id=str(doc["coach_id"]) if doc.get("coach_id") else None,
            coach_name=coach_name,
            sport_id=str(doc["sport_id"]) if doc.get("sport_id") else None,
            sport_name=sport_name,
            date=doc.get("date") or doc.get("created_at") or datetime.now(timezone.utc),
            metrics=norm_metrics,
            overall_score=round(float(doc.get("overall_score", 0.0)), 2),
            remarks=doc.get("remarks"),
            created_at=doc.get("created_at") or datetime.now(timezone.utc),
        )
