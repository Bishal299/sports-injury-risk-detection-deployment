import numpy as np
from typing import List, Dict, Any, Optional


MIN_LANDMARK_VISIBILITY = 0.5
MIN_SCALE = 0.08
MAX_SCALE = 2.0
MIN_VALID_FRAMES = 5

# MediaPipe Pose landmark IDs
LEFT_SHOULDER = 11
RIGHT_SHOULDER = 12
LEFT_HIP = 23
RIGHT_HIP = 24
LEFT_ANKLE = 27
RIGHT_ANKLE = 28
LEFT_HEEL = 29
RIGHT_HEEL = 30


def _safe_float(value: Any) -> Optional[float]:
    """Safely convert a value to float."""
    try:
        value = float(value)

        if not np.isfinite(value):
            return None

        return value

    except (TypeError, ValueError):
        return None


def _get_landmark(
    lm_dict: Dict[int, Dict[str, Any]],
    landmark_id: int,
    min_visibility: float
) -> Optional[Dict[str, Any]]:
    """
    Return a landmark only when x/y coordinates and visibility are valid.
    """

    lm = lm_dict.get(landmark_id)

    if lm is None:
        return None

    x = _safe_float(lm.get("x"))
    y = _safe_float(lm.get("y"))

    if x is None or y is None:
        return None

    visibility = _safe_float(lm.get("visibility", 1.0))

    if visibility is None:
        visibility = 0.0

    if visibility < min_visibility:
        return None

    return {
        "x": x,
        "y": y,
        "visibility": visibility
    }


def _distance(
    p1: Dict[str, float],
    p2: Dict[str, float]
) -> float:
    """Euclidean distance between two 2D landmarks."""

    return float(
        np.hypot(
            p1["x"] - p2["x"],
            p1["y"] - p2["y"]
        )
    )


def _midpoint(
    p1: Dict[str, float],
    p2: Dict[str, float]
) -> Dict[str, float]:
    """Calculate midpoint between two landmarks."""

    return {
        "x": (p1["x"] + p2["x"]) / 2.0,
        "y": (p1["y"] + p2["y"]) / 2.0
    }


def _robust_scale(values: List[float]) -> Optional[float]:
    """
    Calculate a robust body-length scale.

    Uses the median instead of a single-frame measurement so that
    temporary pose noise does not strongly affect normalization.
    """

    if not values:
        return None

    values = np.asarray(values, dtype=float)

    values = values[np.isfinite(values)]

    if len(values) == 0:
        return None

    return float(np.median(values))


def _symmetric_asymmetry(
    right_value: float,
    left_value: float
) -> float:
    """
    Calculate symmetric percentage asymmetry.

    Formula:
        |R - L| / ((R + L) / 2) * 100

    This is preferable to dividing only by the larger value because
    it treats both sides equally.
    """

    denominator = (abs(right_value) + abs(left_value)) / 2.0

    if denominator < 1e-8:
        return 0.0

    asymmetry = (
        abs(right_value - left_value)
        / denominator
    ) * 100.0

    return float(min(100.0, asymmetry))


def analyze_stride(
    frames_landmarks: List[Dict[str, Any]],
    min_visibility: float = MIN_LANDMARK_VISIBILITY
) -> Dict[str, Any]:
    """
    Analyze lower-limb spacing and locomotion-related kinematics.

    This function intentionally reports a normalized foot-separation /
    step-spacing metric rather than claiming a physically calibrated
    stride length.

    Why:
        True stride length requires reliable temporal foot-contact
        detection and a meaningful movement-direction / spatial scale.
        MediaPipe image coordinates alone cannot guarantee meters.

    Main measurements:
        - normalized foot separation
        - peak normalized foot separation
        - right/left step-spacing estimates
        - right/left asymmetry
        - ankle movement amplitude
        - locomotion indication
        - frame-level time series

    MediaPipe landmarks:
        11 = left shoulder
        12 = right shoulder
        23 = left hip
        24 = right hip
        27 = left ankle
        28 = right ankle
        29 = left heel
        30 = right heel
    """

    # ------------------------------------------------------------------
    # Storage
    # ------------------------------------------------------------------

    separation_series: List[Optional[float]] = []
    left_ankle_series: List[Optional[Dict[str, float]]] = []
    right_ankle_series: List[Optional[Dict[str, float]]] = []

    scale_candidates: List[float] = []

    right_forward_steps: List[float] = []
    left_forward_steps: List[float] = []

    # ------------------------------------------------------------------
    # Process frames
    # ------------------------------------------------------------------

    for frame_index, frame_data in enumerate(frames_landmarks):

        landmarks = frame_data.get("landmarks", [])

        if not landmarks:
            separation_series.append(None)
            left_ankle_series.append(None)
            right_ankle_series.append(None)
            continue

        lm_dict = {
            lm["landmark_id"]: lm
            for lm in landmarks
            if isinstance(lm, dict) and "landmark_id" in lm
        }

        # --------------------------------------------------------------
        # Required landmarks
        # --------------------------------------------------------------

        l_ankle = _get_landmark(
            lm_dict,
            LEFT_ANKLE,
            min_visibility
        )

        r_ankle = _get_landmark(
            lm_dict,
            RIGHT_ANKLE,
            min_visibility
        )

        l_shoulder = _get_landmark(
            lm_dict,
            LEFT_SHOULDER,
            min_visibility
        )

        r_shoulder = _get_landmark(
            lm_dict,
            RIGHT_SHOULDER,
            min_visibility
        )

        l_hip = _get_landmark(
            lm_dict,
            LEFT_HIP,
            min_visibility
        )

        r_hip = _get_landmark(
            lm_dict,
            RIGHT_HIP,
            min_visibility
        )

        # --------------------------------------------------------------
        # If ankle detection is unreliable, preserve frame alignment.
        # --------------------------------------------------------------

        if l_ankle is None or r_ankle is None:

            separation_series.append(None)
            left_ankle_series.append(None)
            right_ankle_series.append(None)

            continue

        left_ankle_series.append({
            "x": l_ankle["x"],
            "y": l_ankle["y"]
        })

        right_ankle_series.append({
            "x": r_ankle["x"],
            "y": r_ankle["y"]
        })

        # --------------------------------------------------------------
        # Calculate body scale
        # --------------------------------------------------------------

        scale_values = []

        if l_shoulder is not None and l_hip is not None:
            scale_values.append(
                _distance(l_shoulder, l_hip)
            )

        if r_shoulder is not None and r_hip is not None:
            scale_values.append(
                _distance(r_shoulder, r_hip)
            )

        if l_hip is not None:
            scale_values.append(
                _distance(l_hip, l_ankle)
            )

        if r_hip is not None:
            scale_values.append(
                _distance(r_hip, r_ankle)
            )

        # Fallback to shoulder-to-ankle geometry.
        if (
            l_shoulder is not None
            and r_shoulder is not None
        ):
            shoulder_mid = _midpoint(
                l_shoulder,
                r_shoulder
            )

            ankle_mid = _midpoint(
                l_ankle,
                r_ankle
            )

            scale_values.append(
                _distance(
                    shoulder_mid,
                    ankle_mid
                )
            )

        if not scale_values:
            separation_series.append(None)
            continue

        frame_scale = float(np.median(scale_values))

        # Reject clearly abnormal scale measurements.
        if (
            not np.isfinite(frame_scale)
            or frame_scale < MIN_SCALE
            or frame_scale > MAX_SCALE
        ):
            separation_series.append(None)
            continue

        scale_candidates.append(frame_scale)

        # --------------------------------------------------------------
        # Calculate ankle separation
        # --------------------------------------------------------------

        ankle_separation = _distance(
            l_ankle,
            r_ankle
        )

        if not np.isfinite(ankle_separation):
            separation_series.append(None)
            continue

        normalized_separation = (
            ankle_separation / frame_scale
        )

        # Prevent extreme pose-estimation outliers.
        if (
            not np.isfinite(normalized_separation)
            or normalized_separation < 0.0
            or normalized_separation > 5.0
        ):
            separation_series.append(None)
            continue

        separation_series.append(
            float(normalized_separation)
        )

        # --------------------------------------------------------------
        # Estimate which foot is forward.
        #
        # This is an image-plane heuristic, NOT a world-coordinate
        # forward-direction estimate.
        # --------------------------------------------------------------

        if r_ankle["x"] > l_ankle["x"]:
            right_forward_steps.append(
                normalized_separation
            )
        else:
            left_forward_steps.append(
                normalized_separation
            )

    # ------------------------------------------------------------------
    # Valid measurements
    # ------------------------------------------------------------------

    valid_separations = [
        value
        for value in separation_series
        if value is not None
        and np.isfinite(value)
    ]

    valid_frames = len(valid_separations)

    # ------------------------------------------------------------------
    # Not enough information
    # ------------------------------------------------------------------

    if valid_frames < MIN_VALID_FRAMES:

        return {
            "valid_frames": valid_frames,
            "is_locomotion_detected": False,

            "normalized_stride_length": None,
            "peak_normalized_stride": None,

            "right_normalized_stride": None,
            "left_normalized_stride": None,

            "stride_asymmetry_pct": None,

            "ankle_movement_amplitude": None,
            "normalized_movement_amplitude": None,

            "body_scale": None,
            "analysis_confidence": 0.0,

            "label": (
                "Normalized Foot Separation "
                "(No spatial calibration required)"
            ),

            "time_series": {
                "stride_separation": separation_series,
                "left_ankle": left_ankle_series,
                "right_ankle": right_ankle_series
            }
        }

    # ------------------------------------------------------------------
    # Robust statistics
    # ------------------------------------------------------------------

    valid_array = np.asarray(
        valid_separations,
        dtype=float
    )

    median_separation = float(
        np.median(valid_array)
    )

    mean_separation = float(
        np.mean(valid_array)
    )

    # Use a high percentile instead of raw max to reduce
    # sensitivity to MediaPipe outliers.
    peak_separation = float(
        np.percentile(valid_array, 95)
    )

    # ------------------------------------------------------------------
    # Right / left estimates
    # ------------------------------------------------------------------

    if right_forward_steps:

        right_array = np.asarray(
            right_forward_steps,
            dtype=float
        )

        right_stride_val = float(
            np.percentile(right_array, 90)
        )

    else:

        right_stride_val = median_separation

    if left_forward_steps:

        left_array = np.asarray(
            left_forward_steps,
            dtype=float
        )

        left_stride_val = float(
            np.percentile(left_array, 90)
        )

    else:

        left_stride_val = median_separation

    # ------------------------------------------------------------------
    # Symmetry
    # ------------------------------------------------------------------

    stride_asymmetry = _symmetric_asymmetry(
        right_stride_val,
        left_stride_val
    )

    # ------------------------------------------------------------------
    # Ankle movement amplitude
    #
    # Instead of only looking at the distance between feet, calculate
    # how much each ankle actually moves in image space.
    # ------------------------------------------------------------------

    left_positions = [
        p for p in left_ankle_series
        if p is not None
    ]

    right_positions = [
        p for p in right_ankle_series
        if p is not None
    ]

    def trajectory_amplitude(
        positions: List[Dict[str, float]]
    ) -> float:

        if len(positions) < 2:
            return 0.0

        points = np.asarray(
            [
                [p["x"], p["y"]]
                for p in positions
            ],
            dtype=float
        )

        # Total movement path.
        differences = np.diff(
            points,
            axis=0
        )

        frame_distances = np.linalg.norm(
            differences,
            axis=1
        )

        frame_distances = frame_distances[
            np.isfinite(frame_distances)
        ]

        if len(frame_distances) == 0:
            return 0.0

        # Median frame movement multiplied by number of transitions
        # gives a robust movement estimate.
        return float(
            np.sum(
                np.minimum(
                    frame_distances,
                    np.percentile(
                        frame_distances,
                        95
                    )
                )
            )
        )

    left_amplitude = trajectory_amplitude(
        left_positions
    )

    right_amplitude = trajectory_amplitude(
        right_positions
    )

    average_amplitude = (
        left_amplitude + right_amplitude
    ) / 2.0

    # ------------------------------------------------------------------
    # Normalize movement amplitude using robust body scale.
    # ------------------------------------------------------------------

    body_scale = _robust_scale(
        scale_candidates
    )

    if body_scale is not None and body_scale > 1e-8:

        normalized_movement_amplitude = (
            average_amplitude / body_scale
        )

    else:

        normalized_movement_amplitude = None

    # ------------------------------------------------------------------
    # Locomotion detection
    #
    # This is intentionally conservative.
    #
    # Foot separation alone is not enough to prove walking/running.
    # We therefore require:
    #
    #   1. enough valid frames
    #   2. meaningful ankle separation
    #   3. some ankle movement
    # ------------------------------------------------------------------

    separation_signal = (
        peak_separation >= 0.15
    )

    movement_signal = (
        normalized_movement_amplitude is not None
        and normalized_movement_amplitude >= 0.10
    )

    locomotion_detected = bool(
        valid_frames >= MIN_VALID_FRAMES
        and separation_signal
        and movement_signal
    )

    # ------------------------------------------------------------------
    # Analysis confidence
    #
    # Based primarily on the percentage of usable frames.
    # ------------------------------------------------------------------

    total_frames = max(
        len(frames_landmarks),
        1
    )

    valid_ratio = valid_frames / total_frames

    # Visibility / tracking quality proxy.
    confidence = min(
        1.0,
        valid_ratio * 1.15
    )

    # Penalize extremely short sequences.
    if valid_frames < 10:
        confidence *= 0.75

    confidence = float(
        np.clip(confidence, 0.0, 1.0)
    )

    # ------------------------------------------------------------------
    # Final result
    # ------------------------------------------------------------------

    return {
        "valid_frames": valid_frames,

        "is_locomotion_detected": locomotion_detected,

        # Backward-compatible field.
        #
        # This is technically normalized foot separation rather than
        # physically calibrated stride length.
        "normalized_stride_length": round(
            median_separation,
            3
        ),

        "peak_normalized_stride": round(
            peak_separation,
            3
        ),

        "right_normalized_stride": round(
            right_stride_val,
            3
        ),

        "left_normalized_stride": round(
            left_stride_val,
            3
        ),

        "stride_asymmetry_pct": round(
            stride_asymmetry,
            1
        ),

        "ankle_movement_amplitude": round(
            average_amplitude,
            3
        ),

        "normalized_movement_amplitude": (
            round(
                normalized_movement_amplitude,
                3
            )
            if normalized_movement_amplitude is not None
            else None
        ),

        "body_scale": (
            round(body_scale, 3)
            if body_scale is not None
            else None
        ),

        "analysis_confidence": round(
            confidence,
            3
        ),

        "label": (
            "Normalized Foot Separation "
            "(Relative to estimated body scale)"
        ),

        "time_series": {
            "stride_separation": [
                round(v, 4)
                if v is not None
                else None
                for v in separation_series
            ],

            "left_ankle": left_ankle_series,

            "right_ankle": right_ankle_series
        }
    }
