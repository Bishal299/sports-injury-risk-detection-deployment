import numpy as np
from typing import List, Dict, Any, Optional


MIN_LANDMARK_VISIBILITY = 0.5
MIN_VALID_FRAMES = 5


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


def _get_landmark(
    lm_dict: Dict[int, Dict[str, Any]],
    landmark_id: int,
    min_visibility: float
) -> Optional[Dict[str, float]]:
    """
    Returns a landmark only when it exists and has sufficient visibility.
    """
    lm = lm_dict.get(landmark_id)

    if lm is None:
        return None

    visibility = lm.get("visibility", 1.0)

    if visibility < min_visibility:
        return None

    if "x" not in lm or "y" not in lm:
        return None

    try:
        x = float(lm["x"])
        y = float(lm["y"])

        if not np.isfinite(x) or not np.isfinite(y):
            return None

        return {
            "x": x,
            "y": y,
            "visibility": float(visibility)
        }

    except (TypeError, ValueError):
        return None


def _midpoint(
    p1: Dict[str, float],
    p2: Dict[str, float]
) -> tuple:
    """
    Returns midpoint between two landmarks.
    """
    return (
        (p1["x"] + p2["x"]) / 2.0,
        (p1["y"] + p2["y"]) / 2.0
    )


def _safe_std(values: List[float]) -> Optional[float]:
    if not values:
        return None

    return float(np.std(values))


def _safe_range(values: List[float]) -> Optional[float]:
    if not values:
        return None

    return float(np.max(values) - np.min(values))


def analyze_balance(
    frames_landmarks: List[Dict[str, Any]],
    min_visibility: float = MIN_LANDMARK_VISIBILITY
) -> Dict[str, Any]:
    """
    Analyzes static and dynamic balance using:

    1. Center of Mass (COM) proxy
    2. Base of Support (BOS) approximation
    3. Lateral sway
    4. Anterior-posterior sway
    5. COM-to-BOS relationship
    6. Left/right stance asymmetry

    MediaPipe coordinates are assumed to be normalized to [0, 1].

    Important:
    This is a vision-based COM proxy, NOT a true biomechanical
    center of mass measurement. No force plate or inertial data
    is available.
    """

    com_x_series: List[Optional[float]] = []
    com_y_series: List[Optional[float]] = []

    bos_width_series: List[Optional[float]] = []
    com_bos_offset_series: List[Optional[float]] = []

    left_ankle_x_series: List[Optional[float]] = []
    right_ankle_x_series: List[Optional[float]] = []

    body_width_series: List[Optional[float]] = []

    for frame_data in frames_landmarks:

        landmarks = frame_data.get("landmarks", [])

        if not landmarks:
            com_x_series.append(None)
            com_y_series.append(None)
            bos_width_series.append(None)
            com_bos_offset_series.append(None)
            left_ankle_x_series.append(None)
            right_ankle_x_series.append(None)
            body_width_series.append(None)
            continue

        lm_dict = {
            lm["landmark_id"]: lm
            for lm in landmarks
            if "landmark_id" in lm
        }

        required_ids = [
            NOSE,
            LEFT_SHOULDER,
            RIGHT_SHOULDER,
            LEFT_HIP,
            RIGHT_HIP,
            LEFT_KNEE,
            RIGHT_KNEE,
            LEFT_ANKLE,
            RIGHT_ANKLE
        ]

        points = {}

        valid_frame = True

        for landmark_id in required_ids:

            point = _get_landmark(
                lm_dict,
                landmark_id,
                min_visibility
            )

            if point is None:
                valid_frame = False
                break

            points[landmark_id] = point

        if not valid_frame:
            com_x_series.append(None)
            com_y_series.append(None)
            bos_width_series.append(None)
            com_bos_offset_series.append(None)
            left_ankle_x_series.append(None)
            right_ankle_x_series.append(None)
            body_width_series.append(None)
            continue

        # ---------------------------------------------------------
        # Body segment centers
        # ---------------------------------------------------------

        head = points[NOSE]

        shoulder_x, shoulder_y = _midpoint(
            points[LEFT_SHOULDER],
            points[RIGHT_SHOULDER]
        )
                          
        hip_x, hip_y = _midpoint(
            points[LEFT_HIP],
            points[RIGHT_HIP]
        )

        knee_x, knee_y = _midpoint(
            points[LEFT_KNEE],
            points[RIGHT_KNEE]
        )

        ankle_x, ankle_y = _midpoint(
            points[LEFT_ANKLE],
            points[RIGHT_ANKLE]
        )

        # ---------------------------------------------------------
        # Approximate COM
        # ---------------------------------------------------------
        #
        # Segment weights sum to 1:
        #
        # Head       = 0.08
        # Trunk      = 0.48
        # Thighs     = 0.24
        # Lower legs = 0.12
        # Feet       = 0.08
        #
        # The trunk is approximated by the midpoint between
        # shoulders and hips.
        # ---------------------------------------------------------

        trunk_x = (shoulder_x + hip_x) / 2.0
        trunk_y = (shoulder_y + hip_y) / 2.0

        com_x = (
            0.08 * head["x"]
            + 0.48 * trunk_x
            + 0.24 * hip_x
            + 0.12 * knee_x
            + 0.08 * ankle_x
        )

        com_y = (
            0.08 * head["y"]
            + 0.48 * trunk_y
            + 0.24 * hip_y
            + 0.12 * knee_y
            + 0.08 * ankle_y
        )

        # ---------------------------------------------------------
        # Base of Support
        # ---------------------------------------------------------

        left_ankle_x = points[LEFT_ANKLE]["x"]
        right_ankle_x = points[RIGHT_ANKLE]["x"]

        bos_width = abs(
            right_ankle_x - left_ankle_x
        )

        bos_center_x = (
            left_ankle_x + right_ankle_x
        ) / 2.0

        # Distance of COM projection from center of BOS.
        com_bos_offset = abs(
            com_x - bos_center_x
        )

        # Shoulder width used for normalization.
        shoulder_width = abs(
            points[RIGHT_SHOULDER]["x"]
            - points[LEFT_SHOULDER]["x"]
        )

        # Avoid division by zero.
        if shoulder_width <= 1e-6:
            shoulder_width = None

        # ---------------------------------------------------------
        # Store values
        # ---------------------------------------------------------

        com_x_series.append(round(float(com_x), 4))
        com_y_series.append(round(float(com_y), 4))

        bos_width_series.append(
            round(float(bos_width), 4)
        )

        com_bos_offset_series.append(
            round(float(com_bos_offset), 4)
        )

        left_ankle_x_series.append(
            round(float(left_ankle_x), 4)
        )

        right_ankle_x_series.append(
            round(float(right_ankle_x), 4)
        )

        body_width_series.append(
            round(float(shoulder_width), 4)
            if shoulder_width is not None
            else None
        )

    # =============================================================
    # Valid observations
    # =============================================================

    valid_indices = [
        i
        for i, x in enumerate(com_x_series)
        if x is not None
        and com_y_series[i] is not None
    ]

    valid_com_x = [
        com_x_series[i]
        for i in valid_indices
    ]

    valid_com_y = [
        com_y_series[i]
        for i in valid_indices
    ]

    valid_bos = [
        bos_width_series[i]
        for i in valid_indices
        if bos_width_series[i] is not None
    ]

    valid_com_bos_offset = [
        com_bos_offset_series[i]
        for i in valid_indices
        if com_bos_offset_series[i] is not None
    ]

    # =============================================================
    # Default results
    # =============================================================

    total_frames = len(frames_landmarks)

    valid_frames = len(valid_indices)

    valid_frame_ratio = (
        valid_frames / total_frames
        if total_frames > 0
        else 0.0
    )

    lat_sway_std = None
    lat_sway_range = None

    ap_sway_std = None
    ap_sway_range = None

    avg_bos = None
    avg_com_bos_offset = None

    normalized_lateral_sway = None
    normalized_ap_sway = None

    balance_score = None

    # =============================================================
    # Calculate balance metrics
    # =============================================================

    if valid_frames >= MIN_VALID_FRAMES:

        # Lateral movement
        lat_sway_std = _safe_std(valid_com_x)
        lat_sway_range = _safe_range(valid_com_x)

        # Anterior-posterior movement
        ap_sway_std = _safe_std(valid_com_y)
        ap_sway_range = _safe_range(valid_com_y)

        # Average BOS
        avg_bos = (
            float(np.mean(valid_bos))
            if valid_bos
            else None
        )

        # Average COM-to-BOS offset
        avg_com_bos_offset = (
            float(np.mean(valid_com_bos_offset))
            if valid_com_bos_offset
            else None
        )

        # ---------------------------------------------------------
        # Body-size normalization
        # ---------------------------------------------------------

        valid_body_widths = [
            body_width_series[i]
            for i in valid_indices
            if body_width_series[i] is not None
            and body_width_series[i] > 1e-6
        ]

        if valid_body_widths:

            reference_width = float(
                np.median(valid_body_widths)
            )

            normalized_lateral_sway = (
                lat_sway_std / reference_width
                if lat_sway_std is not None
                else None
            )

            normalized_ap_sway = (
                ap_sway_std / reference_width
                if ap_sway_std is not None
                else None
            )

        # ---------------------------------------------------------
        # Balance score
        # ---------------------------------------------------------
        #
        # Lower sway = better balance.
        #
        # The values below are intentionally moderate so that
        # normal MediaPipe tracking noise does not immediately
        # destroy the score.
        # ---------------------------------------------------------

        lateral_component = 0.0
        ap_component = 0.0
        offset_component = 0.0

        if normalized_lateral_sway is not None:
            lateral_component = min(
                normalized_lateral_sway * 100.0,
                40.0
            )

        if normalized_ap_sway is not None:
            ap_component = min(
                normalized_ap_sway * 60.0,
                30.0
            )

        if avg_com_bos_offset is not None:
            offset_component = min(
                avg_com_bos_offset * 100.0,
                30.0
            )

        total_penalty = (
            lateral_component
            + ap_component
            + offset_component
        )

        balance_score = round(
            max(
                0.0,
                min(
                    100.0,
                    100.0 - total_penalty
                )
            ),
            1
        )

    # =============================================================
    # Left/right stance asymmetry
    # =============================================================

    valid_left = [
        left_ankle_x_series[i]
        for i in valid_indices
        if left_ankle_x_series[i] is not None
    ]

    valid_right = [
        right_ankle_x_series[i]
        for i in valid_indices
        if right_ankle_x_series[i] is not None
    ]

    stance_asymmetry = None

    if valid_left and valid_right:

        left_mean = float(np.mean(valid_left))
        right_mean = float(np.mean(valid_right))

        stance_width = abs(
            right_mean - left_mean
        )

        if stance_width > 1e-6:

            left_deviation = abs(
                left_mean - (left_mean + right_mean) / 2.0
            )

            right_deviation = abs(
                right_mean - (left_mean + right_mean) / 2.0
            )

            stance_asymmetry = round(
                abs(left_deviation - right_deviation)
                / stance_width
                * 100.0,
                2
            )

    # =============================================================
    # Balance classification
    # =============================================================

    balance_status = None

    if balance_score is not None:

        if balance_score >= 85:
            balance_status = "good"

        elif balance_score >= 70:
            balance_status = "moderate"

        else:
            balance_status = "poor"

    # =============================================================
    # Final result
    # =============================================================

    return {
        "valid_frames": valid_frames,
        "total_frames": total_frames,
        "valid_frame_ratio": round(
            float(valid_frame_ratio),
            3
        ),

        "score": balance_score,
        "status": balance_status,

        "lateral_sway_std": (
            round(float(lat_sway_std), 4)
            if lat_sway_std is not None
            else None
        ),

        "lateral_sway_range": (
            round(float(lat_sway_range), 4)
            if lat_sway_range is not None
            else None
        ),

        "ap_sway_std": (
            round(float(ap_sway_std), 4)
            if ap_sway_std is not None
            else None
        ),

        "ap_sway_range": (
            round(float(ap_sway_range), 4)
            if ap_sway_range is not None
            else None
        ),

        "normalized_lateral_sway": (
            round(float(normalized_lateral_sway), 4)
            if normalized_lateral_sway is not None
            else None
        ),

        "normalized_ap_sway": (
            round(float(normalized_ap_sway), 4)
            if normalized_ap_sway is not None
            else None
        ),

        "avg_base_of_support": (
            round(float(avg_bos), 4)
            if avg_bos is not None
            else None
        ),

        "avg_com_bos_offset": (
            round(float(avg_com_bos_offset), 4)
            if avg_com_bos_offset is not None
            else None
        ),

        "stance_asymmetry": stance_asymmetry,

        "time_series": {
            "com_x": com_x_series,
            "com_y": com_y_series,
            "bos_width": bos_width_series,
            "com_bos_offset": com_bos_offset_series,
            "left_ankle_x": left_ankle_x_series,
            "right_ankle_x": right_ankle_x_series
        }
    }