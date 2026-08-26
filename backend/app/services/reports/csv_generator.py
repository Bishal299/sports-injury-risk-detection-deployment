import os
import csv
from typing import Dict, Any, List


def generate_csv_report(
    output_csv_path: str,
    joint_data: Dict[str, Any],
    valgus_data: Dict[str, Any],
    hip_data: Dict[str, Any],
    trunk_data: Dict[str, Any],
    balance_data: Dict[str, Any],
    force_data: Dict[str, Any]
) -> str:
    """
    Generates a downloadable CSV containing frame-by-frame kinematics and time-series data.
    """
    os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)

    timeline = joint_data.get("timeline", [])
    joint_ts = joint_data.get("time_series", {})
    valgus_ts = valgus_data.get("time_series", {})
    hip_ts = hip_data.get("time_series", {})
    trunk_ts = trunk_data.get("time_series", {})
    balance_ts = balance_data.get("time_series", {})
    force_ts = force_data.get("time_series_force", [])

    fieldnames = [
        "frame",
        "timestamp_sec",
        "right_knee_angle",
        "left_knee_angle",
        "right_hip_angle",
        "left_hip_angle",
        "right_ankle_angle",
        "left_ankle_angle",
        "right_shoulder_angle",
        "left_shoulder_angle",
        "right_elbow_angle",
        "left_elbow_angle",
        "right_knee_valgus_deg",
        "left_knee_valgus_deg",
        "pelvic_tilt_deg",
        "trunk_lean_deg",
        "lateral_trunk_lean_deg",
        "com_x",
        "com_y",
        "estimated_force_n"
    ]

    with open(output_csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for idx, t_sec in enumerate(timeline):
            row = {
                "frame": idx,
                "timestamp_sec": t_sec,
                "right_knee_angle": joint_ts.get("right_knee", [None])[idx] if idx < len(joint_ts.get("right_knee", [])) else None,
                "left_knee_angle": joint_ts.get("left_knee", [None])[idx] if idx < len(joint_ts.get("left_knee", [])) else None,
                "right_hip_angle": joint_ts.get("right_hip", [None])[idx] if idx < len(joint_ts.get("right_hip", [])) else None,
                "left_hip_angle": joint_ts.get("left_hip", [None])[idx] if idx < len(joint_ts.get("left_hip", [])) else None,
                "right_ankle_angle": joint_ts.get("right_ankle", [None])[idx] if idx < len(joint_ts.get("right_ankle", [])) else None,
                "left_ankle_angle": joint_ts.get("left_ankle", [None])[idx] if idx < len(joint_ts.get("left_ankle", [])) else None,
                "right_shoulder_angle": joint_ts.get("right_shoulder", [None])[idx] if idx < len(joint_ts.get("right_shoulder", [])) else None,
                "left_shoulder_angle": joint_ts.get("left_shoulder", [None])[idx] if idx < len(joint_ts.get("left_shoulder", [])) else None,
                "right_elbow_angle": joint_ts.get("right_elbow", [None])[idx] if idx < len(joint_ts.get("right_elbow", [])) else None,
                "left_elbow_angle": joint_ts.get("left_elbow", [None])[idx] if idx < len(joint_ts.get("left_elbow", [])) else None,
                "right_knee_valgus_deg": valgus_ts.get("right", [None])[idx] if idx < len(valgus_ts.get("right", [])) else None,
                "left_knee_valgus_deg": valgus_ts.get("left", [None])[idx] if idx < len(valgus_ts.get("left", [])) else None,
                "pelvic_tilt_deg": hip_ts.get("pelvic_tilt", [None])[idx] if idx < len(hip_ts.get("pelvic_tilt", [])) else None,
                "trunk_lean_deg": trunk_ts.get("lean", [None])[idx] if idx < len(trunk_ts.get("lean", [])) else None,
                "lateral_trunk_lean_deg": trunk_ts.get("lateral_lean", [None])[idx] if idx < len(trunk_ts.get("lateral_lean", [])) else None,
                "com_x": balance_ts.get("com_x", [None])[idx] if idx < len(balance_ts.get("com_x", [])) else None,
                "com_y": balance_ts.get("com_y", [None])[idx] if idx < len(balance_ts.get("com_y", [])) else None,
                "estimated_force_n": force_ts[idx] if idx < len(force_ts) else None
            }
            writer.writerow(row)

    return output_csv_path
