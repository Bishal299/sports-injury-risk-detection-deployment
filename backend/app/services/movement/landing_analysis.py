import numpy as np
from typing import List, Dict, Any, Optional


MIN_VISIBILITY = 0.5
MIN_FRAMES = 10
MIN_LANDING_DISPLACEMENT = 0.05
LANDING_WINDOW = 8


# MediaPipe Pose landmark IDs
LEFT_SHOULDER = 11
RIGHT_SHOULDER = 12

LEFT_HIP = 23
RIGHT_HIP = 24

LEFT_KNEE = 25
RIGHT_KNEE = 26

LEFT_ANKLE = 27
RIGHT_ANKLE = 28


# ---------------------------------------------------------
# Utility functions
# ---------------------------------------------------------

def _valid_landmark(landmark: Optional[Dict[str, Any]]) -> bool:
    """Check whether a landmark contains usable coordinates."""

    if landmark is None:
        return False

    if "x" not in landmark or "y" not in landmark:
        return False

    visibility = landmark.get("visibility", 1.0)

    return visibility >= MIN_VISIBILITY


def _get_landmarks(frame_data: Dict[str, Any]) -> Dict[int, Dict[str, Any]]:
    """Return landmark dictionary indexed by landmark_id."""

    landmarks = frame_data.get("landmarks", [])

    result = {}

    for lm in landmarks:
        if "landmark_id" not in lm:
            continue

        if _valid_landmark(lm):
            result[lm["landmark_id"]] = lm

    return result


def _midpoint(
    a: Dict[str, Any],
    b: Dict[str, Any]
) -> Optional[np.ndarray]:
    """Calculate midpoint between two landmarks."""

    if not _valid_landmark(a) or not _valid_landmark(b):
        return None

    return np.array([
        (a["x"] + b["x"]) / 2.0,
        (a["y"] + b["y"]) / 2.0
    ])


def _angle_from_vertical(
    top: np.ndarray,
    bottom: np.ndarray
) -> float:
    """
    Calculate trunk lean angle relative to vertical.

    0° = upright
    Larger values = greater trunk lean
    """

    vector = top - bottom

    vertical = np.array([0.0, -1.0])

    norm = np.linalg.norm(vector)

    if norm < 1e-7:
        return 0.0

    vector = vector / norm

    cosine = np.clip(np.dot(vector, vertical), -1.0, 1.0)

    return float(np.degrees(np.arccos(cosine)))


def _safe_average(values: List[float]) -> Optional[float]:
    """Average valid numerical values."""

    valid = [
        float(v)
        for v in values
        if v is not None and np.isfinite(v)
    ]

    if not valid:
        return None

    return float(np.mean(valid))


def _score_from_range(
    value: float,
    good: float,
    poor: float
) -> float:
    """
    Convert a metric into a 20-100 quality score.

    Values at or better than 'good' -> 100
    Values at or worse than 'poor' -> 20
    """

    if value <= good:
        return 100.0

    if value >= poor:
        return 20.0

    score = 100.0 - (
        (value - good) /
        (poor - good)
    ) * 80.0

    return float(np.clip(score, 20.0, 100.0))


# ---------------------------------------------------------
# Main analysis
# ---------------------------------------------------------

def analyze_landing_mechanics(
    frames_landmarks: List[Dict[str, Any]],
    joint_data: Dict[str, Any],
    valgus_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Analyze landing mechanics from pose landmarks and joint data.

    Evaluates:

    - Landing/deceleration detection
    - Knee flexion absorption
    - Hip flexion absorption
    - Trunk control
    - Knee alignment
    - Dynamic balance
    - Left/right asymmetry

    The returned score represents landing quality, not medical
    diagnosis or direct injury probability.
    """

    # -----------------------------------------------------
    # Insufficient frame check
    # -----------------------------------------------------

    if not frames_landmarks or len(frames_landmarks) < MIN_FRAMES:
        return _insufficient_result(
            "Insufficient visual data"
        )

    # -----------------------------------------------------
    # Extract frame-wise landmarks
    # -----------------------------------------------------

    hip_y = []
    hip_positions = []
    trunk_angles = []

    for frame in frames_landmarks:

        lm = _get_landmarks(frame)

        left_hip = lm.get(LEFT_HIP)
        right_hip = lm.get(RIGHT_HIP)

        left_ankle = lm.get(LEFT_ANKLE)
        right_ankle = lm.get(RIGHT_ANKLE)

        left_shoulder = lm.get(LEFT_SHOULDER)
        right_shoulder = lm.get(RIGHT_SHOULDER)

        hip = None
        ankle = None

        if left_hip and right_hip:
            hip = _midpoint(left_hip, right_hip)

        if left_ankle and right_ankle:
            ankle = _midpoint(left_ankle, right_ankle)

        # Hip trajectory
        if hip is not None:
            hip_positions.append(hip)
            hip_y.append(float(hip[1]))
        else:
            hip_positions.append(None)
            hip_y.append(None)

        # Trunk angle
        if (
            left_shoulder
            and right_shoulder
            and left_hip
            and right_hip
        ):
            shoulders = _midpoint(
                left_shoulder,
                right_shoulder
            )

            hips = _midpoint(
                left_hip,
                right_hip
            )

            if shoulders is not None and hips is not None:
                trunk_angles.append(
                    _angle_from_vertical(
                        shoulders,
                        hips
                    )
                )
            else:
                trunk_angles.append(None)
        else:
            trunk_angles.append(None)

    # -----------------------------------------------------
    # Validate hip trajectory
    # -----------------------------------------------------

    valid_hip_indices = [
        i for i, value in enumerate(hip_y)
        if value is not None
    ]

    if len(valid_hip_indices) < MIN_FRAMES:
        return _insufficient_result(
            "Insufficient visual data"
        )

    valid_hips = [
        hip_y[i]
        for i in valid_hip_indices
    ]

    hip_range = max(valid_hips) - min(valid_hips)

    # -----------------------------------------------------
    # Check whether there is enough vertical movement
    # -----------------------------------------------------

    if hip_range < MIN_LANDING_DISPLACEMENT:
        return _insufficient_result(
            "Insufficient visual data "
            "(No significant landing movement detected)"
        )

    # -----------------------------------------------------
    # Calculate hip velocity
    #
    # Positive velocity = downward movement in image space.
    # Negative velocity = upward movement.
    # -----------------------------------------------------

    velocities = []

    for i in range(1, len(hip_y)):

        if (
            hip_y[i] is not None
            and hip_y[i - 1] is not None
        ):
            velocities.append(
                hip_y[i] - hip_y[i - 1]
            )
        else:
            velocities.append(None)

    # -----------------------------------------------------
    # Detect candidate landing/deceleration frame
    #
    # Look for downward motion followed by reduced/
    # reversed vertical velocity.
    # -----------------------------------------------------

    candidate_frames = []

    for i in range(1, len(velocities)):

        previous_velocity = velocities[i - 1]
        current_velocity = velocities[i]

        if (
            previous_velocity is None
            or current_velocity is None
        ):
            continue

        # Downward movement followed by slowing/reversal
        if (
            previous_velocity > 0
            and current_velocity <= previous_velocity
        ):
            candidate_frames.append(i)

    # -----------------------------------------------------
    # Fallback: maximum hip displacement
    #
    # Used only if velocity transition cannot be detected.
    # -----------------------------------------------------

    if candidate_frames:

        impact_frame = candidate_frames[-1]

    else:

        impact_frame = valid_hip_indices[
            int(np.argmax(valid_hips))
        ]

    impact_frame = int(
        np.clip(
            impact_frame,
            0,
            len(frames_landmarks) - 1
        )
    )

    # -----------------------------------------------------
    # Landing analysis window
    # -----------------------------------------------------

    start_idx = max(
        0,
        impact_frame - LANDING_WINDOW
    )

    end_idx = min(
        len(frames_landmarks),
        impact_frame + LANDING_WINDOW + 1
    )

    landing_indices = list(
        range(start_idx, end_idx)
    )

    # -----------------------------------------------------
    # Joint angle time series
    # -----------------------------------------------------

    time_series = joint_data.get(
        "time_series",
        {}
    )

    right_knee = time_series.get(
        "right_knee",
        []
    )

    left_knee = time_series.get(
        "left_knee",
        []
    )

    right_hip = time_series.get(
        "right_hip",
        []
    )

    left_hip = time_series.get(
        "left_hip",
        []
    )

    # -----------------------------------------------------
    # Extract valid knee/hip angles around landing
    # -----------------------------------------------------

    knee_values = []
    hip_values = []

    right_knee_values = []
    left_knee_values = []

    right_hip_values = []
    left_hip_values = []

    for idx in landing_indices:

        if idx < len(right_knee):
            value = right_knee[idx]

            if value is not None and np.isfinite(value):
                right_knee_values.append(float(value))
                knee_values.append(float(value))

        if idx < len(left_knee):
            value = left_knee[idx]

            if value is not None and np.isfinite(value):
                left_knee_values.append(float(value))
                knee_values.append(float(value))

        if idx < len(right_hip):
            value = right_hip[idx]

            if value is not None and np.isfinite(value):
                right_hip_values.append(float(value))
                hip_values.append(float(value))

        if idx < len(left_hip):
            value = left_hip[idx]

            if value is not None and np.isfinite(value):
                left_hip_values.append(float(value))
                hip_values.append(float(value))

    # -----------------------------------------------------
    # Knee absorption
    #
    # Lower joint angle = greater knee flexion.
    #
    # We measure the amount of flexion that occurs
    # during the landing window rather than relying on
    # one frame.
    # -----------------------------------------------------

    if knee_values:

        max_knee_angle = max(knee_values)
        min_knee_angle = min(knee_values)

        knee_excursion = max_knee_angle - min_knee_angle

        # Good landing generally involves meaningful
        # knee flexion rather than remaining stiff.
        knee_score = _score_from_range(
            abs(knee_excursion),
            good=40.0,
            poor=10.0
        )

        avg_knee_angle = _safe_average(
            knee_values
        )

    else:

        knee_excursion = None
        knee_score = None
        avg_knee_angle = None

    # -----------------------------------------------------
    # Hip absorption
    # -----------------------------------------------------

    if hip_values:

        max_hip_angle = max(hip_values)
        min_hip_angle = min(hip_values)

        hip_excursion = max_hip_angle - min_hip_angle

        hip_score = _score_from_range(
            abs(hip_excursion),
            good=30.0,
            poor=8.0
        )

        avg_hip_angle = _safe_average(
            hip_values
        )

    else:

        hip_excursion = None
        hip_score = None
        avg_hip_angle = None

    # -----------------------------------------------------
    # Trunk control
    # -----------------------------------------------------

    landing_trunk_angles = [
        trunk_angles[i]
        for i in landing_indices
        if i < len(trunk_angles)
        and trunk_angles[i] is not None
    ]

    if landing_trunk_angles:

        max_trunk_lean = max(
            landing_trunk_angles
        )

        # Lower trunk lean is better.
        trunk_score = _score_from_range(
            max_trunk_lean,
            good=10.0,
            poor=35.0
        )

    else:

        max_trunk_lean = None
        trunk_score = None

    # -----------------------------------------------------
    # Knee alignment
    # -----------------------------------------------------

    valgus_dev = valgus_data.get(
        "max_deviation"
    )

    if (
        valgus_dev is not None
        and np.isfinite(valgus_dev)
    ):

        valgus_dev = abs(float(valgus_dev))

        align_score = _score_from_range(
            valgus_dev,
            good=5.0,
            poor=20.0
        )

    else:

        align_score = None

    # -----------------------------------------------------
    # Dynamic balance
    #
    # Use COM proxy = midpoint of the hips.
    # Measure displacement during landing window.
    # -----------------------------------------------------

    valid_com = [
        hip_positions[i]
        for i in landing_indices
        if i < len(hip_positions)
        and hip_positions[i] is not None
    ]

    if len(valid_com) >= 3:

        com_array = np.array(
            valid_com
        )

        com_x_range = (
            np.max(com_array[:, 0])
            - np.min(com_array[:, 0])
        )

        com_y_range = (
            np.max(com_array[:, 1])
            - np.min(com_array[:, 1])
        )

        com_displacement = float(
            np.sqrt(
                com_x_range ** 2
                + com_y_range ** 2
            )
        )

        # Excessive horizontal COM movement
        # is treated as reduced balance.
        balance_score = _score_from_range(
            com_x_range,
            good=0.05,
            poor=0.20
        )

    else:

        com_x_range = None
        com_y_range = None
        com_displacement = None
        balance_score = None

    # -----------------------------------------------------
    # Left/right asymmetry
    # -----------------------------------------------------

    asymmetry_values = []

    if right_knee_values and left_knee_values:

        right_knee_mean = np.mean(
            right_knee_values
        )

        left_knee_mean = np.mean(
            left_knee_values
        )

        knee_asymmetry = abs(
            right_knee_mean
            - left_knee_mean
        )

        asymmetry_values.append(
            knee_asymmetry
        )

    else:

        knee_asymmetry = None

    if right_hip_values and left_hip_values:

        right_hip_mean = np.mean(
            right_hip_values
        )

        left_hip_mean = np.mean(
            left_hip_values
        )

        hip_asymmetry = abs(
            right_hip_mean
            - left_hip_mean
        )

        asymmetry_values.append(
            hip_asymmetry
        )

    else:

        hip_asymmetry = None

    if asymmetry_values:

        overall_asymmetry = float(
            np.mean(asymmetry_values)
        )

    else:

        overall_asymmetry = None

    # -----------------------------------------------------
    # Build available metric scores
    # -----------------------------------------------------

    scores = []

    if knee_score is not None:
        scores.append(
            ("knee", knee_score, 0.35)
        )

    if hip_score is not None:
        scores.append(
            ("hip", hip_score, 0.20)
        )

    if trunk_score is not None:
        scores.append(
            ("trunk", trunk_score, 0.15)
        )

    if align_score is not None:
        scores.append(
            ("alignment", align_score, 0.20)
        )

    if balance_score is not None:
        scores.append(
            ("balance", balance_score, 0.10)
        )

    # -----------------------------------------------------
    # Normalize weights if some metrics are unavailable.
    # -----------------------------------------------------

    if scores:

        total_weight = sum(
            weight
            for _, _, weight in scores
        )

        overall_landing_score = sum(
            score * weight
            for _, score, weight in scores
        ) / total_weight

        overall_landing_score = round(
            float(overall_landing_score),
            1
        )

    else:

        overall_landing_score = None

    # -----------------------------------------------------
    # Convert angles to flexion representation.
    # -----------------------------------------------------

    if avg_knee_angle is not None:
        knee_flexion_deg = round(
            180.0 - avg_knee_angle,
            1
        )
    else:
        knee_flexion_deg = None

    if avg_hip_angle is not None:
        hip_flexion_deg = round(
            180.0 - avg_hip_angle,
            1
        )
    else:
        hip_flexion_deg = None

    # -----------------------------------------------------
    # Return results
    # -----------------------------------------------------

    return {
        "has_landing_data": True,
        "status": "Landing event analyzed",

        "score": overall_landing_score,

        "impact_frame": impact_frame,

        "landing_window": {
            "start_frame": start_idx,
            "end_frame": end_idx - 1
        },

        "knee_flexion_deg": knee_flexion_deg,

        "hip_flexion_deg": hip_flexion_deg,

        "knee_flexion_excursion_deg": (
            round(knee_excursion, 1)
            if knee_excursion is not None
            else None
        ),

        "hip_flexion_excursion_deg": (
            round(hip_excursion, 1)
            if hip_excursion is not None
            else None
        ),

        "trunk_lean_deg": (
            round(max_trunk_lean, 1)
            if max_trunk_lean is not None
            else None
        ),

        "valgus_deviation_deg": (
            round(valgus_dev, 1)
            if valgus_dev is not None
            else None
        ),

        "balance": {
            "com_horizontal_range": (
                round(com_x_range, 4)
                if com_x_range is not None
                else None
            ),

            "com_vertical_range": (
                round(com_y_range, 4)
                if com_y_range is not None
                else None
            ),

            "com_displacement": (
                round(com_displacement, 4)
                if com_displacement is not None
                else None
            )
        },

        "asymmetry": {
            "knee_asymmetry_deg": (
                round(knee_asymmetry, 1)
                if knee_asymmetry is not None
                else None
            ),

            "hip_asymmetry_deg": (
                round(hip_asymmetry, 1)
                if hip_asymmetry is not None
                else None
            ),

            "overall_asymmetry_deg": (
                round(overall_asymmetry, 1)
                if overall_asymmetry is not None
                else None
            )
        },

        "submetrics": {
            "knee_absorption": (
                f"{round(knee_score, 1)} / 100"
                if knee_score is not None
                else "Insufficient visual data"
            ),

            "hip_absorption": (
                f"{round(hip_score, 1)} / 100"
                if hip_score is not None
                else "Insufficient visual data"
            ),

            "trunk_control": (
                f"{round(trunk_score, 1)} / 100"
                if trunk_score is not None
                else "Insufficient visual data"
            ),

            "alignment": (
                f"{round(align_score, 1)} / 100"
                if align_score is not None
                else "Insufficient visual data"
            ),

            "balance": (
                f"{round(balance_score, 1)} / 100"
                if balance_score is not None
                else "Insufficient visual data"
            )
        }
    }


# ---------------------------------------------------------
# Insufficient-data response
# ---------------------------------------------------------

def _insufficient_result(
    status: str
) -> Dict[str, Any]:
    """Standard insufficient-data response."""

    return {
        "has_landing_data": False,
        "status": status,
        "score": None,

        "submetrics": {
            "knee_absorption": "Insufficient visual data",
            "hip_absorption": "Insufficient visual data",
            "trunk_control": "Insufficient visual data",
            "alignment": "Insufficient visual data",
            "balance": "Insufficient visual data"
        }
    }
