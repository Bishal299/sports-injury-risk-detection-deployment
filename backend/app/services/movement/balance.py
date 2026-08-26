import numpy as np
from typing import List, Dict, Any


def analyze_balance(frames_landmarks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyzes static and dynamic balance using Center of Mass (COM) proxy and Base of Support (BOS).
    """
    com_x_series = []
    com_y_series = []
    bos_width_series = []

    for frame_data in frames_landmarks:
        landmarks = frame_data.get("landmarks", [])
        if not landmarks or len(landmarks) < 33:
            com_x_series.append(None)
            com_y_series.append(None)
            bos_width_series.append(None)
            continue
 
        lm_dict = {lm["landmark_id"]: lm for lm in landmarks if "landmark_id" in lm}

        # Key body segment landmarks
        # Head (0), Shoulders (11, 12), Hips (23, 24), Knees (25, 26), Ankles (27, 28)
        req = [0, 11, 12, 23, 24, 25, 26, 27, 28]
        if all(k in lm_dict for k in req):
            head_x = lm_dict[0]["x"]
            head_y = lm_dict[0]["y"]

            sh_x = (lm_dict[11]["x"] + lm_dict[12]["x"]) / 2.0
            sh_y = (lm_dict[11]["y"] + lm_dict[12]["y"]) / 2.0

            hip_x = (lm_dict[23]["x"] + lm_dict[24]["x"]) / 2.0
            hip_y = (lm_dict[23]["y"] + lm_dict[24]["y"]) / 2.0

            knee_x = (lm_dict[25]["x"] + lm_dict[26]["x"]) / 2.0
            knee_y = (lm_dict[25]["y"] + lm_dict[26]["y"]) / 2.0

            ank_x = (lm_dict[27]["x"] + lm_dict[28]["x"]) / 2.0
            ank_y = (lm_dict[27]["y"] + lm_dict[28]["y"]) / 2.0

            # Biomechanical segmental mass weights (Dempster body segment parameters)
            # Head/Neck ~ 8%, Trunk ~ 48%, Thighs ~ 20%, Calves/Feet ~ 24%
            com_x = (0.08 * head_x) + (0.48 * sh_x * 0.5 + 0.48 * hip_x * 0.5) + (0.24 * hip_x) + (0.12 * knee_x) + (0.08 * ank_x)
            com_y = (0.08 * head_y) + (0.24 * sh_y) + (0.36 * hip_y) + (0.20 * knee_y) + (0.12 * ank_y)

            # Base of Support (BOS): distance between left and right feet/ankles
            bos_width = abs(lm_dict[28]["x"] - lm_dict[27]["x"])

            com_x_series.append(round(float(com_x), 4))
            com_y_series.append(round(float(com_y), 4))
            bos_width_series.append(round(float(bos_width), 4))
        else:
            com_x_series.append(None)
            com_y_series.append(None)
            bos_width_series.append(None)

    valid_com_x = [x for x in com_x_series if x is not None]
    valid_com_y = [y for y in com_y_series if y is not None]
    valid_bos = [b for b in bos_width_series if b is not None]

    if valid_com_x:
        lat_sway_std = float(np.std(valid_com_x))
        lat_sway_range = float(np.max(valid_com_x) - np.min(valid_com_x))
        ap_sway_std = float(np.std(valid_com_y))
    else:
        lat_sway_std = lat_sway_range = ap_sway_std = 0.0

    avg_bos = float(np.mean(valid_bos)) if valid_bos else 0.15

    # Balance Score (0-100)
    # Lower sway variance indicates higher postural stability
    sway_penalty = (lat_sway_std * 500.0) + (lat_sway_range * 100.0) + (ap_sway_std * 300.0)
    balance_score = max(0.0, min(100.0, 100.0 - sway_penalty))

    return {
        "score": round(balance_score, 1),
        "lateral_sway_std": round(lat_sway_std, 4),
        "lateral_sway_range": round(lat_sway_range, 4),
        "ap_sway_std": round(ap_sway_std, 4),
        "avg_base_of_support": round(avg_bos, 3),
        "time_series": {
            "com_x": com_x_series,
            "com_y": com_y_series
        }
    }
