import numpy as np
from typing import List, Dict, Any, Optional


MIN_LANDMARK_VISIBILITY = 0.5
EPSILON = 1e-7


def _landmark_valid(
    landmark: Optional[Dict[str, Any]],
    min_visibility: float
) -> bool:
    """Check whether a landmark contains valid coordinates and visibility."""
    if not landmark:
        return False

    try:
        x = float(landmark["x"])
        y = float(landmark["y"])
        visibility = float(landmark.get("visibility", 1.0))

        return (
            np.isfinite(x)
            and np.isfinite(y)
            and np.isfinite(visibility)
            and visibility >= min_visibility
        )
    except (KeyError, TypeError, ValueError):
        return False


def _calculate_knee_angle(
    hip: Dict[str, float],
    knee: Dict[str, float],
    ankle: Dict[str, float]
) -> Optional[float]:
    """
    Calculate the anatomical knee angle in degrees.

    180 degrees = fully extended.
    Smaller values = greater knee flexion.

    This is kept as a supporting metric and is NOT itself
    treated as knee valgus.
    """
    try:
        hip_to_knee = np.array(
            [
                knee["x"] - hip["x"],
                knee["y"] - hip["y"]
            ],
            dtype=np.float64
        )

        ankle_to_knee = np.array(
            [
                knee["x"] - ankle["x"],
                knee["y"] - ankle["y"]
            ],
            dtype=np.float64
        )

        norm_1 = np.linalg.norm(hip_to_knee)
        norm_2 = np.linalg.norm(ankle_to_knee)

        if norm_1 < EPSILON or norm_2 < EPSILON:
            return None

        cosine = np.dot(hip_to_knee, ankle_to_knee) / (
            norm_1 * norm_2
        )

        cosine = np.clip(cosine, -1.0, 1.0)

        angle = np.degrees(np.arccos(cosine))

        return float(angle)

    except (KeyError, TypeError, ValueError, FloatingPointError):
        return None


def _calculate_medial_knee_displacement(
    hip: Dict[str, float],
    knee: Dict[str, float],
    ankle: Dict[str, float],
    is_right: bool
) -> Optional[Dict[str, float]]:
    """
    Estimate frontal-plane medial knee displacement.

    The method:

    1. Creates a reference line from hip to ankle.
    2. Finds where that line intersects the knee's vertical level.
    3. Measures horizontal displacement of the actual knee
       from that reference position.
    4. Converts the displacement into a normalized value
       using hip-to-ankle length.

    Positive normalized displacement indicates movement toward
    the body's estimated midline (medial direction).

    NOTE:
    This is a 2D pose-estimation proxy, not a clinical measurement.
    """

    try:
        hx = float(hip["x"])
        hy = float(hip["y"])

        kx = float(knee["x"])
        ky = float(knee["y"])

        ax = float(ankle["x"])
        ay = float(ankle["y"])

        leg_length = np.hypot(ax - hx, ay - hy)

        if leg_length < EPSILON:
            return None

        # If hip and ankle are almost at the same vertical position,
        # interpolation becomes unstable.
        vertical_difference = ay - hy

        if abs(vertical_difference) < EPSILON:
            return None

        # X-coordinate of the hip-ankle reference line at knee height.
        t = (ky - hy) / vertical_difference

        reference_x = hx + t * (ax - hx)

        horizontal_displacement = kx - reference_x

        # Image coordinates increase from left -> right.
        #
        # Right leg:
        # medial direction is approximately toward image-left.
        #
        # Left leg:
        # medial direction is approximately toward image-right.
        #
        # Therefore convert the displacement into a positive
        # "medial" value.
        if is_right:
            medial_displacement = -horizontal_displacement
        else:
            medial_displacement = horizontal_displacement

        normalized_displacement = (
            medial_displacement / leg_length
        )

        return {
            "displacement": float(medial_displacement),
            "normalized": float(normalized_displacement),
            "reference_x": float(reference_x),
            "leg_length": float(leg_length)
        }

    except (KeyError, TypeError, ValueError, FloatingPointError):
        return None


def _classify_valgus(
    normalized_peak: Optional[float]
) -> str:
    """
    Heuristic classification of normalized medial knee displacement.

    These thresholds are engineering heuristics for this project,
    NOT clinically validated injury-risk thresholds.
    """

    if normalized_peak is None:
        return "Insufficient Data"

    value = abs(normalized_peak)

    if value < 0.05:
        return "Normal"

    if value < 0.10:
        return "Mild"

    if value < 0.15:
        return "Moderate"

    return "High"


def _calculate_alignment_score(
    peak_valgus: Optional[float],
    avg_valgus: Optional[float]
) -> Optional[float]:
    """
    Convert normalized valgus displacement into a 0-100
    alignment quality score.

    Higher = better alignment.

    This is a project-level heuristic, not a clinical score.
    """

    if peak_valgus is None:
        return None

    peak = abs(peak_valgus)
    average = abs(avg_valgus or 0.0)

    # Normalize around project-defined severity ranges.
    score = 100.0 - (
        peak * 300.0 +
        average * 100.0
    )

    return round(
        float(np.clip(score, 0.0, 100.0)),
        1
    )


def _safe_statistics(
    values: List[float]
) -> Dict[str, Optional[float]]:
    """Calculate robust statistics for a list of measurements."""

    valid = [
        float(v)
        for v in values
        if v is not None and np.isfinite(v)
    ]

    if not valid:
        return {
            "valid_frames": 0,
            "max": None,
            "avg": None,
            "std": None
        }

    return {
        "valid_frames": len(valid),
        "max": float(np.max(valid)),
        "avg": float(np.mean(valid)),
        "std": float(np.std(valid))
    }


def analyze_knee_valgus(
    frames_landmarks: List[Dict[str, Any]],
    min_visibility: float = MIN_LANDMARK_VISIBILITY
) -> Dict[str, Any]:
    """
    Analyze frontal-plane knee alignment for both legs.

    MediaPipe Pose landmark mapping:

        Right:
            24 = right hip
            26 = right knee
            28 = right ankle

        Left:
            23 = left hip
            25 = left knee
            27 = left ankle

    Primary metric:
        Normalized medial knee displacement relative to
        the hip-ankle reference line.

    Supporting metric:
        Knee flexion angle.

    Returns:
        Per-leg statistics,
        overall statistics,
        alignment score,
        time-series measurements.

    Important:
        This is a 2D computer-vision estimate and should not be
        presented as a clinical diagnosis or validated injury-risk
        probability.
    """

    right_valgus_series: List[Optional[float]] = []
    left_valgus_series: List[Optional[float]] = []

    right_angle_series: List[Optional[float]] = []
    left_angle_series: List[Optional[float]] = []

    right_displacement_series: List[Optional[float]] = []
    left_displacement_series: List[Optional[float]] = []

    for frame_data in frames_landmarks:

        landmarks = frame_data.get("landmarks", [])

        if not landmarks:
            right_valgus_series.append(None)
            left_valgus_series.append(None)

            right_angle_series.append(None)
            left_angle_series.append(None)

            right_displacement_series.append(None)
            left_displacement_series.append(None)

            continue

        lm_dict = {
            lm["landmark_id"]: lm
            for lm in landmarks
            if isinstance(lm, dict) and "landmark_id" in lm
        }

        # ---------------------------------------------------------
        # RIGHT LEG
        # ---------------------------------------------------------

        right_hip = lm_dict.get(24)
        right_knee = lm_dict.get(26)
        right_ankle = lm_dict.get(28)

        if (
            _landmark_valid(right_hip, min_visibility)
            and _landmark_valid(right_knee, min_visibility)
            and _landmark_valid(right_ankle, min_visibility)
        ):

            result = _calculate_medial_knee_displacement(
                right_hip,
                right_knee,
                right_ankle,
                is_right=True
            )

            knee_angle = _calculate_knee_angle(
                right_hip,
                right_knee,
                right_ankle
            )

            if result is not None:
                right_valgus_series.append(
                    result["normalized"]
                )

                right_displacement_series.append(
                    result["displacement"]
                )
            else:
                right_valgus_series.append(None)
                right_displacement_series.append(None)

            right_angle_series.append(knee_angle)

        else:
            right_valgus_series.append(None)
            right_displacement_series.append(None)
            right_angle_series.append(None)

        # ---------------------------------------------------------
        # LEFT LEG
        # ---------------------------------------------------------

        left_hip = lm_dict.get(23)
        left_knee = lm_dict.get(25)
        left_ankle = lm_dict.get(27)

        if (
            _landmark_valid(left_hip, min_visibility)
            and _landmark_valid(left_knee, min_visibility)
            and _landmark_valid(left_ankle, min_visibility)
        ):

            result = _calculate_medial_knee_displacement(
                left_hip,
                left_knee,
                left_ankle,
                is_right=False
            )

            knee_angle = _calculate_knee_angle(
                left_hip,
                left_knee,
                left_ankle
            )

            if result is not None:
                left_valgus_series.append(
                    result["normalized"]
                )

                left_displacement_series.append(
                    result["displacement"]
                )
            else:
                left_valgus_series.append(None)
                left_displacement_series.append(None)

            left_angle_series.append(knee_angle)

        else:
            left_valgus_series.append(None)
            left_displacement_series.append(None)
            left_angle_series.append(None)

    # -------------------------------------------------------------
    # STATISTICS
    # -------------------------------------------------------------

    right_valid = [
        abs(v)
        for v in right_valgus_series
        if v is not None and np.isfinite(v)
    ]

    left_valid = [
        abs(v)
        for v in left_valgus_series
        if v is not None and np.isfinite(v)
    ]

    right_stats = _safe_statistics(right_valid)
    left_stats = _safe_statistics(left_valid)

    all_valid = right_valid + left_valid

    if all_valid:
        overall_peak = float(np.max(all_valid))
        overall_average = float(np.mean(all_valid))
    else:
        overall_peak = None
        overall_average = None

    score = _calculate_alignment_score(
        overall_peak,
        overall_average
    )

    # -------------------------------------------------------------
    # RISK CLASSIFICATION
    # -------------------------------------------------------------

    right_risk = _classify_valgus(
        right_stats["max"]
    )

    left_risk = _classify_valgus(
        left_stats["max"]
    )

    overall_risk = _classify_valgus(
        overall_peak
    )

    # -------------------------------------------------------------
    # RESULT
    # -------------------------------------------------------------

    return {
        "right": {
            "valid_frames": right_stats["valid_frames"],
            "peak_normalized_valgus": (
                round(right_stats["max"], 4)
                if right_stats["max"] is not None
                else None
            ),
            "avg_normalized_valgus": (
                round(right_stats["avg"], 4)
                if right_stats["avg"] is not None
                else None
            ),
            "std_normalized_valgus": (
                round(right_stats["std"], 4)
                if right_stats["std"] is not None
                else None
            ),
            "risk": right_risk
        },

        "left": {
            "valid_frames": left_stats["valid_frames"],
            "peak_normalized_valgus": (
                round(left_stats["max"], 4)
                if left_stats["max"] is not None
                else None
            ),
            "avg_normalized_valgus": (
                round(left_stats["avg"], 4)
                if left_stats["avg"] is not None
                else None
            ),
            "std_normalized_valgus": (
                round(left_stats["std"], 4)
                if left_stats["std"] is not None
                else None
            ),
            "risk": left_risk
        },

        "score": score,

        "overall_risk": overall_risk,

        "max_deviation": (
            round(overall_peak, 4)
            if overall_peak is not None
            else None
        ),

        "avg_deviation": (
            round(overall_average, 4)
            if overall_average is not None
            else None
        ),

        "time_series": {
            "right": right_valgus_series,
            "left": left_valgus_series
        },

        "supporting_metrics": {
            "right_knee_angle": right_angle_series,
            "left_knee_angle": left_angle_series,
            "right_medial_displacement": right_displacement_series,
            "left_medial_displacement": left_displacement_series
        }
    }
