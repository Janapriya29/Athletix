"""
Pure calculation functions for performance analytics (Phase 5).
No database access or external I/O here — 100% deterministic and testable.
"""
from typing import Any, Optional, Union


def calculate_improvement(
    current: Optional[Union[int, float]],
    previous: Optional[Union[int, float]],
) -> Optional[float]:
    """
    Calculate percentage improvement between current score and previous score:
    ((current - previous) / previous) * 100

    Returns None if:
    - current is None
    - previous is None
    - previous <= 0 (safely handles zero / negative without division by zero)
    """
    if current is None or previous is None:
        return None
    try:
        curr_val = float(current)
        prev_val = float(previous)
    except (ValueError, TypeError):
        return None

    if prev_val <= 0:
        return None

    improvement = ((curr_val - prev_val) / prev_val) * 100.0
    return round(improvement, 2)


def calculate_trend(
    current: Optional[Union[int, float]],
    previous: Optional[Union[int, float]],
) -> str:
    """
    Determine performance trend based on chronological assessments:
    - Improving: current > previous
    - Declining: current < previous
    - Stable: current == previous
    - Insufficient Data: less than 2 assessments or missing score
    """
    if current is None or previous is None:
        return "Insufficient Data"
    try:
        curr_val = float(current)
        prev_val = float(previous)
    except (ValueError, TypeError):
        return "Insufficient Data"

    if curr_val > prev_val:
        return "Improving"
    elif curr_val < prev_val:
        return "Declining"
    else:
        return "Stable"


def identify_strongest_metric(metrics: Optional[dict[str, Any]]) -> Optional[dict[str, Any]]:
    """
    Identify metric with the highest score from the assessment metrics dict.
    Returns: {"name": str, "score": float} or None
    """
    if not metrics or not isinstance(metrics, dict):
        return None

    valid_items = []
    for k, v in metrics.items():
        if v is not None:
            try:
                valid_items.append((str(k), float(v)))
            except (ValueError, TypeError):
                continue

    if not valid_items:
        return None

    # Max by score
    best_name, best_score = max(valid_items, key=lambda item: item[1])
    return {"name": best_name, "score": best_score}


def identify_weakest_metric(metrics: Optional[dict[str, Any]]) -> Optional[dict[str, Any]]:
    """
    Identify metric with the lowest score from the assessment metrics dict.
    Returns: {"name": str, "score": float} or None
    """
    if not metrics or not isinstance(metrics, dict):
        return None

    valid_items = []
    for k, v in metrics.items():
        if v is not None:
            try:
                valid_items.append((str(k), float(v)))
            except (ValueError, TypeError):
                continue

    if not valid_items:
        return None

    # Min by score
    worst_name, worst_score = min(valid_items, key=lambda item: item[1])
    return {"name": worst_name, "score": worst_score}


def calculate_attendance_analytics(
    records: list[dict],
    total_applicable_sessions: int,
    warning_threshold: float = 75.0,
) -> dict:
    """
    Calculate attendance statistics adhering strictly to Phase 3 rules:
    - Present = attended
    - Late = attended
    - Absent = missed
    - Attendance Percentage = (Present + Late) / total_applicable_sessions * 100
    - If total_applicable_sessions == 0: percentage is None, warning is False
    - Warning = True if percentage < 75.0
    """
    present = 0
    late = 0
    absent = 0

    for r in records:
        st = str(r.get("status", "")).strip().lower()
        if st == "present":
            present += 1
        elif st == "late":
            late += 1
        elif st == "absent":
            absent += 1

    attended = present + late

    if total_applicable_sessions > 0:
        percentage = round((attended / total_applicable_sessions) * 100.0, 1)
        warning = percentage < warning_threshold
    else:
        percentage = None
        warning = False

    return {
        "total_sessions": total_applicable_sessions,
        "attended_sessions": attended,
        "present_count": present,
        "late_count": late,
        "absent_count": absent,
        "percentage": percentage,
        "warning": warning,
    }
