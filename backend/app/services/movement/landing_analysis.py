import numpy as np
from typing import List, Dict, Any, Optional


def analyze_landing_mechanics(frames_landmarks: List[Dict[str, Any]], joint_data: Dict[str, Any], valgus_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyzes landing and impact deceleration events.
    Evaluates knee flexion absorption, hip flexion absorption, trunk control, and alignment during impact.
    If no impact or jump event is found, returns 'Insufficient visual data'.
    """
    if not frames_landmarks or len(frames_landmarks) < 10:
        return {
            "has_landing_data": False,
            "status": "Insufficient visual data",
            "score": None,
            "submetrics": {
                "knee_absorption": "Insufficient visual data",
                "hip_absorption": "Insufficient visual data",
                "trunk_control": "Insufficient visual data",
                "alignment": "Insufficient visual data",
                "balance": "Insufficient visual data"
            }
        }

    # Extract vertical hip trajectory to find landing deceleration dip
    hip_y_series = []
    for frame_data in frames_landmarks:
        landmarks = frame_data.get("landmarks", [])
        if landmarks and len(landmarks) >= 33:
            lm_dict = {lm["landmark_id"]: lm for lm in landmarks if "landmark_id" in lm}
            if 23 in lm_dict and 24 in lm_dict:
                hip_y = (lm_dict[23]["y"] + lm_dict[24]["y"]) / 2.0
                hip_y_series.append(hip_y)
            else:
                hip_y_series.append(None)
        else:
            hip_y_series.append(None)

    # Calculate vertical velocity
    valid_indices = [i for i, y in enumerate(hip_y_series) if y is not None]
    if len(valid_indices) < 10:
        return {
            "has_landing_data": False,
            "status": "Insufficient visual data",
            "score": None,
            "submetrics": {
                "knee_absorption": "Insufficient visual data",
                "hip_absorption": "Insufficient visual data",
                "trunk_control": "Insufficient visual data",
                "alignment": "Insufficient visual data",
                "balance": "Insufficient visual data"
            }
        }

    # Detect significant vertical displacement indicating a jump or landing impact
    ys = [hip_y_series[i] for i in valid_indices]
    y_range = max(ys) - min(ys)

    # If the vertical variation is small (e.g. static standing or pure upper body movement), mark as insufficient landing data
    if y_range < 0.08:
        return {
            "has_landing_data": False,
            "status": "Insufficient visual data (No high-impact landing event detected)",
            "score": None,
            "submetrics": {
                "knee_absorption": "Insufficient visual data",
                "hip_absorption": "Insufficient visual data",
                "trunk_control": "Insufficient visual data",
                "alignment": "Insufficient visual data",
                "balance": "Insufficient visual data"
            }
        }

    # Find the frame of lowest hip point (maximum ground compression / flexion)
    max_y_idx = valid_indices[int(np.argmax(ys))]

    # Get knee angles around impact
    r_knees = joint_data.get("time_series", {}).get("right_knee", [])
    l_knees = joint_data.get("time_series", {}).get("left_knee", [])
    
    impact_r_knee = r_knees[max_y_idx] if max_y_idx < len(r_knees) and r_knees[max_y_idx] is not None else 130.0
    impact_l_knee = l_knees[max_y_idx] if max_y_idx < len(l_knees) and l_knees[max_y_idx] is not None else 130.0
    avg_impact_knee_angle = (impact_r_knee + impact_l_knee) / 2.0

    # Deep knee flexion (> 60 deg flexion, meaning knee angle < 120) absorbs force better than stiff landing (> 150)
    # Knee score: 100 at 90 deg, down to 30 at 170 deg (stiff landing)
    knee_score = max(20.0, min(100.0, 100.0 - max(0.0, avg_impact_knee_angle - 90.0) * 1.3))

    # Hip absorption
    r_hips = joint_data.get("time_series", {}).get("right_hip", [])
    l_hips = joint_data.get("time_series", {}).get("left_hip", [])
    impact_r_hip = r_hips[max_y_idx] if max_y_idx < len(r_hips) and r_hips[max_y_idx] is not None else 140.0
    impact_l_hip = l_hips[max_y_idx] if max_y_idx < len(l_hips) and l_hips[max_y_idx] is not None else 140.0
    avg_impact_hip_angle = (impact_r_hip + impact_l_hip) / 2.0
    hip_score = max(20.0, min(100.0, 100.0 - max(0.0, avg_impact_hip_angle - 100.0) * 1.1))

    # Trunk control at landing
    trunk_score = max(40.0, min(100.0, 100.0 - (valgus_data.get("max_deviation", 0.0) * 2.0)))

    # Knee alignment at landing
    valgus_dev = valgus_data.get("max_deviation", 0.0)
    align_score = max(20.0, min(100.0, 100.0 - valgus_dev * 4.0))

    # Balance score at landing
    balance_subscore = round((knee_score + hip_score) / 2.0, 1)

    overall_landing_score = round(
        knee_score * 0.35 +
        hip_score * 0.25 +
        trunk_score * 0.15 +
        align_score * 0.25,
        1
    )

    return {
        "has_landing_data": True,
        "status": "Landing event analyzed",
        "score": overall_landing_score,
        "impact_frame": max_y_idx,
        "knee_flexion_deg": round(180.0 - avg_impact_knee_angle, 1),
        "hip_flexion_deg": round(180.0 - avg_impact_hip_angle, 1),
        "submetrics": {
            "knee_absorption": f"{round(knee_score, 1)} / 100",
            "hip_absorption": f"{round(hip_score, 1)} / 100",
            "trunk_control": f"{round(trunk_score, 1)} / 100",
            "alignment": f"{round(align_score, 1)} / 100",
            "balance": f"{round(balance_subscore, 1)} / 100"
        }
    }
