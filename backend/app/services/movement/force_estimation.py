import numpy as np
from typing import Dict, Any, List, Optional


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

DEFAULT_FPS = 30.0
MIN_VALID_POINTS = 8

GRAVITY = 9.81

# Filtering
SMOOTHING_WINDOW = 5

# Reasonable safety bounds for a VIDEO-DERIVED force proxy.
# These are not medical/force-plate limits.
MIN_FORCE_BW = 0.0
MAX_FORCE_BW = 8.0


# ---------------------------------------------------------
# Utility functions
# ---------------------------------------------------------

def _moving_average(values: np.ndarray, window: int) -> np.ndarray:
    """
    Smooth a 1D signal using a centered moving average.
    """
    if len(values) < 3:
        return values.copy()

    window = min(window, len(values))

    if window % 2 == 0:
        window -= 1

    if window < 3:
        return values.copy()

    kernel = np.ones(window) / window

    padded = np.pad(
        values,
        (window // 2, window // 2),
        mode="edge"
    )

    return np.convolve(padded, kernel, mode="valid")


def _interpolate_missing(values: List[Optional[float]]) -> np.ndarray:
    """
    Interpolates missing values in a time series.
    """
    arr = np.asarray(
        [np.nan if v is None else float(v) for v in values],
        dtype=float
    )

    valid = np.isfinite(arr)

    if valid.sum() < 2:
        return arr

    indices = np.arange(len(arr))

    arr[~valid] = np.interp(
        indices[~valid],
        indices[valid],
        arr[valid]
    )

    return arr


def _safe_float(value: Any) -> Optional[float]:
    """
    Safely convert a value to float.
    """
    try:
        value = float(value)

        if np.isfinite(value):
            return value

    except (TypeError, ValueError):
        pass

    return None


# ---------------------------------------------------------
# Main Force Analysis
# ---------------------------------------------------------

def estimate_visual_forces(
    balance_data: Dict[str, Any],
    fps: float = DEFAULT_FPS,
    athlete_profile: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Estimates vertical ground-reaction force from video-derived
    center-of-mass movement.

    IMPORTANT:
    This is a visual/kinematic proxy and is NOT equivalent to
    force-plate or laboratory biomechanical measurement.

    Athlete height and weight should come from the athlete profile.

    Expected athlete_profile structure:

        {
            "height_cm": 173,
            "weight_kg": 64
        }

    or:

        {
            "height": 173,
            "weight": 64
        }

    Returns:
        Dictionary containing:
        - peak force
        - peak force in bodyweights
        - average force
        - loading rate
        - impulse proxy
        - impact duration
        - impact count
        - acceleration
        - confidence
        - time-series force
    """

    # -----------------------------------------------------
    # 1. Validate FPS
    # -----------------------------------------------------

    if fps is None or fps <= 0:
        fps = DEFAULT_FPS

    dt = 1.0 / fps

    # -----------------------------------------------------
    # 2. Get athlete profile
    # -----------------------------------------------------

    athlete_profile = athlete_profile or {}

    height_cm = (
        _safe_float(athlete_profile.get("height_cm"))
        or _safe_float(athlete_profile.get("height"))
    )

    weight_kg = (
        _safe_float(athlete_profile.get("weight_kg"))
        or _safe_float(athlete_profile.get("weight"))
    )

    # We do NOT silently pretend that the athlete weighs 70 kg.
    # Profile data should be supplied by the backend.
    profile_valid = (
        height_cm is not None
        and weight_kg is not None
        and height_cm > 100
        and height_cm < 250
        and weight_kg > 20
        and weight_kg < 250
    )

    if not profile_valid:

        return {
            "label": "Estimated Force / Visual Proxy",
            "status": "insufficient_profile_data",
            "disclaimer": (
                "Force values require athlete height and weight from "
                "the athlete profile. This is a video-derived proxy "
                "and is not equivalent to force-plate measurement."
            ),
            "estimated_body_mass_kg": None,
            "athlete_height_cm": None,
            "peak_force_n": None,
            "peak_force_bw": None,
            "avg_force_n": None,
            "loading_rate_n_s": None,
            "impact_duration_ms": None,
            "impulse_ns": None,
            "impact_count": 0,
            "peak_acceleration_ms2": None,
            "confidence": 0.0,
            "time_series_force": []
        }

    # -----------------------------------------------------
    # 3. Extract COM Y trajectory
    # -----------------------------------------------------

    time_series = balance_data.get("time_series", {})

    com_y_series = time_series.get("com_y", [])

    if not com_y_series:

        return {
            "label": "Estimated Force / Visual Proxy",
            "status": "insufficient_motion_data",
            "disclaimer": (
                "Insufficient center-of-mass movement data for "
                "visual force estimation."
            ),
            "estimated_body_mass_kg": round(weight_kg, 2),
            "athlete_height_cm": round(height_cm, 2),
            "peak_force_n": None,
            "peak_force_bw": None,
            "avg_force_n": None,
            "loading_rate_n_s": None,
            "impact_duration_ms": None,
            "impulse_ns": None,
            "impact_count": 0,
            "peak_acceleration_ms2": None,
            "confidence": 0.0,
            "time_series_force": []
        }

    # -----------------------------------------------------
    # 4. Interpolate missing COM values
    # -----------------------------------------------------

    com_y = _interpolate_missing(com_y_series)

    valid_count = int(np.isfinite(com_y).sum())

    if valid_count < MIN_VALID_POINTS:

        return {
            "label": "Estimated Force / Visual Proxy",
            "status": "insufficient_motion_data",
            "disclaimer": (
                "Insufficient valid COM samples for visual force estimation."
            ),
            "estimated_body_mass_kg": round(weight_kg, 2),
            "athlete_height_cm": round(height_cm, 2),
            "peak_force_n": None,
            "peak_force_bw": None,
            "avg_force_n": None,
            "loading_rate_n_s": None,
            "impact_duration_ms": None,
            "impulse_ns": None,
            "impact_count": 0,
            "peak_acceleration_ms2": None,
            "confidence": 0.0,
            "time_series_force": []
        }

    # -----------------------------------------------------
    # 5. Smooth COM
    # -----------------------------------------------------

    smoothed_y = _moving_average(
        com_y,
        SMOOTHING_WINDOW
    )

    # -----------------------------------------------------
    # 6. Convert normalized coordinates to approximate meters
    # -----------------------------------------------------
    #
    # MediaPipe Y is normalized approximately from 0 to 1.
    #
    # Instead of assuming every athlete is 1.7 m tall,
    # use the athlete's actual height.
    #
    # The COM trajectory is not the full body height, so we
    # use athlete height as the reference scale.
    #
    # This remains a VISUAL APPROXIMATION because camera
    # perspective and depth are unknown.
    # -----------------------------------------------------

    height_m = height_cm / 100.0

    # Normalized MediaPipe coordinate → approximate metric scale.
    #
    # The 0.8 factor represents the approximate normalized
    # vertical body span visible in a typical pose.
    #
    # Athlete-specific height is now used.
    pixels_to_meter_scale = height_m / 0.8

    com_y_metric = smoothed_y * pixels_to_meter_scale

    # -----------------------------------------------------
    # 7. Velocity
    # -----------------------------------------------------

    velocity_y = np.gradient(
        com_y_metric,
        dt
    )

    velocity_y = _moving_average(
        velocity_y,
        3
    )

    # -----------------------------------------------------
    # 8. Acceleration
    # -----------------------------------------------------

    acceleration_y = np.gradient(
        velocity_y,
        dt
    )

    acceleration_y = _moving_average(
        acceleration_y,
        3
    )

    # MediaPipe image Y increases downward.
    #
    # Therefore:
    # downward image acceleration → negative physical acceleration
    #
    # Invert the sign to represent upward physical acceleration.
    vertical_acceleration = -acceleration_y

    # -----------------------------------------------------
    # 9. Force calculation
    # -----------------------------------------------------

    body_weight_n = weight_kg * GRAVITY

    force_n = (
        weight_kg *
        (GRAVITY + vertical_acceleration)
    )

    # Ground cannot provide negative vertical force.
    force_n = np.maximum(
        force_n,
        0.0
    )

    # -----------------------------------------------------
    # 10. Convert force to Body Weight
    # -----------------------------------------------------

    force_bw = force_n / body_weight_n

    # -----------------------------------------------------
    # 11. Remove unrealistic visual spikes
    # -----------------------------------------------------

    force_bw = np.clip(
        force_bw,
        MIN_FORCE_BW,
        MAX_FORCE_BW
    )

    force_n = force_bw * body_weight_n

    # -----------------------------------------------------
    # 12. Detect impact / loading events
    # -----------------------------------------------------

    # Impact is represented by force above approximately
    # 1.2 × bodyweight.
    #
    # This is a heuristic for video analysis, not a clinical
    # threshold.
    impact_threshold_bw = 1.20

    impact_mask = force_bw >= impact_threshold_bw

    # -----------------------------------------------------
    # 13. Identify impact regions
    # -----------------------------------------------------

    impact_regions = []

    start = None

    for i, active in enumerate(impact_mask):

        if active and start is None:
            start = i

        elif not active and start is not None:

            impact_regions.append(
                (start, i - 1)
            )

            start = None

    if start is not None:
        impact_regions.append(
            (start, len(impact_mask) - 1)
        )

    # Remove very short noise events.
    min_impact_frames = max(
        2,
        int(0.05 * fps)
    )

    impact_regions = [
        (s, e)
        for s, e in impact_regions
        if (e - s + 1) >= min_impact_frames
    ]

    # -----------------------------------------------------
    # 14. Peak force
    # -----------------------------------------------------

    peak_index = int(
        np.argmax(force_n)
    )

    peak_force_n = float(
        force_n[peak_index]
    )

    peak_force_bw = float(
        force_bw[peak_index]
    )

    # -----------------------------------------------------
    # 15. Average force
    # -----------------------------------------------------

    avg_force_n = float(
        np.mean(force_n)
    )

    # -----------------------------------------------------
    # 16. Peak acceleration
    # -----------------------------------------------------

    peak_acceleration = float(
        np.max(vertical_acceleration)
    )

    # -----------------------------------------------------
    # 17. Loading rate
    # -----------------------------------------------------

    loading_rate_n_s = 0.0

    if impact_regions:

        rates = []

        for start, end in impact_regions:

            segment_force = force_n[start:end + 1]

            if len(segment_force) < 2:
                continue

            local_peak = np.argmax(
                segment_force
            )

            peak_position = start + local_peak

            peak_force_local = force_n[
                peak_position
            ]

            force_start = force_n[start]

            elapsed = (
                peak_position - start
            ) * dt

            if elapsed > 0:

                rate = (
                    peak_force_local - force_start
                ) / elapsed

                rates.append(
                    max(0.0, rate)
                )

        if rates:
            loading_rate_n_s = float(
                max(rates)
            )

    # -----------------------------------------------------
    # 18. Impact duration
    # -----------------------------------------------------

    impact_duration_ms = None

    if impact_regions:

        longest_duration = max(
            (
                (end - start + 1) * dt
                for start, end in impact_regions
            ),
            default=0.0
        )

        impact_duration_ms = (
            longest_duration * 1000.0
        )

    # -----------------------------------------------------
    # 19. Impulse proxy
    # -----------------------------------------------------
    #
    # Integral of force over time.
    #
    # This is still only a visual approximation.
    # -----------------------------------------------------

    impulse_ns = float(
        np.trapezoid(
            force_n,
            dx=dt
        )
    )

    # -----------------------------------------------------
    # 20. Confidence estimation
    # -----------------------------------------------------

    total_points = len(com_y_series)

    visibility_ratio = (
        valid_count / total_points
        if total_points > 0
        else 0.0
    )

    confidence = (
        0.70 * visibility_ratio +
        0.30 * min(
            1.0,
            valid_count / 60.0
        )
    )

    confidence = float(
        np.clip(confidence, 0.0, 1.0)
    )

    # -----------------------------------------------------
    # 21. Force time series
    # -----------------------------------------------------

    force_series = [
        round(float(force), 1)
        for force in force_n
    ]

    force_bw_series = [
        round(float(bw), 3)
        for bw in force_bw
    ]

    acceleration_series = [
        round(float(a), 3)
        for a in vertical_acceleration
    ]

    velocity_series = [
        round(float(v), 3)
        for v in velocity_y
    ]

    # -----------------------------------------------------
    # 22. Final result
    # -----------------------------------------------------

    return {

        "label":
            "Estimated Force / Visual Proxy",

        "status":
            "success",

        "disclaimer":
            (
                "Force values are estimated from video-derived "
                "center-of-mass kinematics using athlete profile "
                "height and weight. They are visual proxies and "
                "are not equivalent to force-plate or laboratory "
                "biomechanical measurements."
            ),

        # Athlete profile
        "athlete_height_cm":
            round(height_cm, 2),

        "estimated_body_mass_kg":
            round(weight_kg, 2),

        "body_weight_n":
            round(body_weight_n, 1),

        # Main force metrics
        "peak_force_n":
            round(peak_force_n, 1),

        "peak_force_bw":
            round(peak_force_bw, 2),

        "avg_force_n":
            round(avg_force_n, 1),

        # Loading characteristics
        "loading_rate_n_s":
            round(loading_rate_n_s, 1),

        "impact_duration_ms":
            (
                round(impact_duration_ms, 1)
                if impact_duration_ms is not None
                else None
            ),

        "impulse_ns":
            round(impulse_ns, 2),

        # Impact information
        "impact_count":
            len(impact_regions),

        "peak_acceleration_ms2":
            round(peak_acceleration, 3),

        # Quality
        "confidence":
            round(confidence, 3),

        # Time-series data
        "time_series_force":
            force_series,

        "time_series_force_bw":
            force_bw_series,

        "time_series_vertical_acceleration":
            acceleration_series,

        "time_series_vertical_velocity":
            velocity_series,

        # Peak location
        "peak_force_frame":
            peak_index,

        "peak_force_time_s":
            round(
                peak_index * dt,
                3
            )
    }