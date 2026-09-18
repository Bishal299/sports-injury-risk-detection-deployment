import os
from uuid import UUID

from app.models.analysis_result import AnalysisResult


def normalize_risk_category(score):
    if score is None:
        return "Not Available"
    if score < 25:
        return "LOW"
    if score < 50:
        return "MODERATE"
    if score < 75:
        return "HIGH"
    return "CRITICAL"


def normalize_risk_category_label(category, score):
    if category:
        value = str(category).upper()
        if "CRITICAL" in value:
            return "CRITICAL"
        if "HIGH" in value:
            return "HIGH"
        if "MODERATE" in value:
            return "MODERATE"
        if "LOW" in value:
            return "LOW"
    return normalize_risk_category(score)


def get_analysis_score(analysis: AnalysisResult | None):
    if not analysis:
        return None
    return (
        analysis.composite_risk_score
        if analysis.composite_risk_score is not None
        else analysis.overall_risk_score
    )


def get_existing_analysis_report_path(video_id: UUID, file_type: str):
    if file_type == "pdf":
        candidates = [
            os.path.join("uploads/analysis/reports", f"{video_id}_report.pdf"),
            os.path.join("uploads/analysis/reports", f"{video_id}_features.pdf"),
        ]
    else:
        candidates = [
            os.path.join("uploads/analysis/reports", f"video_{video_id}_timeseries.csv"),
            os.path.join("uploads/analysis/reports", f"{video_id}_report.csv"),
            os.path.join("uploads/analysis/reports", f"{video_id}_features.csv"),
        ]

    for path in candidates:
        if os.path.exists(path):
            return path

    return None


def movement_metrics(analysis: AnalysisResult | None):
    if not analysis:
        return None

    values = {
        "knee_valgus": analysis.knee_valgus,
        "hip_stability": analysis.hip_stability,
        "trunk_lean": analysis.trunk_lean,
        "landing_mechanics": analysis.movement_quality,
        "stride": analysis.stride_length,
        "joint_alignment": analysis.joint_alignment,
        "symmetry": analysis.symmetry_score,
        "movement_quality": analysis.movement_quality,
    }
    return {key: value for key, value in values.items() if value is not None}


def build_movement_comparison_payload(analyses: list[AnalysisResult]):
    latest = analyses[0] if analyses else None
    if not latest:
        return {
            "initial_assessment": None,
            "latest_assessment": None,
            "comparison": {},
            "comparison_status": "No Analysis",
        }

    compatible_previous = [
        analysis
        for analysis in reversed(analyses[1:])
        if analysis.algorithm_version == latest.algorithm_version
    ]
    initial = compatible_previous[0] if compatible_previous else latest

    if initial.analysis_id == latest.analysis_id:
        status = "No Previous Assessment" if len(analyses) == 1 else "Incompatible Analysis Versions"
        return {
            "initial_assessment": initial,
            "latest_assessment": latest,
            "comparison": {},
            "comparison_status": status,
        }

    initial_metrics = movement_metrics(initial)
    latest_metrics = movement_metrics(latest)
    comparison = {}

    if initial_metrics and latest_metrics:
        for key, latest_value in latest_metrics.items():
            initial_value = initial_metrics.get(key)
            if initial_value is not None:
                comparison[key] = {
                    "initial": initial_value,
                    "latest": latest_value,
                    "change": latest_value - initial_value,
                }

    return {
        "initial_assessment": initial,
        "latest_assessment": latest,
        "comparison": comparison,
        "comparison_status": "Compared" if comparison else "Not Available",
    }
