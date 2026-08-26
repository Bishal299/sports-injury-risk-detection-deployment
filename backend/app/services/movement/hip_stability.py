import numpy as np
from typing import List, Dict, Any


def analyze_hip_stability(frames_landmarks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyzes hip and pelvic stability across movement.
    Calculates pelvic tilt angle (degrees from horizontal) and pelvic displacement.
    """
    tilt_series = []
    midpoint_y_series = []
    midpoint_x_series = []

    for frame_data in frames_landmarks:
        landmarks = frame_data.get("landmarks", [])
        if not landmarks or len(landmarks) < 33:
            tilt_series.append(None)
            midpoint_y_series.append(None)
            midpoint_x_series.append(None)
            continue

        lm_dict = {lm["landmark_id"]: lm for lm in landmarks if "landmark_id" in lm}

        if 23 in lm_dict and 24 in lm_dict:
            lh = lm_dict[23]
            rh = lm_dict[24]

            dx = rh["x"] - lh["x"]
            dy = rh["y"] - lh["y"]

            # Pelvic tilt in degrees
            tilt = np.degrees(np.arctan2(dy, dx if abs(dx) > 1e-6 else 1e-6))
            tilt_series.append(round(float(tilt), 2))

            mid_x = (lh["x"] + rh["x"]) / 2.0
            mid_y = (lh["y"] + rh["y"]) / 2.0
            midpoint_x_series.append(round(float(mid_x), 4))
            midpoint_y_series.append(round(float(mid_y), 4))
        else:
            tilt_series.append(None)
            midpoint_y_series.append(None)
            midpoint_x_series.append(None)

    valid_tilts = [abs(t) for t in tilt_series if t is not None]
    valid_ys = [y for y in midpoint_y_series if y is not None]
    valid_xs = [x for x in midpoint_x_series if x is not None]

    if valid_tilts:
        avg_tilt = float(np.mean(valid_tilts))
        max_tilt = float(np.max(valid_tilts))
        tilt_std = float(np.std(valid_tilts))
    else:
        avg_tilt = max_tilt = tilt_std = 0.0

    if valid_ys:
        y_range = float(np.max(valid_ys) - np.min(valid_ys))
    else:
        y_range = 0.0

    # Right vs Left tilt distribution (pelvic drop on right vs left)
    raw_tilts = [t for t in tilt_series if t is not None]
    right_drops = [abs(t) for t in raw_tilts if t > 0]
    left_drops = [abs(t) for t in raw_tilts if t < 0]

    r_mean_drop = float(np.mean(right_drops)) if right_drops else 0.0
    l_mean_drop = float(np.mean(left_drops)) if left_drops else 0.0

    # Hip stability score (0-100)
    # A stable pelvis has low mean tilt and low tilt variance
    penalty = (avg_tilt * 4.0) + (tilt_std * 6.0) + (max_tilt * 1.5)
    hip_stability_score = max(0.0, min(100.0, 100.0 - penalty))

    # Right & Left specific stability scores
    r_stability = max(0.0, min(100.0, 100.0 - (r_mean_drop * 6.0 + avg_tilt * 2.0)))
    l_stability = max(0.0, min(100.0, 100.0 - (l_mean_drop * 6.0 + avg_tilt * 2.0)))

    # Hip symmetry score
    if max(r_stability, l_stability) > 0:
        symmetry_score = 100.0 - (abs(r_stability - l_stability) / max(r_stability, l_stability)) * 100.0
    else:
        symmetry_score = 100.0

    return {
        "score": round(hip_stability_score, 1),
        "right_hip_stability": round(r_stability, 1),
        "left_hip_stability": round(l_stability, 1),
        "avg_pelvic_tilt_deg": round(avg_tilt, 1),
        "max_pelvic_tilt_deg": round(max_tilt, 1),
        "tilt_variation_std": round(tilt_std, 2),
        "pelvic_displacement_range": round(y_range, 3),
        "symmetry_score": round(max(0.0, min(100.0, symmetry_score)), 1),
        "time_series": {
            "pelvic_tilt": tilt_series,
            "midpoint_y": midpoint_y_series
        }
    }
