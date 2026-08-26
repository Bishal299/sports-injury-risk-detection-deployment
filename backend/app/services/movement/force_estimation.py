import numpy as np
from typing import Dict, Any, List, Optional


def estimate_visual_forces(
    balance_data: Dict[str, Any],
    fps: float = 30.0,
    athlete_weight_kg: Optional[float] = 70.0
) -> Dict[str, Any]:
    """
    Computes visual proxy force estimation based on 2D body kinematics and center-of-mass acceleration.
    Clearly labeled with non-medical estimation disclaimers.
    """
    weight_kg = athlete_weight_kg if athlete_weight_kg and athlete_weight_kg > 20.0 else 70.0
    gravity = 9.81  # m/s^2

    com_y_series = balance_data.get("time_series", {}).get("com_y", [])
    valid_ys = [y for y in com_y_series if y is not None]

    if len(valid_ys) < 6 or fps <= 0:
        return {
            "label": "Estimated Force / Visual Proxy",
            "disclaimer": "This is an estimation derived from video-based movement data and is not equivalent to force-plate measurement.",
            "estimated_body_mass_kg": weight_kg,
            "peak_force_n": round(weight_kg * gravity, 1),
            "peak_force_bw": 1.0,
            "avg_force_n": round(weight_kg * gravity, 1),
            "time_series_force": []
        }

    # Smooth COM y trajectory using a moving average window
    window = 3
    smoothed_y = np.convolve(valid_ys, np.ones(window)/window, mode='valid')

    # First derivative: velocity (pixels/norm units per sec)
    dt = 1.0 / fps
    vy = np.gradient(smoothed_y, dt)

    # Second derivative: acceleration
    ay = np.gradient(vy, dt)

    # Convert normalized vertical acceleration proxy to m/s^2 scale (assuming ~1.7m human height scale ~ 0.8 norm screen units)
    scale_factor = 1.7 / 0.8
    ay_metric = -ay * scale_factor  # invert y since image y points downwards

    # Ground reaction force proxy: F = m * (g + a)
    # Clamp negative values (cannot pull downwards on ground)
    forces_n = [max(0.0, weight_kg * (gravity + a_val)) for a_val in ay_metric]

    peak_force = float(np.max(forces_n)) if len(forces_n) > 0 else weight_kg * gravity
    avg_force = float(np.mean(forces_n)) if len(forces_n) > 0 else weight_kg * gravity
    peak_bw = peak_force / (weight_kg * gravity)

    # Map back to full length timeline with padding
    pad_left = (len(com_y_series) - len(forces_n)) // 2
    pad_right = len(com_y_series) - len(forces_n) - pad_left
    force_series = [None] * pad_left + [round(f, 1) for f in forces_n] + [None] * pad_right

    return {
        "label": "Estimated Force / Visual Proxy",
        "disclaimer": "This is an estimation derived from video-based movement data and is not equivalent to force-plate measurement.",
        "estimated_body_mass_kg": weight_kg,
        "peak_force_n": round(peak_force, 1),
        "peak_force_bw": round(peak_bw, 2),
        "avg_force_n": round(avg_force, 1),
        "time_series_force": force_series
    }
