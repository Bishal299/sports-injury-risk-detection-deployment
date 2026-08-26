import numpy as np
from typing import List, Dict, Any


def analyze_stride(frames_landmarks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyzes stride kinematics for walking, running, and locomotor movements.
    Uses ankle (27, 28) and heel (29, 30) positions normalized to estimated body height.
    """
    stride_separations = []
    r_forward_steps = []
    l_forward_steps = []
    body_heights = []

    for frame_data in frames_landmarks:
        landmarks = frame_data.get("landmarks", [])
        if not landmarks or len(landmarks) < 33:
            continue

        lm_dict = {lm["landmark_id"]: lm for lm in landmarks if "landmark_id" in lm}

        if 27 in lm_dict and 28 in lm_dict and 11 in lm_dict and 12 in lm_dict:
            l_ankle = lm_dict[27]
            r_ankle = lm_dict[28]

            # Approximate body height proxy (shoulder mid to ankle mid)
            sh_y = (lm_dict[11]["y"] + lm_dict[12]["y"]) / 2.0
            ank_y = (l_ankle["y"] + r_ankle["y"]) / 2.0
            height_proxy = max(0.1, abs(ank_y - sh_y))
            body_heights.append(height_proxy)

            # Euclidean separation between ankles
            sep_x = r_ankle["x"] - l_ankle["x"]
            sep_y = r_ankle["y"] - l_ankle["y"]
            sep = np.sqrt(sep_x**2 + sep_y**2)

            norm_sep = sep / height_proxy
            stride_separations.append(norm_sep)

            # Distinguish right forward vs left forward
            if r_ankle["x"] > l_ankle["x"]:
                r_forward_steps.append(norm_sep)
            else:
                l_forward_steps.append(norm_sep)

    if not stride_separations:
        return {
            "is_locomotion_detected": False,
            "normalized_stride_length": 0.0,
            "right_normalized_stride": 0.0,
            "left_normalized_stride": 0.0,
            "stride_asymmetry_pct": 0.0,
            "label": "Normalized Stride Length (No spatial calibration required)"
        }

    # Stride peaks
    r_stride_val = float(np.percentile(r_forward_steps, 90)) if r_forward_steps else float(np.mean(stride_separations))
    l_stride_val = float(np.percentile(l_forward_steps, 90)) if l_forward_steps else float(np.mean(stride_separations))
    avg_norm_stride = float(np.mean(stride_separations))
    peak_norm_stride = float(np.max(stride_separations))

    # Asymmetry
    max_step = max(r_stride_val, l_stride_val, 1e-5)
    asymmetry = (abs(r_stride_val - l_stride_val) / max_step) * 100.0

    return {
        "is_locomotion_detected": peak_norm_stride > 0.15,
        "normalized_stride_length": round(avg_norm_stride, 3),
        "peak_normalized_stride": round(peak_norm_stride, 3),
        "right_normalized_stride": round(r_stride_val, 3),
        "left_normalized_stride": round(l_stride_val, 3),
        "stride_asymmetry_pct": round(min(100.0, asymmetry), 1),
        "label": "Normalized Stride Length (Relative to torso-leg length)"
    }
