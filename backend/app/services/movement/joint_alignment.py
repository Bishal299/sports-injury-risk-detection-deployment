from typing import Dict, Any, Optional
import math


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

DEFAULT_MIN_COVERAGE = 50.0

# Weights for the overall alignment score.
# Knee and hip receive higher importance because they are
# particularly relevant to lower-limb movement assessment.
JOINT_WEIGHTS = {
    "knee": 0.30,
    "hip": 0.25,
    "ankle": 0.15,
    "shoulder": 0.15,
    "elbow": 0.15,
}


# ---------------------------------------------------------
# Utility functions
# ---------------------------------------------------------

def _safe_float(value: Any) -> Optional[float]:
    """Convert a value to a finite float, otherwise return None."""

    try:
        if value is None:
            return None

        value = float(value)

        if not math.isfinite(value):
            return None

        return value

    except (TypeError, ValueError):
        return None


def _get_joint_summary(
    joint_data: Dict[str, Any],
    joint_name: str,
) -> Dict[str, Any]:
    """
    Extract a joint summary from the structure produced by
    calculate_joint_angles().
    """

    summary = joint_data.get("summary", {})

    joint_summary = summary.get(joint_name, {})

    if not isinstance(joint_summary, dict):
        return {}

    return joint_summary


def _get_angle(
    joint_data: Dict[str, Any],
    joint_name: str,
    field: str = "avg_angle",
) -> Optional[float]:
    """Get a joint-angle value from the joint_angles output."""

    summary = _get_joint_summary(
        joint_data,
        joint_name,
    )

    return _safe_float(summary.get(field))


def _get_coverage(
    joint_data: Dict[str, Any],
    joint_name: str,
) -> float:
    """Get measurement coverage for a joint."""

    summary = _get_joint_summary(
        joint_data,
        joint_name,
    )

    coverage = _safe_float(
        summary.get("coverage_percent")
    )

    if coverage is None:
        return 0.0

    return max(0.0, min(100.0, coverage))


def _get_valgus(
    valgus_data: Dict[str, Any],
    side: str,
) -> Optional[float]:
    """Extract maximum knee valgus deviation."""

    side_data = valgus_data.get(side, {})

    if not isinstance(side_data, dict):
        return None

    return _safe_float(
        side_data.get("max_deviation")
    )


def _calculate_asymmetry(
    right: Optional[float],
    left: Optional[float],
) -> Optional[float]:
    """
    Calculate percentage difference between right and left.

    Uses the average absolute magnitude as the denominator.
    """

    if right is None or left is None:
        return None

    denominator = (
        abs(right) + abs(left)
    ) / 2.0

    if denominator < 1e-7:
        return 0.0

    return abs(right - left) / denominator * 100.0


def _classify_valgus(
    max_valgus: Optional[float],
) -> str:
    """Classify maximum observed knee valgus."""

    if max_valgus is None:
        return "Insufficient Data"

    max_valgus = abs(max_valgus)

    if max_valgus < 5.0:
        return "Optimal"

    if max_valgus < 10.0:
        return "Mild Deviation"

    if max_valgus < 15.0:
        return "Moderate Deviation"

    return "Significant Deviation"


def _classify_angle_asymmetry(
    right: Optional[float],
    left: Optional[float],
    right_coverage: float,
    left_coverage: float,
) -> str:
    """
    Classify joint alignment based on side-to-side angle
    difference and data quality.
    """

    if (
        right is None
        or left is None
        or right_coverage < DEFAULT_MIN_COVERAGE
        or left_coverage < DEFAULT_MIN_COVERAGE
    ):
        return "Insufficient Data"

    difference = abs(right - left)

    # Joint-angle asymmetry thresholds.
    if difference < 5.0:
        return "Optimal"

    if difference < 10.0:
        return "Mild Asymmetry"

    if difference < 20.0:
        return "Moderate Asymmetry"

    return "Significant Asymmetry"


def _angle_score(
    right: Optional[float],
    left: Optional[float],
    optimal_difference: float = 5.0,
) -> Optional[float]:
    """
    Convert right-vs-left angle difference into a 0-100 score.

    This is an alignment consistency score, not a clinical score.
    """

    if right is None or left is None:
        return None

    difference = abs(right - left)

    if difference <= optimal_difference:
        return 100.0

    # Every degree beyond the optimal region reduces the score.
    score = 100.0 - (
        (difference - optimal_difference) * 4.0
    )

    return max(0.0, min(100.0, score))


def _valgus_score(
    right: Optional[float],
    left: Optional[float],
) -> Optional[float]:
    """
    Convert maximum knee valgus into a 0-100 score.

    This represents deviation severity, not injury probability.
    """

    values = [
        abs(v)
        for v in [right, left]
        if v is not None
    ]

    if not values:
        return None

    max_valgus = max(values)

    score = 100.0 - (
        max_valgus * 4.0
    )

    return max(0.0, min(100.0, score))


# ---------------------------------------------------------
# Main function
# ---------------------------------------------------------

def analyze_joint_alignment(
    joint_data: Dict[str, Any],
    valgus_data: Dict[str, Any],
    hip_data: Dict[str, Any],
    posture_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Analyze bilateral joint alignment using the actual outputs
    produced by joint_angles.py.

    Inputs:
        joint_data:
            Output from calculate_joint_angles().

        valgus_data:
            Output from knee valgus analysis.

        hip_data:
            Output from hip stability analysis.

        posture_data:
            Output from posture analysis.

    Returns:
        {
            "score": float,
            "status": str,
            "table": [...],
            "asymmetry": {...},
            "component_scores": {...},
            "data_quality": {...},
            "warnings": [...]
        }

    Important:
        The score is a biomechanical alignment consistency indicator.
        It is NOT a medical diagnosis or probability of injury.
    """

    warnings = []

    # =====================================================
    # KNEE ANGLES
    # =====================================================

    right_knee_angle = _get_angle(
        joint_data,
        "right_knee",
        "avg_angle",
    )

    left_knee_angle = _get_angle(
        joint_data,
        "left_knee",
        "avg_angle",
    )

    right_knee_coverage = _get_coverage(
        joint_data,
        "right_knee",
    )

    left_knee_coverage = _get_coverage(
        joint_data,
        "left_knee",
    )

    # =====================================================
    # KNEE VALGUS
    # =====================================================

    right_valgus = _get_valgus(
        valgus_data,
        "right",
    )

    left_valgus = _get_valgus(
        valgus_data,
        "left",
    )

    valgus_values = [
        abs(v)
        for v in [right_valgus, left_valgus]
        if v is not None
    ]

    max_valgus = (
        max(valgus_values)
        if valgus_values
        else None
    )

    knee_status = _classify_valgus(
        max_valgus
    )

    knee_angle_asymmetry = _calculate_asymmetry(
        right_knee_angle,
        left_knee_angle,
    )

    # Knee score combines:
    # 70% valgus deviation
    # 30% bilateral joint-angle consistency

    valgus_score = _valgus_score(
        right_valgus,
        left_valgus,
    )

    knee_angle_score = _angle_score(
        right_knee_angle,
        left_knee_angle,
    )

    if (
        valgus_score is not None
        and knee_angle_score is not None
    ):
        knee_score = (
            valgus_score * 0.70
            + knee_angle_score * 0.30
        )

    elif valgus_score is not None:
        knee_score = valgus_score

    else:
        knee_score = knee_angle_score

    # =====================================================
    # HIP
    # =====================================================

    right_hip_angle = _get_angle(
        joint_data,
        "right_hip",
        "avg_angle",
    )

    left_hip_angle = _get_angle(
        joint_data,
        "left_hip",
        "avg_angle",
    )

    right_hip_coverage = _get_coverage(
        joint_data,
        "right_hip",
    )

    left_hip_coverage = _get_coverage(
        joint_data,
        "left_hip",
    )

    # Hip stability comes from your hip stability module.
    right_hip_stability = _safe_float(
        hip_data.get("right_hip_stability")
    )

    left_hip_stability = _safe_float(
        hip_data.get("left_hip_stability")
    )

    hip_angle_asymmetry = _calculate_asymmetry(
        right_hip_angle,
        left_hip_angle,
    )

    hip_stability_asymmetry = _calculate_asymmetry(
        right_hip_stability,
        left_hip_stability,
    )

    hip_status = _classify_angle_asymmetry(
        right_hip_angle,
        left_hip_angle,
        right_hip_coverage,
        left_hip_coverage,
    )

    # If actual hip stability data exists, use it to
    # improve the classification.
    if (
        right_hip_stability is not None
        and left_hip_stability is not None
    ):

        average_hip_stability = (
            right_hip_stability
            + left_hip_stability
        ) / 2.0

        stability_difference = abs(
            right_hip_stability
            - left_hip_stability
        )

        if (
            average_hip_stability >= 75
            and stability_difference < 5
            and hip_status == "Optimal"
        ):
            hip_status = "Optimal"

        elif stability_difference < 10:
            hip_status = "Mild Asymmetry"

        elif stability_difference < 20:
            hip_status = "Moderate Asymmetry"

        else:
            hip_status = "Significant Asymmetry"

    # Hip score.
    hip_angle_score = _angle_score(
        right_hip_angle,
        left_hip_angle,
    )

    if (
        right_hip_stability is not None
        and left_hip_stability is not None
    ):
        hip_stability_score = (
            right_hip_stability
            + left_hip_stability
        ) / 2.0
    else:
        hip_stability_score = None

    if (
        hip_angle_score is not None
        and hip_stability_score is not None
    ):
        hip_score = (
            hip_angle_score * 0.40
            + hip_stability_score * 0.60
        )

    elif hip_stability_score is not None:
        hip_score = hip_stability_score

    else:
        hip_score = hip_angle_score

    # =====================================================
    # ANKLE
    # =====================================================

    right_ankle_angle = _get_angle(
        joint_data,
        "right_ankle",
        "avg_angle",
    )

    left_ankle_angle = _get_angle(
        joint_data,
        "left_ankle",
        "avg_angle",
    )

    right_ankle_coverage = _get_coverage(
        joint_data,
        "right_ankle",
    )

    left_ankle_coverage = _get_coverage(
        joint_data,
        "left_ankle",
    )

    ankle_asymmetry = _calculate_asymmetry(
        right_ankle_angle,
        left_ankle_angle,
    )

    ankle_status = _classify_angle_asymmetry(
        right_ankle_angle,
        left_ankle_angle,
        right_ankle_coverage,
        left_ankle_coverage,
    )

    ankle_score = _angle_score(
        right_ankle_angle,
        left_ankle_angle,
    )

    # =====================================================
    # SHOULDER
    # =====================================================

    right_shoulder_angle = _get_angle(
        joint_data,
        "right_shoulder",
        "avg_angle",
    )

    left_shoulder_angle = _get_angle(
        joint_data,
        "left_shoulder",
        "avg_angle",
    )

    right_shoulder_coverage = _get_coverage(
        joint_data,
        "right_shoulder",
    )

    left_shoulder_coverage = _get_coverage(
        joint_data,
        "left_shoulder",
    )

    shoulder_asymmetry = _calculate_asymmetry(
        right_shoulder_angle,
        left_shoulder_angle,
    )

    # Shoulder tilt comes from posture.py.
    shoulder_tilt = _safe_float(
        posture_data.get("shoulder_tilt_deg")
    )

    if shoulder_tilt is not None:

        if shoulder_tilt < 3:
            shoulder_status = "Optimal"

        elif shoulder_tilt < 6:
            shoulder_status = "Mild Deviation"

        elif shoulder_tilt < 10:
            shoulder_status = "Moderate Deviation"

        else:
            shoulder_status = "Significant Deviation"

    else:
        shoulder_status = _classify_angle_asymmetry(
            right_shoulder_angle,
            left_shoulder_angle,
            right_shoulder_coverage,
            left_shoulder_coverage,
        )

    shoulder_angle_score = _angle_score(
        right_shoulder_angle,
        left_shoulder_angle,
    )

    if shoulder_tilt is not None:

        shoulder_tilt_score = max(
            0.0,
            min(
                100.0,
                100.0 - shoulder_tilt * 5.0,
            )
        )

    else:
        shoulder_tilt_score = None

    if (
        shoulder_angle_score is not None
        and shoulder_tilt_score is not None
    ):
        shoulder_score = (
            shoulder_angle_score * 0.40
            + shoulder_tilt_score * 0.60
        )

    elif shoulder_tilt_score is not None:
        shoulder_score = shoulder_tilt_score

    else:
        shoulder_score = shoulder_angle_score

    # =====================================================
    # ELBOW
    # =====================================================

    right_elbow_angle = _get_angle(
        joint_data,
        "right_elbow",
        "avg_angle",
    )

    left_elbow_angle = _get_angle(
        joint_data,
        "left_elbow",
        "avg_angle",
    )

    right_elbow_coverage = _get_coverage(
        joint_data,
        "right_elbow",
    )

    left_elbow_coverage = _get_coverage(
        joint_data,
        "left_elbow",
    )

    elbow_asymmetry = _calculate_asymmetry(
        right_elbow_angle,
        left_elbow_angle,
    )

    elbow_status = _classify_angle_asymmetry(
        right_elbow_angle,
        left_elbow_angle,
        right_elbow_coverage,
        left_elbow_coverage,
    )

    elbow_score = _angle_score(
        right_elbow_angle,
        left_elbow_angle,
    )

    # =====================================================
    # TABLE
    # =====================================================

    table = [
        {
            "joint": "Hip",
            "right": (
                f"{right_hip_angle:.1f}°"
                if right_hip_angle is not None
                else "N/A"
            ),
            "left": (
                f"{left_hip_angle:.1f}°"
                if left_hip_angle is not None
                else "N/A"
            ),
            "status": hip_status,
            "metric": "Joint Angle",
            "asymmetry_percent": (
                round(hip_angle_asymmetry, 1)
                if hip_angle_asymmetry is not None
                else None
            ),
        },
        {
            "joint": "Knee",
            "right": (
                f"{right_knee_angle:.1f}°"
                if right_knee_angle is not None
                else "N/A"
            ),
            "left": (
                f"{left_knee_angle:.1f}°"
                if left_knee_angle is not None
                else "N/A"
            ),
            "status": knee_status,
            "metric": "Knee Angle + Valgus",
            "right_valgus": (
                round(right_valgus, 1)
                if right_valgus is not None
                else None
            ),
            "left_valgus": (
                round(left_valgus, 1)
                if left_valgus is not None
                else None
            ),
            "asymmetry_percent": (
                round(knee_angle_asymmetry, 1)
                if knee_angle_asymmetry is not None
                else None
            ),
        },
        {
            "joint": "Ankle",
            "right": (
                f"{right_ankle_angle:.1f}°"
                if right_ankle_angle is not None
                else "N/A"
            ),
            "left": (
                f"{left_ankle_angle:.1f}°"
                if left_ankle_angle is not None
                else "N/A"
            ),
            "status": ankle_status,
            "metric": "Ankle Joint Angle",
            "asymmetry_percent": (
                round(ankle_asymmetry, 1)
                if ankle_asymmetry is not None
                else None
            ),
        },
        {
            "joint": "Shoulder",
            "right": (
                f"{right_shoulder_angle:.1f}°"
                if right_shoulder_angle is not None
                else "N/A"
            ),
            "left": (
                f"{left_shoulder_angle:.1f}°"
                if left_shoulder_angle is not None
                else "N/A"
            ),
            "status": shoulder_status,
            "metric": "Shoulder Angle + Tilt",
            "shoulder_tilt_deg": (
                round(shoulder_tilt, 1)
                if shoulder_tilt is not None
                else None
            ),
            "asymmetry_percent": (
                round(shoulder_asymmetry, 1)
                if shoulder_asymmetry is not None
                else None
            ),
        },
        {
            "joint": "Elbow",
            "right": (
                f"{right_elbow_angle:.1f}°"
                if right_elbow_angle is not None
                else "N/A"
            ),
            "left": (
                f"{left_elbow_angle:.1f}°"
                if left_elbow_angle is not None
                else "N/A"
            ),
            "status": elbow_status,
            "metric": "Elbow Joint Angle",
            "asymmetry_percent": (
                round(elbow_asymmetry, 1)
                if elbow_asymmetry is not None
                else None
            ),
        },
    ]

    # =====================================================
    # COMPONENT SCORES
    # =====================================================

    component_scores = {
        "knee": (
            round(knee_score, 1)
            if knee_score is not None
            else None
        ),
        "hip": (
            round(hip_score, 1)
            if hip_score is not None
            else None
        ),
        "ankle": (
            round(ankle_score, 1)
            if ankle_score is not None
            else None
        ),
        "shoulder": (
            round(shoulder_score, 1)
            if shoulder_score is not None
            else None
        ),
        "elbow": (
            round(elbow_score, 1)
            if elbow_score is not None
            else None
        ),
    }

    # =====================================================
    # WEIGHTED ALIGNMENT SCORE
    # =====================================================

    weighted_sum = 0.0
    total_weight = 0.0

    for joint, weight in JOINT_WEIGHTS.items():

        score = component_scores.get(joint)

        if score is None:
            continue

        weighted_sum += score * weight
        total_weight += weight

    if total_weight > 0:

        alignment_score = (
            weighted_sum / total_weight
        )

    else:
        alignment_score = 0.0

    alignment_score = round(
        max(
            0.0,
            min(100.0, alignment_score),
        ),
        1,
    )

    # =====================================================
    # OVERALL STATUS
    # =====================================================

    if total_weight == 0:

        overall_status = "Insufficient Data"

    elif alignment_score >= 90:

        overall_status = "Optimal"

    elif alignment_score >= 75:

        overall_status = "Good"

    elif alignment_score >= 60:

        overall_status = "Moderate Deviation"

    else:

        overall_status = "Significant Deviation"

    # =====================================================
    # DATA QUALITY
    # =====================================================

    relevant_joints = [
        "right_knee",
        "left_knee",
        "right_hip",
        "left_hip",
        "right_ankle",
        "left_ankle",
        "right_shoulder",
        "left_shoulder",
        "right_elbow",
        "left_elbow",
    ]

    coverage_values = [
        _get_coverage(
            joint_data,
            joint_name,
        )
        for joint_name in relevant_joints
    ]

    average_coverage = (
        sum(coverage_values)
        / len(coverage_values)
        if coverage_values
        else 0.0
    )

    if average_coverage < 50:

        warnings.append(
            "Low landmark coverage may reduce alignment reliability."
        )

    if right_valgus is None or left_valgus is None:

        warnings.append(
            "Incomplete knee valgus measurements."
        )

    if (
        right_hip_stability is None
        or left_hip_stability is None
    ):

        warnings.append(
            "Hip stability data is incomplete."
        )

    if shoulder_tilt is None:

        warnings.append(
            "Shoulder tilt measurement is unavailable."
        )

    # =====================================================
    # ASYMMETRY SUMMARY
    # =====================================================

    asymmetry = {
        "hip_percent": (
            round(hip_angle_asymmetry, 1)
            if hip_angle_asymmetry is not None
            else None
        ),
        "hip_stability_percent": (
            round(hip_stability_asymmetry, 1)
            if hip_stability_asymmetry is not None
            else None
        ),
        "knee_percent": (
            round(knee_angle_asymmetry, 1)
            if knee_angle_asymmetry is not None
            else None
        ),
        "ankle_percent": (
            round(ankle_asymmetry, 1)
            if ankle_asymmetry is not None
            else None
        ),
        "shoulder_percent": (
            round(shoulder_asymmetry, 1)
            if shoulder_asymmetry is not None
            else None
        ),
        "elbow_percent": (
            round(elbow_asymmetry, 1)
            if elbow_asymmetry is not None
            else None
        ),
    }

    # =====================================================
    # RETURN
    # =====================================================

    return {
        "score": alignment_score,
        "status": overall_status,

        "table": table,

        "asymmetry": asymmetry,

        "component_scores": component_scores,

        "data_quality": {
            "average_joint_coverage_percent": round(
                average_coverage,
                1,
            ),
            "joint_coverage": {
                joint_name: round(
                    _get_coverage(
                        joint_data,
                        joint_name,
                    ),
                    1,
                )
                for joint_name in relevant_joints
            },
        },

        "warnings": warnings,
    }
