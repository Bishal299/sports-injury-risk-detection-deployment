import numpy as np
from typing import List, Dict, Any, Optional


MIN_LANDMARK_VISIBILITY = 0.5
DEFAULT_FPS = 30.0

# Smoothing window for reducing pose-estimation jitter
SMOOTHING_WINDOW = 5

# Maximum reasonable pelvic tilt used for normalization.
# This is NOT a medical threshold.
MAX_EXPECTED_TILT_DEG = 20.0


def _safe_float(value: Any) -> Optional[float]:
    """Safely convert a value to float."""
    try:
        value = float(value)
        if np.isfinite(value):
            return value
    except (TypeError, ValueError):
        pass

    return None


def _moving_average(
    values: List[Optional[float]],
    window: int = SMOOTHING_WINDOW
) -> List[Optional[float]]:
    """
    Smooth a time series while preserving None values.

    Only nearby valid values are used for averaging.
    """
    if window <= 1:
        return values.copy()

    result = []

    for i in range(len(values)):
        start = max(0, i - window // 2)
        end = min(len(values), i + window // 2 + 1)

        valid = [
            values[j]
            for j in range(start, end)
            if values[j] is not None and np.isfinite(values[j])
        ]

        if valid:
            result.append(float(np.mean(valid)))
        else:
            result.append(None)

    return result


def _calculate_angle_from_horizontal(
    left_hip: Dict[str, Any],
    right_hip: Dict[str, Any]
) -> Optional[float]:
    """
    Calculate pelvic tilt relative to the horizontal axis.

    Returns an angle approximately in the range [-90, 90].

    Positive:
        right hip is lower than left hip in image coordinates.

    Negative:
        right hip is higher than left hip.

    Note:
        MediaPipe image Y usually increases downward.
    """

    lx = _safe_float(left_hip.get("x"))
    ly = _safe_float(left_hip.get("y"))
    rx = _safe_float(right_hip.get("x"))
    ry = _safe_float(right_hip.get("y"))

    if None in (lx, ly, rx, ry):
        return None

    dx = rx - lx
    dy = ry - ly

    if abs(dx) < 1e-6:
        return None

    angle = np.degrees(np.arctan2(dy, abs(dx)))

    # Keep the value numerically safe
    angle = max(-90.0, min(90.0, float(angle)))

    return angle


def _calculate_midpoint(
    left_hip: Dict[str, Any],
    right_hip: Dict[str, Any]
) -> Optional[tuple]:
    """Calculate the midpoint between the two hip landmarks."""

    lx = _safe_float(left_hip.get("x"))
    ly = _safe_float(left_hip.get("y"))
    rx = _safe_float(right_hip.get("x"))
    ry = _safe_float(right_hip.get("y"))

    if None in (lx, ly, rx, ry):
        return None

    return (
        (lx + rx) / 2.0,
        (ly + ry) / 2.0
    )


def _calculate_hip_width(
    left_hip: Dict[str, Any],
    right_hip: Dict[str, Any]
) -> Optional[float]:
    """Calculate distance between left and right hip landmarks."""

    lx = _safe_float(left_hip.get("x"))
    ly = _safe_float(left_hip.get("y"))
    rx = _safe_float(right_hip.get("x"))
    ry = _safe_float(right_hip.get("y"))

    if None in (lx, ly, rx, ry):
        return None

    distance = np.sqrt(
        (rx - lx) ** 2 +
        (ry - ly) ** 2
    )

    if distance <= 1e-6:
        return None

    return float(distance)


def _calculate_derivative(
    values: List[Optional[float]],
    fps: float
) -> List[Optional[float]]:
    """
    Calculate frame-to-frame velocity.

    Missing frames produce None.
    """

    if fps <= 0:
        fps = DEFAULT_FPS

    dt = 1.0 / fps
    result = [None] * len(values)

    for i in range(1, len(values)):
        if values[i] is None or values[i - 1] is None:
            continue

        result[i] = (values[i] - values[i - 1]) / dt

    return result


def _mean_absolute(
    values: List[Optional[float]]
) -> Optional[float]:
    """Mean absolute value of a time series."""

    valid = [
        abs(v)
        for v in values
        if v is not None and np.isfinite(v)
    ]

    if not valid:
        return None

    return float(np.mean(valid))


def _range(
    values: List[Optional[float]]
) -> Optional[float]:
    """Range of valid values."""

    valid = [
        v
        for v in values
        if v is not None and np.isfinite(v)
    ]

    if not valid:
        return None

    return float(np.max(valid) - np.min(valid))


def analyze_hip_stability(
    frames_landmarks: List[Dict[str, Any]],
    min_visibility: float = MIN_LANDMARK_VISIBILITY,
    fps: float = DEFAULT_FPS,
    smooth: bool = True
) -> Dict[str, Any]:
    """
    Analyze hip/pelvic movement stability using pose landmarks.

    MediaPipe landmarks:
        23 = left hip
        24 = right hip

    Main measurements:
        - Pelvic tilt
        - Pelvic tilt variability
        - Pelvic midpoint movement
        - Normalized pelvic displacement
        - Pelvic velocity
        - Pelvic acceleration
        - Left/right pelvic tilt distribution
        - Movement-control symmetry
        - Vision-based hip stability proxy score

    IMPORTANT:
        This does NOT directly measure clinical hip stability,
        joint loading, muscle strength, or injury probability.

        It provides a vision-based movement-control proxy.
    """

    if not frames_landmarks:
        return {
            "valid_frames": 0,
            "total_frames": 0,
            "valid_frame_ratio": 0.0,
            "score": None,
            "right_hip_stability": None,
            "left_hip_stability": None,
            "symmetry_score": None,
            "avg_pelvic_tilt_deg": None,
            "max_pelvic_tilt_deg": None,
            "tilt_variation_std": None,
            "pelvic_displacement_2d": None,
            "pelvic_displacement_x": None,
            "pelvic_displacement_y": None,
            "normalized_displacement": None,
            "mean_pelvic_velocity": None,
            "max_pelvic_velocity": None,
            "mean_pelvic_acceleration": None,
            "max_pelvic_acceleration": None,
            "time_series": {
                "pelvic_tilt": [],
                "midpoint_x": [],
                "midpoint_y": [],
                "normalized_midpoint_x": [],
                "normalized_midpoint_y": [],
                "pelvic_velocity": [],
                "pelvic_acceleration": []
            }
        }

    tilt_series = []
    midpoint_x_series = []
    midpoint_y_series = []
    hip_width_series = []

    total_frames = len(frames_landmarks)

    # ---------------------------------------------------------
    # 1. Extract hip landmarks frame by frame
    # ---------------------------------------------------------

    for frame_data in frames_landmarks:

        landmarks = frame_data.get("landmarks", [])

        if not landmarks:
            tilt_series.append(None)
            midpoint_x_series.append(None)
            midpoint_y_series.append(None)
            hip_width_series.append(None)
            continue

        lm_dict = {
            lm["landmark_id"]: lm
            for lm in landmarks
            if "landmark_id" in lm
        }

        if 23 not in lm_dict or 24 not in lm_dict:
            tilt_series.append(None)
            midpoint_x_series.append(None)
            midpoint_y_series.append(None)
            hip_width_series.append(None)
            continue

        left_hip = lm_dict[23]
        right_hip = lm_dict[24]

        left_visibility = _safe_float(
            left_hip.get("visibility", 1.0)
        )

        right_visibility = _safe_float(
            right_hip.get("visibility", 1.0)
        )

        if (
            left_visibility is None
            or right_visibility is None
            or left_visibility < min_visibility
            or right_visibility < min_visibility
        ):
            tilt_series.append(None)
            midpoint_x_series.append(None)
            midpoint_y_series.append(None)
            hip_width_series.append(None)
            continue

        # Pelvic tilt
        tilt = _calculate_angle_from_horizontal(
            left_hip,
            right_hip
        )

        # Pelvic midpoint
        midpoint = _calculate_midpoint(
            left_hip,
            right_hip
        )

        # Hip width
        hip_width = _calculate_hip_width(
            left_hip,
            right_hip
        )

        if tilt is None or midpoint is None or hip_width is None:
            tilt_series.append(None)
            midpoint_x_series.append(None)
            midpoint_y_series.append(None)
            hip_width_series.append(None)
            continue

        tilt_series.append(round(tilt, 3))
        midpoint_x_series.append(round(midpoint[0], 5))
        midpoint_y_series.append(round(midpoint[1], 5))
        hip_width_series.append(round(hip_width, 5))

    # ---------------------------------------------------------
    # 2. Smooth pose noise
    # ---------------------------------------------------------

    if smooth:
        tilt_series = _moving_average(tilt_series)
        midpoint_x_series = _moving_average(midpoint_x_series)
        midpoint_y_series = _moving_average(midpoint_y_series)

    # ---------------------------------------------------------
    # 3. Valid frames
    # ---------------------------------------------------------

    valid_indices = [
        i
        for i in range(total_frames)
        if (
            tilt_series[i] is not None
            and midpoint_x_series[i] is not None
            and midpoint_y_series[i] is not None
        )
    ]

    valid_frames = len(valid_indices)

    valid_frame_ratio = (
        valid_frames / total_frames
        if total_frames > 0
        else 0.0
    )

    if valid_frames == 0:
        return {
            "valid_frames": 0,
            "total_frames": total_frames,
            "valid_frame_ratio": 0.0,
            "score": None,
            "right_hip_stability": None,
            "left_hip_stability": None,
            "symmetry_score": None,
            "avg_pelvic_tilt_deg": None,
            "max_pelvic_tilt_deg": None,
            "tilt_variation_std": None,
            "pelvic_displacement_2d": None,
            "pelvic_displacement_x": None,
            "pelvic_displacement_y": None,
            "normalized_displacement": None,
            "mean_pelvic_velocity": None,
            "max_pelvic_velocity": None,
            "mean_pelvic_acceleration": None,
            "max_pelvic_acceleration": None,
            "time_series": {
                "pelvic_tilt": tilt_series,
                "midpoint_x": midpoint_x_series,
                "midpoint_y": midpoint_y_series,
                "normalized_midpoint_x": [None] * total_frames,
                "normalized_midpoint_y": [None] * total_frames,
                "pelvic_velocity": [None] * total_frames,
                "pelvic_acceleration": [None] * total_frames
            }
        }

    # ---------------------------------------------------------
    # 4. Pelvic tilt statistics
    # ---------------------------------------------------------

    valid_tilts = [
        abs(tilt_series[i])
        for i in valid_indices
    ]

    avg_tilt = float(np.mean(valid_tilts))
    max_tilt = float(np.max(valid_tilts))
    tilt_std = float(np.std(valid_tilts))

    # ---------------------------------------------------------
    # 5. Pelvic displacement
    # ---------------------------------------------------------

    valid_xs = [
        midpoint_x_series[i]
        for i in valid_indices
    ]

    valid_ys = [
        midpoint_y_series[i]
        for i in valid_indices
    ]

    x_range = float(np.max(valid_xs) - np.min(valid_xs))
    y_range = float(np.max(valid_ys) - np.min(valid_ys))

    # Total 2D displacement across bounding range
    displacement_2d = float(
        np.sqrt(
            x_range ** 2 +
            y_range ** 2
        )
    )

    # ---------------------------------------------------------
    # 6. Normalize movement using hip width
    # ---------------------------------------------------------

    valid_hip_widths = [
        hip_width_series[i]
        for i in valid_indices
        if hip_width_series[i] is not None
        and hip_width_series[i] > 1e-6
    ]

    if valid_hip_widths:
        reference_hip_width = float(
            np.median(valid_hip_widths)
        )
    else:
        reference_hip_width = None

    if reference_hip_width:
        normalized_x = [
            (
                (x - valid_xs[0]) / reference_hip_width
                if x is not None
                else None
            )
            for x in midpoint_x_series
        ]

        normalized_y = [
            (
                (y - valid_ys[0]) / reference_hip_width
                if y is not None
                else None
            )
            for y in midpoint_y_series
        ]

        normalized_displacement = (
            displacement_2d / reference_hip_width
        )
    else:
        normalized_x = [None] * total_frames
        normalized_y = [None] * total_frames
        normalized_displacement = None

    # ---------------------------------------------------------
    # 7. Pelvic velocity
    # ---------------------------------------------------------

    velocity_x = _calculate_derivative(
        normalized_x,
        fps
    )

    velocity_y = _calculate_derivative(
        normalized_y,
        fps
    )

    pelvic_velocity = []

    for vx, vy in zip(velocity_x, velocity_y):

        if vx is None or vy is None:
            pelvic_velocity.append(None)
            continue

        pelvic_velocity.append(
            float(np.sqrt(vx ** 2 + vy ** 2))
        )

    valid_velocities = [
        v
        for v in pelvic_velocity
        if v is not None and np.isfinite(v)
    ]

    if valid_velocities:
        mean_velocity = float(np.mean(valid_velocities))
        max_velocity = float(np.max(valid_velocities))
    else:
        mean_velocity = None
        max_velocity = None

    # ---------------------------------------------------------
    # 8. Pelvic acceleration
    # ---------------------------------------------------------

    pelvic_acceleration = _calculate_derivative(
        pelvic_velocity,
        fps
    )

    valid_accelerations = [
        abs(a)
        for a in pelvic_acceleration
        if a is not None and np.isfinite(a)
    ]

    if valid_accelerations:
        mean_acceleration = float(
            np.mean(valid_accelerations)
        )

        max_acceleration = float(
            np.max(valid_accelerations)
        )
    else:
        mean_acceleration = None
        max_acceleration = None

    # ---------------------------------------------------------
    # 9. Right vs left pelvic tilt distribution
    # ---------------------------------------------------------

    raw_tilts = [
        tilt_series[i]
        for i in valid_indices
    ]

    positive_tilts = [
        abs(t)
        for t in raw_tilts
        if t > 0
    ]

    negative_tilts = [
        abs(t)
        for t in raw_tilts
        if t < 0
    ]

    right_mean_drop = (
        float(np.mean(positive_tilts))
        if positive_tilts
        else 0.0
    )

    left_mean_drop = (
        float(np.mean(negative_tilts))
        if negative_tilts
        else 0.0
    )

    # ---------------------------------------------------------
    # 10. Directional symmetry
    # ---------------------------------------------------------

    directional_difference = abs(
        right_mean_drop - left_mean_drop
    )

    directional_total = (
        right_mean_drop +
        left_mean_drop
    )

    if directional_total > 1e-6:
        symmetry_score = (
            100.0 -
            (
                directional_difference /
                directional_total
            ) * 100.0
        )
    else:
        symmetry_score = 100.0

    symmetry_score = max(
        0.0,
        min(100.0, symmetry_score)
    )

    # ---------------------------------------------------------
    # 11. Stability proxy score
    # ---------------------------------------------------------
    #
    # IMPORTANT:
    # These are heuristic engineering weights.
    # They are NOT medical thresholds.
    #

    tilt_component = min(
        100.0,
        (avg_tilt / MAX_EXPECTED_TILT_DEG) * 100.0
    )

    variability_component = min(
        100.0,
        (tilt_std / 10.0) * 100.0
    )

    displacement_component = (
        min(
            100.0,
            normalized_displacement / 1.0 * 100.0
        )
        if normalized_displacement is not None
        else 0.0
    )

    symmetry_penalty = 100.0 - symmetry_score

    # Overall movement-control instability
    instability = (
        tilt_component * 0.35 +
        variability_component * 0.25 +
        displacement_component * 0.20 +
        symmetry_penalty * 0.20
    )

    hip_stability_score = max(
        0.0,
        min(100.0, 100.0 - instability)
    )

    # ---------------------------------------------------------
    # 12. Side-specific stability proxies
    # ---------------------------------------------------------

    right_stability = max(
        0.0,
        min(
            100.0,
            100.0 -
            (
                right_mean_drop * 4.0 +
                tilt_std * 3.0
            )
        )
    )

    left_stability = max(
        0.0,
        min(
            100.0,
            100.0 -
            (
                left_mean_drop * 4.0 +
                tilt_std * 3.0
            )
        )
    )

    # ---------------------------------------------------------
    # 13. Return results
    # ---------------------------------------------------------

    return {
        "valid_frames": valid_frames,
        "total_frames": total_frames,
        "valid_frame_ratio": round(
            valid_frame_ratio,
            3
        ),

        # Main score
        "score": round(
            hip_stability_score,
            1
        ),

        "score_type": "vision_based_stability_proxy",

        # Side scores
        "right_hip_stability": round(
            right_stability,
            1
        ),

        "left_hip_stability": round(
            left_stability,
            1
        ),

        "symmetry_score": round(
            symmetry_score,
            1
        ),

        # Pelvic tilt
        "avg_pelvic_tilt_deg": round(
            avg_tilt,
            2
        ),

        "max_pelvic_tilt_deg": round(
            max_tilt,
            2
        ),

        "tilt_variation_std": round(
            tilt_std,
            3
        ),

        # Pelvic displacement
        "pelvic_displacement_2d": round(
            displacement_2d,
            4
        ),

        "pelvic_displacement_x": round(
            x_range,
            4
        ),

        "pelvic_displacement_y": round(
            y_range,
            4
        ),

        "normalized_displacement": (
            round(normalized_displacement, 3)
            if normalized_displacement is not None
            else None
        ),

        # Dynamic control
        "mean_pelvic_velocity": (
            round(mean_velocity, 3)
            if mean_velocity is not None
            else None
        ),

        "max_pelvic_velocity": (
            round(max_velocity, 3)
            if max_velocity is not None
            else None
        ),

        "mean_pelvic_acceleration": (
            round(mean_acceleration, 3)
            if mean_acceleration is not None
            else None
        ),

        "max_pelvic_acceleration": (
            round(max_acceleration, 3)
            if max_acceleration is not None
            else None
        ),

        # Raw directional information
        "right_mean_pelvic_drop_deg": round(
            right_mean_drop,
            2
        ),

        "left_mean_pelvic_drop_deg": round(
            left_mean_drop,
            2
        ),

        # Time series
        "time_series": {
            "pelvic_tilt": [
                round(v, 3) if v is not None else None
                for v in tilt_series
            ],

            "midpoint_x": [
                round(v, 5) if v is not None else None
                for v in midpoint_x_series
            ],

            "midpoint_y": [
                round(v, 5) if v is not None else None
                for v in midpoint_y_series
            ],

            "normalized_midpoint_x": [
                round(v, 5) if v is not None else None
                for v in normalized_x
            ],

            "normalized_midpoint_y": [
                round(v, 5) if v is not None else None
                for v in normalized_y
            ],

            "pelvic_velocity": [
                round(v, 4) if v is not None else None
                for v in pelvic_velocity
            ],

            "pelvic_acceleration": [
                round(v, 4) if v is not None else None
                for v in pelvic_acceleration
            ]
        }
    }