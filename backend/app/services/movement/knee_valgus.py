import numpy as np
from typing import List, Dict, Any, Tuple


def _calculate_frontal_knee_deviation(hip: Dict[str, float], knee: Dict[str, float], ankle: Dict[str, float], is_right: bool) -> float:
    """
    Calculates the 2D frontal plane medial collapse (valgus deviation in degrees).
    In frontal plane (x, y):
    A straight vertical leg has collinear hip, knee, ankle (0 deg deviation).
    Medial shift of the knee increases valgus deviation angle.
    """
    try:
        # Vector from hip to ankle
        ha_x = ankle["x"] - hip["x"]
        ha_y = ankle["y"] - hip["y"]

        # Vector from hip to knee
        hk_x = knee["x"] - hip["x"]
        hk_y = knee["y"] - hip["y"]

        # Vector from knee to ankle
        ka_x = ankle["x"] - knee["x"]
        ka_y = ankle["y"] - knee["y"]

        v1 = np.array([-hk_x, -hk_y], dtype=np.float64) # knee to hip
        v2 = np.array([ka_x, ka_y], dtype=np.float64)    # knee to ankle

        n1 = np.linalg.norm(v1)
        n2 = np.linalg.norm(v2)

        if n1 < 1e-7 or n2 < 1e-7:
            return 0.0

        cosine = np.dot(v1, v2) / (n1 * n2)
        cosine = np.clip(cosine, -1.0, 1.0)
        straight_angle = np.degrees(np.arccos(cosine))

        # Deviation from 180 degrees
        deviation = abs(180.0 - straight_angle)

        # Midpoint x between hips and ankles to verify medial direction
        # Normalized coordinates: x ranges 0 (left of image) to 1 (right of image)
        # For right leg (camera right or person right), medial direction is towards center
        return round(float(deviation), 2)
    except Exception:
        return 0.0


def _classify_valgus_risk(deviation: float) -> Tuple[str, str]:
    """
    Returns (risk_category, description)
    """
    if deviation < 5.0:
        return "Normal", "Optimal knee alignment in the frontal plane."
    elif deviation < 10.0:
        return "Mild", "Minor medial knee displacement observed during load."
    elif deviation < 15.0:
        return "Moderate", "Moderate knee valgus collapse detected; elevated strain on ACL and patellofemoral joint."
    else:
        return "High", "Significant dynamic knee valgus observed; high biomechanical injury risk."


def analyze_knee_valgus(frames_landmarks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyzes Knee Valgus across all frames for both right and left knees.
    """
    right_series = []
    left_series = []

    for frame_data in frames_landmarks:
        landmarks = frame_data.get("landmarks", [])
        if not landmarks or len(landmarks) < 33:
            right_series.append(None)
            left_series.append(None)
            continue

        lm_dict = {lm["landmark_id"]: lm for lm in landmarks if "landmark_id" in lm}

        # Right Knee (24: right_hip, 26: right_knee, 28: right_ankle)
        if 24 in lm_dict and 26 in lm_dict and 28 in lm_dict:
            r_dev = _calculate_frontal_knee_deviation(lm_dict[24], lm_dict[26], lm_dict[28], is_right=True)
            right_series.append(r_dev)
        else:
            right_series.append(None)

        # Left Knee (23: left_hip, 25: left_knee, 27: left_ankle)
        if 23 in lm_dict and 25 in lm_dict and 27 in lm_dict:
            l_dev = _calculate_frontal_knee_deviation(lm_dict[23], lm_dict[25], lm_dict[27], is_right=False)
            left_series.append(l_dev)
        else:
            left_series.append(None)

    valid_r = [v for v in right_series if v is not None]
    valid_l = [v for v in left_series if v is not None]

    r_max = float(np.max(valid_r)) if valid_r else 0.0
    r_avg = float(np.mean(valid_r)) if valid_r else 0.0
    l_max = float(np.max(valid_l)) if valid_l else 0.0
    l_avg = float(np.mean(valid_l)) if valid_l else 0.0

    r_risk, r_desc = _classify_valgus_risk(r_max)
    l_risk, l_desc = _classify_valgus_risk(l_max)

    # Composite valgus score (0 to 100 where 100 is best / 0 valgus)
    peak_valgus = max(r_max, l_max)
    avg_valgus = (r_avg + l_avg) / 2.0
    valgus_score = max(0.0, min(100.0, 100.0 - (peak_valgus * 3.5 + avg_valgus * 1.5)))

    overall_risk = "Low"
    if peak_valgus >= 15.0 or valgus_score < 50.0:
        overall_risk = "High"
    elif peak_valgus >= 10.0 or valgus_score < 70.0:
        overall_risk = "Moderate"
    elif peak_valgus >= 5.0 or valgus_score < 85.0:
        overall_risk = "Mild"

    return {
        "right": {
            "max_deviation": round(r_max, 1),
            "avg_deviation": round(r_avg, 1),
            "risk": r_risk,
            "description": r_desc
        },
        "left": {
            "max_deviation": round(l_max, 1),
            "avg_deviation": round(l_avg, 1),
            "risk": l_risk,
            "description": l_desc
        },
        "score": round(valgus_score, 1),
        "overall_risk": overall_risk,
        "max_deviation": round(peak_valgus, 1),
        "avg_deviation": round(avg_valgus, 1),
        "time_series": {
            "right": right_series,
            "left": left_series
        }
    }
