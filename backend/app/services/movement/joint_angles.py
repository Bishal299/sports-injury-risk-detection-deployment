import numpy as np
from typing import List, Dict, Any, Optional


def calculate_3pt_angle(p1: Dict[str, float], p2: Dict[str, float], p3: Dict[str, float], use_3d: bool = True) -> Optional[float]:
    """
    Calculate the interior angle at p2 formed by points p1, p2, p3 in degrees.
    """
    try:
        if use_3d and "z" in p1 and "z" in p2 and "z" in p3:
            v1 = np.array([p1["x"] - p2["x"], p1["y"] - p2["y"], p1["z"] - p2["z"]], dtype=np.float64)
            v2 = np.array([p3["x"] - p2["x"], p3["y"] - p2["y"], p3["z"] - p2["z"]], dtype=np.float64)
        else:
            v1 = np.array([p1["x"] - p2["x"], p1["y"] - p2["y"]], dtype=np.float64)
            v2 = np.array([p3["x"] - p2["x"], p3["y"] - p2["y"]], dtype=np.float64)

        norm_v1 = np.linalg.norm(v1)
        norm_v2 = np.linalg.norm(v2)

        if norm_v1 < 1e-7 or norm_v2 < 1e-7:
            return None

        cosine = np.dot(v1, v2) / (norm_v1 * norm_v2)
        cosine = np.clip(cosine, -1.0, 1.0)
        angle = float(np.degrees(np.arccos(cosine)))
        return round(angle, 2)
    except Exception:
        return None


def calculate_joint_angles(frames_landmarks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculates time-series and summary metrics for lower and upper body joint angles.
    
    Landmark Indices (MediaPipe):
    11: left_shoulder,  12: right_shoulder
    13: left_elbow,     14: right_elbow
    15: left_wrist,     16: right_wrist
    23: left_hip,       24: right_hip
    25: left_knee,      26: right_knee
    27: left_ankle,     28: right_ankle
    31: left_foot_index,32: right_foot_index
    """
    joint_series = {
        "right_knee": [],
        "left_knee": [],
        "right_hip": [],
        "left_hip": [],
        "right_ankle": [],
        "left_ankle": [],
        "right_shoulder": [],
        "left_shoulder": [],
        "right_elbow": [],
        "left_elbow": [],
    }

    timeline = []

    for frame_data in frames_landmarks:
        frame_num = frame_data["frame_number"]
        timestamp_ms = frame_data["timestamp_ms"]
        time_sec = round(timestamp_ms / 1000.0, 3)
        timeline.append(time_sec)

        landmarks = frame_data.get("landmarks", [])
        if not landmarks or len(landmarks) < 33:
            for k in joint_series:
                joint_series[k].append(None)
            continue

        lm_dict = {lm["landmark_id"]: lm for lm in landmarks if "landmark_id" in lm}

        # Right Knee (24 -> 26 -> 28)
        rk = calculate_3pt_angle(lm_dict.get(24, {}), lm_dict.get(26, {}), lm_dict.get(28, {})) if 24 in lm_dict and 26 in lm_dict and 28 in lm_dict else None
        joint_series["right_knee"].append(rk)

        # Left Knee (23 -> 25 -> 27)
        lk = calculate_3pt_angle(lm_dict.get(23, {}), lm_dict.get(25, {}), lm_dict.get(27, {})) if 23 in lm_dict and 25 in lm_dict and 27 in lm_dict else None
        joint_series["left_knee"].append(lk)

        # Right Hip (12 -> 24 -> 26)
        rh = calculate_3pt_angle(lm_dict.get(12, {}), lm_dict.get(24, {}), lm_dict.get(26, {})) if 12 in lm_dict and 24 in lm_dict and 26 in lm_dict else None
        joint_series["right_hip"].append(rh)

        # Left Hip (11 -> 23 -> 25)
        lh = calculate_3pt_angle(lm_dict.get(11, {}), lm_dict.get(23, {}), lm_dict.get(25, {})) if 11 in lm_dict and 23 in lm_dict and 25 in lm_dict else None
        joint_series["left_hip"].append(lh)

        # Right Ankle (26 -> 28 -> 32)
        ra = calculate_3pt_angle(lm_dict.get(26, {}), lm_dict.get(28, {}), lm_dict.get(32, {})) if 26 in lm_dict and 28 in lm_dict and 32 in lm_dict else None
        joint_series["right_ankle"].append(ra)

        # Left Ankle (25 -> 27 -> 31)
        la = calculate_3pt_angle(lm_dict.get(25, {}), lm_dict.get(27, {}), lm_dict.get(31, {})) if 25 in lm_dict and 27 in lm_dict and 31 in lm_dict else None
        joint_series["left_ankle"].append(la)

        # Right Shoulder (24 -> 12 -> 14)
        rs = calculate_3pt_angle(lm_dict.get(24, {}), lm_dict.get(12, {}), lm_dict.get(14, {})) if 24 in lm_dict and 12 in lm_dict and 14 in lm_dict else None
        joint_series["right_shoulder"].append(rs)

        # Left Shoulder (23 -> 11 -> 13)
        ls = calculate_3pt_angle(lm_dict.get(23, {}), lm_dict.get(11, {}), lm_dict.get(13, {})) if 23 in lm_dict and 11 in lm_dict and 13 in lm_dict else None
        joint_series["left_shoulder"].append(ls)

        # Right Elbow (12 -> 14 -> 16)
        re = calculate_3pt_angle(lm_dict.get(12, {}), lm_dict.get(14, {}), lm_dict.get(16, {})) if 12 in lm_dict and 14 in lm_dict and 16 in lm_dict else None
        joint_series["right_elbow"].append(re)

        # Left Elbow (11 -> 13 -> 15)
        le = calculate_3pt_angle(lm_dict.get(11, {}), lm_dict.get(13, {}), lm_dict.get(15, {})) if 11 in lm_dict and 13 in lm_dict and 15 in lm_dict else None
        joint_series["left_elbow"].append(le)

    # Compute summary statistics & ROM
    summary = {}
    for joint_name, values in joint_series.items():
        valid_vals = [v for v in values if v is not None]
        if valid_vals:
            min_val = float(np.min(valid_vals))
            max_val = float(np.max(valid_vals))
            avg_val = float(np.mean(valid_vals))
            current_val = float(valid_vals[-1])
            rom = float(max_val - min_val)
        else:
            min_val = max_val = avg_val = current_val = rom = 0.0

        summary[joint_name] = {
            "current_angle": round(current_val, 1),
            "min_angle": round(min_val, 1),
            "max_angle": round(max_val, 1),
            "avg_angle": round(avg_val, 1),
            "rom": round(rom, 1)
        }

    return {
        "timeline": timeline,
        "time_series": joint_series,
        "summary": summary
    }
