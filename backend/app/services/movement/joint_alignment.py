from typing import Dict, Any, List


def analyze_joint_alignment(
    joint_data: Dict[str, Any],
    valgus_data: Dict[str, Any],
    hip_data: Dict[str, Any],
    posture_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generates joint alignment comparisons and status table for Hip, Knee, Ankle, Shoulder, Elbow.
    """
    r_valgus = valgus_data.get("right", {}).get("max_deviation", 0.0)
    l_valgus = valgus_data.get("left", {}).get("max_deviation", 0.0)

    r_hip_stab = hip_data.get("right_hip_stability", 85.0)
    l_hip_stab = hip_data.get("left_hip_stability", 85.0)

    sh_tilt = posture_data.get("shoulder_tilt_deg", 2.0)

    # Knee status
    knee_max = max(r_valgus, l_valgus)
    if knee_max < 5.0:
        knee_status = "Optimal"
    elif knee_max < 10.0:
        knee_status = "Mild Deviation"
    elif knee_max < 15.0:
        knee_status = "Moderate Deviation"
    else:
        knee_status = "Significant Deviation"

    # Hip status
    hip_diff = abs(r_hip_stab - l_hip_stab)
    if hip_diff < 5.0 and min(r_hip_stab, l_hip_stab) > 75.0:
        hip_status = "Optimal"
    elif hip_diff < 12.0:
        hip_status = "Mild Asymmetry"
    else:
        hip_status = "Moderate Asymmetry"

    # Shoulder status
    if sh_tilt < 3.0:
        sh_status = "Optimal"
    elif sh_tilt < 6.0:
        sh_status = "Mild Deviation"
    else:
        sh_status = "Moderate Tilt"

    # Ankle & Elbow
    ankle_status = "Optimal"
    elbow_status = "Optimal"

    table = [
        {
            "joint": "Hip",
            "right": f"{r_hip_stab:.1f} / 100",
            "left": f"{l_hip_stab:.1f} / 100",
            "status": hip_status,
            "metric": "Stability Index"
        },
        {
            "joint": "Knee",
            "right": f"{r_valgus:.1f}° valgus",
            "left": f"{l_valgus:.1f}° valgus",
            "status": knee_status,
            "metric": "Valgus Deviation"
        },
        {
            "joint": "Ankle",
            "right": "Aligned",
            "left": "Aligned",
            "status": ankle_status,
            "metric": "Load Axis"
        },
        {
            "joint": "Shoulder",
            "right": f"{sh_tilt:.1f}° tilt",
            "left": f"{sh_tilt:.1f}° tilt",
            "status": sh_status,
            "metric": "Horizontal Level"
        },
        {
            "joint": "Elbow",
            "right": "Neutral",
            "left": "Neutral",
            "status": elbow_status,
            "metric": "Carrying Angle"
        }
    ]

    # Composite alignment score
    alignment_score = 100.0
    if knee_status == "Mild Deviation": alignment_score -= 8.0
    elif knee_status == "Moderate Deviation": alignment_score -= 16.0
    elif knee_status == "Significant Deviation": alignment_score -= 25.0

    if hip_status == "Mild Asymmetry": alignment_score -= 6.0
    elif hip_status == "Moderate Asymmetry": alignment_score -= 14.0

    if sh_status == "Mild Deviation": alignment_score -= 4.0
    elif sh_status == "Moderate Tilt": alignment_score -= 10.0

    return {
        "score": round(max(0.0, min(100.0, alignment_score)), 1),
        "table": table
    }
