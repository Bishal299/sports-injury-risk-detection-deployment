import numpy as np
from typing import List, Dict, Any, Optional


MIN_LANDMARK_VISIBILITY = 0.5
EPSILON = 1e-7


# MediaPipe Pose landmark indices
LANDMARKS = {
    "left_shoulder": 11,
    "right_shoulder": 12,
    "left_elbow": 13,
    "right_elbow": 14,
    "left_wrist": 15,
    "right_wrist": 16,
    "left_hip": 23,
    "right_hip": 24,
    "left_knee": 25,
    "right_knee": 26,
    "left_ankle": 27,
    "right_ankle": 28,
    "left_foot_index": 31,
    "right_foot_index": 32,
}


# Each tuple represents:
# (point1, joint/vertex, point3)
JOINT_DEFINITIONS = {
    "right_knee": (
        "right_hip",
        "right_knee",
        "right_ankle",
    ),
    "left_knee": (
        "left_hip",
        "left_knee",
        "left_ankle",
    ),
    "right_hip": (
        "right_shoulder",
        "right_hip",
        "right_knee",
    ),
    "left_hip": (
        "left_shoulder",
        "left_hip",
        "left_knee",
    ),
    "right_ankle": (
        "right_knee",
        "right_ankle",
        "right_foot_index",
    ),
    "left_ankle": (
        "left_knee",
        "left_ankle",
        "left_foot_index",
    ),
    "right_shoulder": (
        "right_hip",
        "right_shoulder",
        "right_elbow",
    ),
    "left_shoulder": (
        "left_hip",
        "left_shoulder",
        "left_elbow",
    ),
    "right_elbow": (
        "right_shoulder",
        "right_elbow",
        "right_wrist",
    ),
    "left_elbow": (
        "left_shoulder",
        "left_elbow",
        "left_wrist",
    ),
}


def _is_valid_number(value: Any) -> bool:
    """Return True if value is a finite numeric value."""
    try:
        return np.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def _is_valid_landmark(
    landmark: Optional[Dict[str, Any]],
    min_visibility: float = MIN_LANDMARK_VISIBILITY,
    require_z: bool = False,
) -> bool:
    """
    Validate a MediaPipe landmark before using it.

    Checks:
    - landmark exists
    - x/y are finite
    - visibility is above threshold
    - z is present and finite when required
    """
    if not landmark:
        return False

    if not _is_valid_number(landmark.get("x")):
        return False

    if not _is_valid_number(landmark.get("y")):
        return False

    visibility = landmark.get("visibility", 1.0)

    if not _is_valid_number(visibility):
        return False

    if float(visibility) < min_visibility:
        return False

    if require_z:
        if not _is_valid_number(landmark.get("z")):
            return False

    return True


def calculate_3pt_angle(
    p1: Dict[str, float],
    p2: Dict[str, float],
    p3: Dict[str, float],
    use_3d: bool = True,
    min_visibility: float = MIN_LANDMARK_VISIBILITY,
) -> Optional[float]:
    """
    Calculate the interior angle at p2 formed by p1-p2-p3.

    Returns:
        Angle in degrees [0, 180], or None if the landmarks are invalid.

    Notes:
        - Uses 3D coordinates when use_3d=True and valid z values exist.
        - Falls back to 2D when 3D coordinates are unavailable.
        - Rejects landmarks below the visibility threshold.
    """

    if not p1 or not p2 or not p3:
        return None

    # First validate x/y/visibility.
    if not (
        _is_valid_landmark(p1, min_visibility)
        and _is_valid_landmark(p2, min_visibility)
        and _is_valid_landmark(p3, min_visibility)
    ):
        return None

    use_valid_3d = (
        use_3d
        and _is_valid_number(p1.get("z"))
        and _is_valid_number(p2.get("z"))
        and _is_valid_number(p3.get("z"))
    )

    try:
        if use_valid_3d:
            v1 = np.array(
                [
                    float(p1["x"]) - float(p2["x"]),
                    float(p1["y"]) - float(p2["y"]),
                    float(p1["z"]) - float(p2["z"]),
                ],
                dtype=np.float64,
            )

            v2 = np.array(
                [
                    float(p3["x"]) - float(p2["x"]),
                    float(p3["y"]) - float(p2["y"]),
                    float(p3["z"]) - float(p2["z"]),
                ],
                dtype=np.float64,
            )

        else:
            v1 = np.array(
                [
                    float(p1["x"]) - float(p2["x"]),
                    float(p1["y"]) - float(p2["y"]),
                ],
                dtype=np.float64,
            )

            v2 = np.array(
                [
                    float(p3["x"]) - float(p2["x"]),
                    float(p3["y"]) - float(p2["y"]),
                ],
                dtype=np.float64,
            )

        norm_v1 = np.linalg.norm(v1)
        norm_v2 = np.linalg.norm(v2)

        if norm_v1 < EPSILON or norm_v2 < EPSILON:
            return None

        denominator = norm_v1 * norm_v2

        cosine = float(np.dot(v1, v2) / denominator)

        # Protect against floating-point errors such as
        # 1.0000000002 or -1.0000000001.
        cosine = float(np.clip(cosine, -1.0, 1.0))

        angle = float(np.degrees(np.arccos(cosine)))

        if not np.isfinite(angle):
            return None

        return round(angle, 2)

    except (TypeError, ValueError, KeyError, FloatingPointError):
        return None


def _moving_average(
    values: List[Optional[float]],
    window: int = 5,
) -> List[Optional[float]]:
    """
    Simple moving average that preserves None values.

    Only averages contiguous valid observations.
    """
    if window <= 1:
        return values.copy()

    result: List[Optional[float]] = []

    for i in range(len(values)):
        start = max(0, i - window + 1)

        window_values = values[start : i + 1]

        valid_values = [
            float(v)
            for v in window_values
            if v is not None and np.isfinite(v)
        ]

        if not valid_values:
            result.append(None)
        else:
            result.append(float(np.mean(valid_values)))

    return result


def _calculate_derivative(
    values: List[Optional[float]],
    timeline: List[float],
) -> List[Optional[float]]:
    """
    Calculate first derivative of angle with respect to time.

    Result:
        Angular velocity in degrees/second.

    Uses the previous valid observation.
    """

    result: List[Optional[float]] = [None] * len(values)

    previous_index: Optional[int] = None

    for i, value in enumerate(values):

        if value is None or not np.isfinite(value):
            continue

        if previous_index is None:
            previous_index = i
            continue

        dt = timeline[i] - timeline[previous_index]

        if dt <= 0:
            previous_index = i
            continue

        velocity = (
            float(value) - float(values[previous_index])
        ) / dt

        if np.isfinite(velocity):
            result[i] = float(velocity)

        previous_index = i

    return result


def _calculate_summary(
    values: List[Optional[float]],
) -> Dict[str, Any]:
    """
    Calculate robust summary statistics for a time-series.
    """

    valid_values = [
        float(v)
        for v in values
        if v is not None and np.isfinite(v)
    ]

    if not valid_values:
        return {
            "valid_frames": 0,
            "coverage_percent": 0.0,
            "current_angle": None,
            "min_angle": None,
            "max_angle": None,
            "avg_angle": None,
            "std_angle": None,
            "rom": None,
        }

    min_val = float(np.min(valid_values))
    max_val = float(np.max(valid_values))
    avg_val = float(np.mean(valid_values))
    std_val = float(np.std(valid_values))

    # Last valid observation.
    current_val = valid_values[-1]

    observed_rom = max_val - min_val

    return {
        "valid_frames": len(valid_values),
        "coverage_percent": None,
        "current_angle": round(current_val, 1),
        "min_angle": round(min_val, 1),
        "max_angle": round(max_val, 1),
        "avg_angle": round(avg_val, 1),
        "std_angle": round(std_val, 2),
        "rom": round(observed_rom, 1),
    }


def _calculate_motion_summary(
    velocity: List[Optional[float]],
    acceleration: List[Optional[float]],
) -> Dict[str, Optional[float]]:
    """
    Calculate movement-speed summaries.

    Velocity:
        degrees/second

    Acceleration:
        degrees/second²
    """

    valid_velocity = [
        float(v)
        for v in velocity
        if v is not None and np.isfinite(v)
    ]

    valid_acceleration = [
        float(a)
        for a in acceleration
        if a is not None and np.isfinite(a)
    ]

    return {
        "peak_angular_velocity": (
            round(float(np.max(np.abs(valid_velocity))), 2)
            if valid_velocity
            else None
        ),
        "mean_angular_velocity": (
            round(float(np.mean(np.abs(valid_velocity))), 2)
            if valid_velocity
            else None
        ),
        "peak_angular_acceleration": (
            round(float(np.max(np.abs(valid_acceleration))), 2)
            if valid_acceleration
            else None
        ),
    }


def calculate_joint_angles(
    frames_landmarks: List[Dict[str, Any]],
    min_visibility: float = MIN_LANDMARK_VISIBILITY,
    use_3d: bool = True,
    smoothing_window: int = 5,
) -> Dict[str, Any]:
    """
    Calculate joint-angle kinematics from MediaPipe pose landmarks.

    Outputs:
        - timeline
        - raw angle time-series
        - smoothed angle time-series
        - angular velocity
        - angular acceleration
        - joint summaries
        - motion summaries
        - overall data quality

    The ROM reported here is OBSERVED ROM during the supplied video,
    not maximum anatomical ROM.
    """

    joint_series: Dict[str, List[Optional[float]]] = {
        joint_name: []
        for joint_name in JOINT_DEFINITIONS
    }

    timeline: List[float] = []

    # ---------------------------------------------------------
    # FRAME PROCESSING
    # ---------------------------------------------------------

    for frame_data in frames_landmarks:

        timestamp_ms = frame_data.get("timestamp_ms")

        if not _is_valid_number(timestamp_ms):
            timestamp_ms = 0.0

        time_sec = float(timestamp_ms) / 1000.0

        timeline.append(round(time_sec, 3))

        landmarks = frame_data.get("landmarks", [])

        if not isinstance(landmarks, list):
            landmarks = []

        # Create landmark dictionary.
        lm_dict = {}

        for landmark in landmarks:

            if not isinstance(landmark, dict):
                continue

            landmark_id = landmark.get("landmark_id")

            if landmark_id is None:
                continue

            try:
                landmark_id = int(landmark_id)
            except (TypeError, ValueError):
                continue

            lm_dict[landmark_id] = landmark

        # Calculate every joint from the centralized definition.
        for joint_name, (
            point1_name,
            point2_name,
            point3_name,
        ) in JOINT_DEFINITIONS.items():

            p1_id = LANDMARKS[point1_name]
            p2_id = LANDMARKS[point2_name]
            p3_id = LANDMARKS[point3_name]

            p1 = lm_dict.get(p1_id)
            p2 = lm_dict.get(p2_id)
            p3 = lm_dict.get(p3_id)

            angle = calculate_3pt_angle(
                p1,
                p2,
                p3,
                use_3d=use_3d,
                min_visibility=min_visibility,
            )

            joint_series[joint_name].append(angle)

    # ---------------------------------------------------------
    # DATA QUALITY
    # ---------------------------------------------------------

    total_frames = len(timeline)

    joint_quality = {}

    for joint_name, values in joint_series.items():

        valid_count = sum(
            1
            for value in values
            if value is not None and np.isfinite(value)
        )

        coverage = (
            (valid_count / total_frames) * 100.0
            if total_frames > 0
            else 0.0
        )

        joint_quality[joint_name] = {
            "valid_frames": valid_count,
            "total_frames": total_frames,
            "coverage_percent": round(coverage, 1),
        }

    # ---------------------------------------------------------
    # SMOOTHING
    # ---------------------------------------------------------

    smoothed_series: Dict[str, List[Optional[float]]] = {}

    for joint_name, values in joint_series.items():

        smoothed = _moving_average(
            values,
            window=smoothing_window,
        )

        smoothed_series[joint_name] = [
            round(float(v), 2) if v is not None else None
            for v in smoothed
        ]

    # ---------------------------------------------------------
    # ANGULAR VELOCITY
    # ---------------------------------------------------------

    angular_velocity: Dict[str, List[Optional[float]]] = {}

    for joint_name, values in smoothed_series.items():

        velocity = _calculate_derivative(
            values,
            timeline,
        )

        angular_velocity[joint_name] = [
            round(float(v), 2) if v is not None else None
            for v in velocity
        ]

    # ---------------------------------------------------------
    # ANGULAR ACCELERATION
    # ---------------------------------------------------------

    angular_acceleration: Dict[str, List[Optional[float]]] = {}

    for joint_name, velocity in angular_velocity.items():

        acceleration = _calculate_derivative(
            velocity,
            timeline,
        )

        angular_acceleration[joint_name] = [
            round(float(v), 2) if v is not None else None
            for v in acceleration
        ]

    # ---------------------------------------------------------
    # SUMMARY
    # ---------------------------------------------------------

    summary: Dict[str, Any] = {}

    for joint_name, values in joint_series.items():

        joint_summary = _calculate_summary(values)

        coverage = joint_quality[joint_name]["coverage_percent"]

        joint_summary["coverage_percent"] = coverage

        # Motion statistics use smoothed data.
        motion_summary = _calculate_motion_summary(
            angular_velocity[joint_name],
            angular_acceleration[joint_name],
        )

        joint_summary.update(motion_summary)

        summary[joint_name] = joint_summary

    # ---------------------------------------------------------
    # OVERALL DATA QUALITY
    # ---------------------------------------------------------

    if total_frames > 0:

        coverage_values = [
            data["coverage_percent"]
            for data in joint_quality.values()
        ]

        overall_coverage = float(np.mean(coverage_values))

    else:
        overall_coverage = 0.0

    return {
        "timeline": timeline,

        # Original raw measurements.
        "time_series": joint_series,

        # Smoothed measurements.
        "smoothed_time_series": smoothed_series,

        # Angular velocity in degrees/second.
        "angular_velocity": angular_velocity,

        # Angular acceleration in degrees/second².
        "angular_acceleration": angular_acceleration,

        # Per-joint summary.
        "summary": summary,

        # Data quality information.
        "quality": {
            "total_frames": total_frames,
            "overall_coverage_percent": round(
                overall_coverage,
                1,
            ),
            "joint_coverage": joint_quality,
            "min_landmark_visibility": min_visibility,
            "using_3d": use_3d,
            "smoothing_window": smoothing_window,
        },
    }