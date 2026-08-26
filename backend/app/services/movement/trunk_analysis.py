import numpy as np
from typing import List, Dict, Any


def analyze_trunk_lean(frames_landmarks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyzes trunk/torso lean and orientation relative to the vertical axis.
    Midpoint of shoulders (11, 12) vs Midpoint of hips (23, 24).
    """
    lean_series = []
    lateral_lean_series = []

    for frame_data in frames_landmarks:
        landmarks = frame_data.get("landmarks", [])
        if not landmarks or len(landmarks) < 33:
            lean_series.append(None)
            lateral_lean_series.append(None)
            continue

        lm_dict = {lm["landmark_id"]: lm for lm in landmarks if "landmark_id" in lm}

        if 11 in lm_dict and 12 in lm_dict and 23 in lm_dict and 24 in lm_dict:
            shoulder_mid_x = (lm_dict[11]["x"] + lm_dict[12]["x"]) / 2.0
            shoulder_mid_y = (lm_dict[11]["y"] + lm_dict[12]["y"]) / 2.0

            hip_mid_x = (lm_dict[23]["x"] + lm_dict[24]["x"]) / 2.0
            hip_mid_y = (lm_dict[23]["y"] + lm_dict[24]["y"]) / 2.0

            dx = shoulder_mid_x - hip_mid_x
            dy = hip_mid_y - shoulder_mid_y  # In image coords, shoulder is above hip (smaller y)

            # Absolute inclination from vertical
            inclination = np.degrees(np.arctan2(abs(dx), max(dy, 1e-6)))
            lean_series.append(round(float(inclination), 2))

            # Signed lateral lean (negative = leaning left, positive = leaning right)
            signed_lean = np.degrees(np.arctan2(dx, max(dy, 1e-6)))
            lateral_lean_series.append(round(float(signed_lean), 2))
        else:
            lean_series.append(None)
            lateral_lean_series.append(None)

    valid_leans = [l for l in lean_series if l is not None]
    valid_signed = [s for s in lateral_lean_series if s is not None]

    if valid_leans:
        avg_lean = float(np.mean(valid_leans))
        max_lean = float(np.max(valid_leans))
        lean_std = float(np.std(valid_leans))
    else:
        avg_lean = max_lean = lean_std = 0.0

    # Directional lean tendency
    left_leans = [abs(s) for s in valid_signed if s < -1.5]
    right_leans = [abs(s) for s in valid_signed if s > 1.5]

    if len(left_leans) > len(right_leans) * 1.5:
        predominant_direction = "Left Lateral Lean"
    elif len(right_leans) > len(left_leans) * 1.5:
        predominant_direction = "Right Lateral Lean"
    else:
        predominant_direction = "Symmetric / Neutral"

    # Trunk score (0-100)
    # Excessive lean increases spinal and shear forces
    trunk_score = max(0.0, min(100.0, 100.0 - (avg_lean * 3.0 + (max_lean - 15.0 if max_lean > 15.0 else 0.0) * 2.0)))

    return {
        "score": round(trunk_score, 1),
        "avg_trunk_lean_deg": round(avg_lean, 1),
        "max_trunk_lean_deg": round(max_lean, 1),
        "lean_std_deg": round(lean_std, 2),
        "predominant_direction": predominant_direction,
        "time_series": {
            "lean": lean_series,
            "lateral_lean": lateral_lean_series
        }
    }
