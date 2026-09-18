import numpy as np
from typing import List, Dict, Any, Optional


# ============================================================
# Configuration
# ============================================================

MIN_LANDMARK_VISIBILITY = 0.5
EPSILON = 1e-7

# MediaPipe Pose landmark IDs
NOSE = 0

LEFT_SHOULDER = 11
RIGHT_SHOULDER = 12

LEFT_HIP = 23
RIGHT_HIP = 24

LEFT_KNEE = 25
RIGHT_KNEE = 26

LEFT_ANKLE = 27
RIGHT_ANKLE = 28

LEFT_HEEL = 29
RIGHT_HEEL = 30

LEFT_FOOT_INDEX = 31
RIGHT_FOOT_INDEX = 32


# ============================================================
# Utility functions
# ============================================================

def _safe_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    """Safely convert a value to float."""
    try:
        value = float(value)

        if not np.isfinite(value):
            return default

        return value

    except (TypeError, ValueError):
        return default


def _landmark_visible(
    landmark: Dict[str, Any],
    min_visibility: float = MIN_LANDMARK_VISIBILITY
) -> bool:
    """
    Check whether a landmark has valid coordinates and sufficient visibility.
    """

    x = _safe_float(landmark.get("x"))
    y = _safe_float(landmark.get("y"))

    if x is None or y is None:
        return False

    visibility = _safe_float(
        landmark.get("visibility"),
        default=1.0
    )

    return visibility >= min_visibility


def _get_landmarks(
    frame_data: Dict[str, Any]
) -> Dict[int, Dict[str, Any]]:
    """
    Convert landmark list into {landmark_id: landmark}.
    """

    landmarks = frame_data.get("landmarks", [])

    if not isinstance(landmarks, list):
        return {}

    result = {}

    for lm in landmarks:
        if not isinstance(lm, dict):
            continue

        landmark_id = lm.get("landmark_id")

        if landmark_id is None:
            continue

        try:
            landmark_id = int(landmark_id)
        except (TypeError, ValueError):
            continue

        result[landmark_id] = lm

    return result


def _angle_from_horizontal(
    p1: Dict[str, Any],
    p2: Dict[str, Any]
) -> Optional[float]:
    """
    Calculate absolute angle of a line relative to horizontal.
    """

    x1 = _safe_float(p1.get("x"))
    y1 = _safe_float(p1.get("y"))
    x2 = _safe_float(p2.get("x"))
    y2 = _safe_float(p2.get("y"))

    if None in (x1, y1, x2, y2):
        return None

    dx = x2 - x1
    dy = y2 - y1

    if abs(dx) < EPSILON and abs(dy) < EPSILON:
        return None

    angle = np.degrees(np.arctan2(abs(dy), max(abs(dx), EPSILON)))

    return float(angle)


def _horizontal_offset(
    point: Dict[str, Any],
    reference_x: float
) -> Optional[float]:
    """Calculate normalized horizontal displacement."""

    x = _safe_float(point.get("x"))

    if x is None:
        return None

    return float(abs(x - reference_x))


def _normalized_distance(
    p1: Dict[str, Any],
    p2: Dict[str, Any]
) -> Optional[float]:
    """Calculate 2D normalized distance."""

    x1 = _safe_float(p1.get("x"))
    y1 = _safe_float(p1.get("y"))
    x2 = _safe_float(p2.get("x"))
    y2 = _safe_float(p2.get("y"))

    if None in (x1, y1, x2, y2):
        return None

    return float(np.sqrt(
        (x2 - x1) ** 2 +
        (y2 - y1) ** 2
    ))


def _mean_or_none(values: List[float]) -> Optional[float]:
    """Mean that returns None when there is no valid data."""

    if not values:
        return None

    return float(np.mean(values))


def _percentile_or_none(
    values: List[float],
    percentile: float
) -> Optional[float]:
    """Safe percentile."""

    if not values:
        return None

    return float(np.percentile(values, percentile))


# Classification

def _classify(
    value: Optional[float],
    optimal_limit: float,
    moderate_limit: float
) -> str:

    if value is None:
        return "insufficient_data"

    if value < optimal_limit:
        return "optimal"

    if value < moderate_limit:
        return "mild"

    return "moderate"


def _penalty(
    status: str,
    mild_penalty: float,
    moderate_penalty: float
) -> float:

    if status == "mild":
        return mild_penalty

    if status == "moderate":
        return moderate_penalty

    return 0.0


def _build_checklist_item(
    item: str,
    status: str,
    optimal_message: str,
    mild_message: str,
    moderate_message: str,
    value: Optional[float] = None,
    unit: str = ""
) -> Dict[str, Any]:

    if status == "optimal":

        message = optimal_message
        icon = "✓"

    elif status == "mild":

        message = mild_message
        icon = "⚠"

    elif status == "moderate":

        message = moderate_message
        icon = "⚠"

    else:

        message = "Insufficient reliable data for this assessment."
        icon = "?"

    result = {
        "item": item,
        "status": status,
        "icon": icon,
        "message": message
    }

    if value is not None:
        result["value"] = round(value, 2)

        if unit:
            result["unit"] = unit

    return result


# ============================================================
# Main posture analysis
# ============================================================

def analyze_posture(
    frames_landmarks: List[Dict[str, Any]],
    valgus_data: Dict[str, Any],
    hip_data: Dict[str, Any],
    trunk_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Advanced posture and kinetic-chain alignment analysis.

    Evaluates:

    1. Shoulder alignment
    2. Head/cervical alignment
    3. Trunk orientation
    4. Pelvic alignment
    5. Knee tracking
    6. Ankle/foot alignment
    7. Left-right asymmetry
    8. Data quality / confidence

    Returns:
        A structured dictionary containing:
        - posture score
        - component scores
        - alignment measurements
        - deviation checklist
        - confidence
        - data quality
    """

    # --------------------------------------------------------
    # Validate input
    # --------------------------------------------------------

    if not frames_landmarks:

        return {
            "score": 0.0,
            "status": "insufficient_data",
            "confidence": 0.0,
            "checklist": [],
            "message": "No pose landmarks available."
        }

    # --------------------------------------------------------
    # Measurement containers
    # --------------------------------------------------------

    shoulder_tilts = []
    head_offsets = []

    ankle_widths = []

    left_ankle_foot_angles = []
    right_ankle_foot_angles = []

    left_leg_lengths = []
    right_leg_lengths = []

    valid_frames = 0

    # --------------------------------------------------------
    # Frame-level analysis
    # --------------------------------------------------------

    for frame_data in frames_landmarks:

        lm_dict = _get_landmarks(frame_data)

        if not lm_dict:
            continue

        # ----------------------------------------------
        # Required core landmarks
        # ----------------------------------------------

        required = [
            LEFT_SHOULDER,
            RIGHT_SHOULDER
        ]

        if not all(
            landmark_id in lm_dict and
            _landmark_visible(lm_dict[landmark_id])
            for landmark_id in required
        ):
            continue

        valid_frames += 1

        left_shoulder = lm_dict[LEFT_SHOULDER]
        right_shoulder = lm_dict[RIGHT_SHOULDER]

        # ----------------------------------------------
        # Shoulder alignment
        # ----------------------------------------------

        shoulder_angle = _angle_from_horizontal(
            left_shoulder,
            right_shoulder
        )

        if shoulder_angle is not None:
            shoulder_tilts.append(shoulder_angle)

        # ----------------------------------------------
        # Head alignment
        # ----------------------------------------------

        if (
            NOSE in lm_dict
            and _landmark_visible(lm_dict[NOSE])
        ):

            nose = lm_dict[NOSE]

            mid_shoulder_x = (
                _safe_float(left_shoulder.get("x"), 0.0)
                +
                _safe_float(right_shoulder.get("x"), 0.0)
            ) / 2.0

            head_offset = _horizontal_offset(
                nose,
                mid_shoulder_x
            )

            if head_offset is not None:
                head_offsets.append(head_offset)

        # ----------------------------------------------
        # Ankle / foot alignment
        # ----------------------------------------------

        if (
            LEFT_ANKLE in lm_dict
            and RIGHT_ANKLE in lm_dict
            and
            _landmark_visible(lm_dict[LEFT_ANKLE])
            and
            _landmark_visible(lm_dict[RIGHT_ANKLE])
        ):

            left_ankle = lm_dict[LEFT_ANKLE]
            right_ankle = lm_dict[RIGHT_ANKLE]

            ankle_distance = _normalized_distance(
                left_ankle,
                right_ankle
            )

            if ankle_distance is not None:
                ankle_widths.append(ankle_distance)

        # ----------------------------------------------
        # Foot orientation
        # ----------------------------------------------

        if (
            LEFT_HEEL in lm_dict
            and LEFT_FOOT_INDEX in lm_dict
            and
            _landmark_visible(lm_dict[LEFT_HEEL])
            and
            _landmark_visible(lm_dict[LEFT_FOOT_INDEX])
        ):

            left_angle = _angle_from_horizontal(
                lm_dict[LEFT_HEEL],
                lm_dict[LEFT_FOOT_INDEX]
            )

            if left_angle is not None:
                left_ankle_foot_angles.append(left_angle)

        if (
            RIGHT_HEEL in lm_dict
            and RIGHT_FOOT_INDEX in lm_dict
            and
            _landmark_visible(lm_dict[RIGHT_HEEL])
            and
            _landmark_visible(lm_dict[RIGHT_FOOT_INDEX])
        ):

            right_angle = _angle_from_horizontal(
                lm_dict[RIGHT_HEEL],
                lm_dict[RIGHT_FOOT_INDEX]
            )

            if right_angle is not None:
                right_ankle_foot_angles.append(right_angle)

        # ----------------------------------------------
        # Left / right leg length
        # ----------------------------------------------

        if (
            LEFT_HIP in lm_dict
            and LEFT_KNEE in lm_dict
            and LEFT_ANKLE in lm_dict
        ):

            if all(
                _landmark_visible(lm_dict[i])
                for i in [
                    LEFT_HIP,
                    LEFT_KNEE,
                    LEFT_ANKLE
                ]
            ):

                upper = _normalized_distance(
                    lm_dict[LEFT_HIP],
                    lm_dict[LEFT_KNEE]
                )

                lower = _normalized_distance(
                    lm_dict[LEFT_KNEE],
                    lm_dict[LEFT_ANKLE]
                )

                if upper is not None and lower is not None:
                    left_leg_lengths.append(upper + lower)

        if (
            RIGHT_HIP in lm_dict
            and RIGHT_KNEE in lm_dict
            and RIGHT_ANKLE in lm_dict
        ):

            if all(
                _landmark_visible(lm_dict[i])
                for i in [
                    RIGHT_HIP,
                    RIGHT_KNEE,
                    RIGHT_ANKLE
                ]
            ):

                upper = _normalized_distance(
                    lm_dict[RIGHT_HIP],
                    lm_dict[RIGHT_KNEE]
                )

                lower = _normalized_distance(
                    lm_dict[RIGHT_KNEE],
                    lm_dict[RIGHT_ANKLE]
                )

                if upper is not None and lower is not None:
                    right_leg_lengths.append(upper + lower)

    # ========================================================
    # Aggregate measurements
    # ========================================================

    avg_shoulder_tilt = _mean_or_none(shoulder_tilts)
    avg_head_offset = _mean_or_none(head_offsets)

    p90_shoulder_tilt = _percentile_or_none(
        shoulder_tilts,
        90
    )

    p90_head_offset = _percentile_or_none(
        head_offsets,
        90
    )

    avg_ankle_width = _mean_or_none(
        ankle_widths
    )

    avg_left_foot_angle = _mean_or_none(
        left_ankle_foot_angles
    )

    avg_right_foot_angle = _mean_or_none(
        right_ankle_foot_angles
    )

    # ========================================================
    # External module measurements
    # ========================================================

    avg_pelvic_tilt = _safe_float(
        hip_data.get("avg_pelvic_tilt_deg")
    )

    avg_trunk_lean = _safe_float(
        trunk_data.get("avg_trunk_lean_deg")
    )

    max_valgus = _safe_float(
        valgus_data.get("max_deviation")
    )

    # ========================================================
    # Component statuses
    # ========================================================

    shoulder_status = _classify(
        avg_shoulder_tilt,
        optimal_limit=3.0,
        moderate_limit=6.0
    )

    head_status = _classify(
        avg_head_offset,
        optimal_limit=0.03,
        moderate_limit=0.07
    )

    trunk_status = _classify(
        avg_trunk_lean,
        optimal_limit=5.0,
        moderate_limit=12.0
    )

    pelvic_status = _classify(
        avg_pelvic_tilt,
        optimal_limit=4.0,
        moderate_limit=8.0
    )

    valgus_status = _classify(
        max_valgus,
        optimal_limit=5.0,
        moderate_limit=10.0
    )

    # ========================================================
    # Ankle assessment
    # ========================================================

    ankle_status = "insufficient_data"

    if (
        avg_left_foot_angle is not None
        and avg_right_foot_angle is not None
    ):

        foot_asymmetry = abs(
            avg_left_foot_angle
            -
            avg_right_foot_angle
        )

        ankle_status = _classify(
            foot_asymmetry,
            optimal_limit=5.0,
            moderate_limit=12.0
        )

    # ========================================================
    # Checklist
    # ========================================================

    checklist = []

    # --------------------------------------------------------
    # Shoulder
    # --------------------------------------------------------

    checklist.append(
        _build_checklist_item(
            "Shoulder Level",
            shoulder_status,
            "Optimal horizontal shoulder alignment.",
            (
                f"Mild shoulder tilt "
                f"({avg_shoulder_tilt:.1f}°)."
                if avg_shoulder_tilt is not None
                else "Mild shoulder tilt detected."
            ),
            (
                f"Significant shoulder asymmetry "
                f"({avg_shoulder_tilt:.1f}°)."
                if avg_shoulder_tilt is not None
                else "Significant shoulder asymmetry detected."
            ),
            avg_shoulder_tilt,
            "deg"
        )
    )

    # --------------------------------------------------------
    # Head
    # --------------------------------------------------------

    checklist.append(
        _build_checklist_item(
            "Cervical Alignment",
            head_status,
            "Head remains centered over the shoulder midpoint.",
            "Mild lateral head displacement detected.",
            "Significant lateral head displacement detected.",
            avg_head_offset,
            "normalized"
        )
    )

    # --------------------------------------------------------
    # Trunk
    # --------------------------------------------------------

    checklist.append(
        _build_checklist_item(
            "Spine & Trunk Orientation",
            trunk_status,
            "Upright and controlled trunk position.",
            (
                f"Mild trunk lean "
                f"({avg_trunk_lean:.1f}°)."
                if avg_trunk_lean is not None
                else "Mild trunk lean detected."
            ),
            (
                f"Significant trunk lean "
                f"({avg_trunk_lean:.1f}°)."
                if avg_trunk_lean is not None
                else "Significant trunk lean detected."
            ),
            avg_trunk_lean,
            "deg"
        )
    )

    # --------------------------------------------------------
    # Pelvis
    # --------------------------------------------------------

    checklist.append(
        _build_checklist_item(
            "Pelvic Alignment",
            pelvic_status,
            "Pelvis remains relatively level and stable.",
            (
                f"Mild pelvic tilt "
                f"({avg_pelvic_tilt:.1f}°)."
                if avg_pelvic_tilt is not None
                else "Mild pelvic tilt detected."
            ),
            (
                f"Significant pelvic tilt "
                f"({avg_pelvic_tilt:.1f}°)."
                if avg_pelvic_tilt is not None
                else "Significant pelvic tilt detected."
            ),
            avg_pelvic_tilt,
            "deg"
        )
    )

    # --------------------------------------------------------
    # Knee
    # --------------------------------------------------------

    checklist.append(
        _build_checklist_item(
            "Knee Tracking",
            valgus_status,
            "Knee tracking remains within the defined alignment range.",
            (
                f"Mild dynamic knee valgus "
                f"({max_valgus:.1f}°)."
                if max_valgus is not None
                else "Mild knee valgus detected."
            ),
            (
                f"Significant dynamic knee valgus "
                f"({max_valgus:.1f}°)."
                if max_valgus is not None
                else "Significant knee valgus detected."
            ),
            max_valgus,
            "deg"
        )
    )

    # --------------------------------------------------------
    # Ankle
    # --------------------------------------------------------

    ankle_message_value = None

    if (
        avg_left_foot_angle is not None
        and avg_right_foot_angle is not None
    ):
        ankle_message_value = abs(
            avg_left_foot_angle
            -
            avg_right_foot_angle
        )

    checklist.append(
        _build_checklist_item(
            "Ankle & Foot Alignment",
            ankle_status,
            "Left and right foot orientation are reasonably symmetrical.",
            "Mild left-right foot orientation asymmetry detected.",
            "Significant left-right foot orientation asymmetry detected.",
            ankle_message_value,
            "deg"
        )
    )

    # ========================================================
    # Penalty-based component score
    # ========================================================

    penalty_map = {
        "shoulder": _penalty(
            shoulder_status,
            5.0,
            12.0
        ),

        "head": _penalty(
            head_status,
            5.0,
            10.0
        ),

        "trunk": _penalty(
            trunk_status,
            8.0,
            18.0
        ),

        "pelvis": _penalty(
            pelvic_status,
            6.0,
            15.0
        ),

        "knee": _penalty(
            valgus_status,
            8.0,
            20.0
        ),

        "ankle": _penalty(
            ankle_status,
            4.0,
            8.0
        )
    }

    # ========================================================
    # Missing-data handling
    # ========================================================

    statuses = [
        shoulder_status,
        head_status,
        trunk_status,
        pelvic_status,
        valgus_status,
        ankle_status
    ]

    available_components = sum(
        status != "insufficient_data"
        for status in statuses
    )

    total_components = len(statuses)

    data_completeness = (
        available_components / total_components
    )

    # ========================================================
    # Raw posture score
    # ========================================================

    total_penalty = sum(
        penalty_map.values()
    )

    raw_score = max(
        0.0,
        min(
            100.0,
            100.0 - total_penalty
        )
    )

    # ========================================================
    # Confidence
    # ========================================================

    frame_coverage = min(
        1.0,
        valid_frames / max(len(frames_landmarks), 1)
    )

    confidence = (
        0.6 * data_completeness
        +
        0.4 * frame_coverage
    ) * 100.0

    confidence = max(
        0.0,
        min(100.0, confidence)
    )

    # ========================================================
    # Reliability-adjusted score
    # ========================================================

    if confidence < 40.0:

        final_score = raw_score * 0.75

        analysis_status = "low_confidence"

    elif confidence < 70.0:

        final_score = raw_score * 0.90

        analysis_status = "moderate_confidence"

    else:

        final_score = raw_score

        analysis_status = "high_confidence"

    final_score = max(
        0.0,
        min(100.0, final_score)
    )

    # ========================================================
    # Overall classification
    # ========================================================

    if final_score >= 85.0:
        overall_status = "excellent"

    elif final_score >= 70.0:
        overall_status = "good"

    elif final_score >= 50.0:
        overall_status = "needs_attention"

    else:
        overall_status = "poor"

    # ========================================================
    # Identify primary deviations
    # ========================================================

    deviations = []

    for item in checklist:

        if item["status"] in ("mild", "moderate"):

            deviations.append({
                "item": item["item"],
                "severity": item["status"],
                "message": item["message"]
            })

    # Sort moderate deviations first
    deviations.sort(
        key=lambda x: (
            0 if x["severity"] == "moderate" else 1
        )
    )

    # ========================================================
    # Component scores
    # ========================================================

    component_scores = {}

    for name, penalty in penalty_map.items():

        if statuses[
            ["shoulder", "head", "trunk", "pelvis", "knee", "ankle"]
            .index(name)
        ] == "insufficient_data":

            component_scores[name] = None

        else:

            component_scores[name] = round(
                max(0.0, 100.0 - penalty * 5.0),
                1
            )

    # ========================================================
    # Return
    # ========================================================

    return {

        "score": round(final_score, 1),

        "raw_score": round(raw_score, 1),

        "status": overall_status,

        "analysis_status": analysis_status,

        "confidence": round(confidence, 1),

        "data_quality": {
            "valid_frames": valid_frames,
            "total_frames": len(frames_landmarks),
            "frame_coverage_percent": round(
                frame_coverage * 100.0,
                1
            ),
            "component_completeness_percent": round(
                data_completeness * 100.0,
                1
            )
        },

        "measurements": {

            "shoulder_tilt_deg": (
                round(avg_shoulder_tilt, 2)
                if avg_shoulder_tilt is not None
                else None
            ),

            "shoulder_tilt_p90_deg": (
                round(p90_shoulder_tilt, 2)
                if p90_shoulder_tilt is not None
                else None
            ),

            "head_offset_normalized": (
                round(avg_head_offset, 4)
                if avg_head_offset is not None
                else None
            ),

            "head_offset_p90_normalized": (
                round(p90_head_offset, 4)
                if p90_head_offset is not None
                else None
            ),

            "pelvic_tilt_deg": (
                round(avg_pelvic_tilt, 2)
                if avg_pelvic_tilt is not None
                else None
            ),

            "trunk_lean_deg": (
                round(avg_trunk_lean, 2)
                if avg_trunk_lean is not None
                else None
            ),

            "max_knee_valgus_deg": (
                round(max_valgus, 2)
                if max_valgus is not None
                else None
            ),

            "left_foot_angle_deg": (
                round(avg_left_foot_angle, 2)
                if avg_left_foot_angle is not None
                else None
            ),

            "right_foot_angle_deg": (
                round(avg_right_foot_angle, 2)
                if avg_right_foot_angle is not None
                else None
            ),

            "foot_orientation_asymmetry_deg": (
                round(
                    abs(
                        avg_left_foot_angle
                        -
                        avg_right_foot_angle
                    ),
                    2
                )
                if (
                    avg_left_foot_angle is not None
                    and
                    avg_right_foot_angle is not None
                )
                else None
            )
        },

        "component_scores": component_scores,

        "checklist": checklist,

        "primary_deviations": deviations,

        "penalties": {
            key: round(value, 1)
            for key, value in penalty_map.items()
        }
    }