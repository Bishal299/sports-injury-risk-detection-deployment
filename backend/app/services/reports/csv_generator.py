import os
import csv
import numpy as np
from io import StringIO
from typing import Dict, Any, List, Optional


FRAME_LEVEL_COLUMNS = [
    # Metadata
    "video_id",
    "athlete_id",
    "sport",
    "activity",
    "height_cm",
    "weight_kg",
    "fps",
    "feature_version",
    # Frame / Timestamp
    "frame",
    "timestamp_sec",
    # Validity
    "pose_valid",
    "left_leg_valid",
    "right_leg_valid",
    "trunk_valid",
    # Movement Phase
    "movement_phase",
    # Joint Angles
    "right_knee_angle_deg",
    "left_knee_angle_deg",
    "right_hip_angle_deg",
    "left_hip_angle_deg",
    "right_ankle_angle_deg",
    "left_ankle_angle_deg",
    "right_shoulder_angle_deg",
    "left_shoulder_angle_deg",
    "right_elbow_angle_deg",
    "left_elbow_angle_deg",
    # Knee Valgus
    "right_knee_valgus_deg",
    "left_knee_valgus_deg",
    # Hip / Pelvis
    "pelvic_tilt_deg",
    "pelvic_midpoint_y_norm",
    # Trunk
    "trunk_lean_deg",
    "lateral_trunk_lean_deg",
    # Landing Mechanics
    "landing_phase",
    "landing_knee_flexion_deg",
    "landing_hip_flexion_deg",
    # Stride
    "stride_length",
    "stride_velocity",
    "stride_asymmetry_pct",
    # Balance
    "com_x_norm",
    "com_y_norm",
    "base_of_support_width_norm",
    # Force
    "force_proxy_N",
    "force_proxy_BW",
]


def _format_val(val: Any, decimals: Optional[int] = None) -> Any:
    """Format numeric values safely without converting None/NaN to 0."""
    if val is None:
        return ""
    try:
        if isinstance(val, (int, np.integer)):
            return int(val)
        f_val = float(val)
        if not np.isfinite(f_val):
            return ""
        if decimals is not None:
            return round(f_val, decimals)
        return f_val
    except (TypeError, ValueError):
        return str(val) if val != "" else ""


def _safe_get_ts(ts_dict: Dict[str, Any], key: str, idx: int, decimals: Optional[int] = None) -> Any:
    """Safely retrieves a time-series element at idx."""
    if not isinstance(ts_dict, dict):
        return ""
    series = ts_dict.get(key)
    if not series or not isinstance(series, list) or idx >= len(series):
        return ""
    return _format_val(series[idx], decimals=decimals)


def generate_csv_report(
    output_csv_path: str,
    joint_data: Dict[str, Any],
    valgus_data: Dict[str, Any],
    hip_data: Dict[str, Any],
    trunk_data: Dict[str, Any],
    balance_data: Dict[str, Any],
    stride_data: Optional[Dict[str, Any]] = None,
    landing_data: Optional[Dict[str, Any]] = None,
    force_data: Optional[Dict[str, Any]] = None,
    frames_landmarks: Optional[List[Dict[str, Any]]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generates a clean, structured time-series CSV dataset containing real frame-by-frame
    biomechanical kinematics for future ML training.

    Preserves actual frame number and timestamps, segment validity flags,
    movement phases, angles, valgus deviations, hip stability, trunk lean,
    stride separation, balance COM, and force estimation proxies.
    Never fills missing/invalid values with 0.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_csv_path)), exist_ok=True)

    metadata = metadata or {}
    timeline = joint_data.get("timeline", [])
    total_frames = len(timeline)

    # If timeline is empty but frames_landmarks is available, infer total_frames
    if total_frames == 0 and frames_landmarks:
        total_frames = len(frames_landmarks)
        fps = float(metadata.get("fps", 30.0))
        timeline = [round(i / max(fps, 1e-4), 3) for i in range(total_frames)]

    joint_ts = joint_data.get("time_series", {})
    valgus_ts = valgus_data.get("time_series", {})
    hip_ts = hip_data.get("time_series", {})
    trunk_ts = trunk_data.get("time_series", {})
    balance_ts = balance_data.get("time_series", {})
    stride_ts = stride_data.get("time_series", {}) if stride_data else {}
    force_ts_n = force_data.get("time_series_force", []) if force_data else []
    force_ts_bw = force_data.get("time_series_force_bw", []) if force_data else []

    # Landing window check
    landing_window = landing_data.get("landing_window", {}) if landing_data else {}
    landing_start = landing_window.get("start_frame") if isinstance(landing_window, dict) else None
    landing_end = landing_window.get("end_frame") if isinstance(landing_window, dict) else None

    # Metadata fields
    video_id_str = str(metadata.get("video_id", ""))
    athlete_id_str = str(metadata.get("athlete_id", ""))
    sport_str = str(metadata.get("sport", "") or "")
    activity_str = str(metadata.get("activity", "") or "")
    height_val = _format_val(metadata.get("height_cm"), decimals=1)
    weight_val = _format_val(metadata.get("weight_kg"), decimals=1)
    fps_val = _format_val(metadata.get("fps"), decimals=2)
    version_str = str(metadata.get("feature_version", "1.0-biomechanics"))

    with open(output_csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FRAME_LEVEL_COLUMNS)
        writer.writeheader()

        for idx in range(total_frames):
            t_sec = timeline[idx] if idx < len(timeline) else (round(idx / float(metadata.get("fps", 30.0)), 3))

            # Retrieve validity information from frames_landmarks if available
            frame_entry = frames_landmarks[idx] if (frames_landmarks and idx < len(frames_landmarks)) else {}
            validity = frame_entry.get("validity", {})
            actual_frame_idx = frame_entry.get("frame_number", idx)

            pose_valid_str = "TRUE" if validity.get("pose_valid") else ("FALSE" if "pose_valid" in validity else "")
            left_leg_valid_str = "TRUE" if validity.get("left_leg_valid") else ("FALSE" if "left_leg_valid" in validity else "")
            right_leg_valid_str = "TRUE" if validity.get("right_leg_valid") else ("FALSE" if "right_leg_valid" in validity else "")
            trunk_valid_str = "TRUE" if validity.get("trunk_valid") else ("FALSE" if "trunk_valid" in validity else "")

            # Movement & Landing phase
            in_landing = False
            if landing_start is not None and landing_end is not None:
                if landing_start <= actual_frame_idx <= landing_end:
                    in_landing = True

            landing_phase_str = "landing" if in_landing else ""
            movement_phase_str = "landing" if in_landing else ""

            # Pelvic midpoint y norm (check normalized_midpoint_y then midpoint_y)
            pelvic_y = _safe_get_ts(hip_ts, "normalized_midpoint_y", idx, decimals=5)
            if pelvic_y == "":
                pelvic_y = _safe_get_ts(hip_ts, "midpoint_y", idx, decimals=5)

            # Force values
            f_n = ""
            if idx < len(force_ts_n):
                f_n = _format_val(force_ts_n[idx], decimals=1)

            f_bw = ""
            if idx < len(force_ts_bw):
                f_bw = _format_val(force_ts_bw[idx], decimals=3)

            # Landing flexion (if frame is in landing window, compute instantaneous knee flexion from 180 - angle)
            rk_angle = _safe_get_ts(joint_ts, "right_knee", idx, decimals=2)
            rh_angle = _safe_get_ts(joint_ts, "right_hip", idx, decimals=2)
            landing_knee_flex = ""
            landing_hip_flex = ""
            if in_landing:
                if rk_angle != "":
                    try:
                        landing_knee_flex = round(180.0 - float(rk_angle), 2)
                    except ValueError:
                        pass
                if rh_angle != "":
                    try:
                        landing_hip_flex = round(180.0 - float(rh_angle), 2)
                    except ValueError:
                        pass

            row = {
                # Metadata
                "video_id": video_id_str,
                "athlete_id": athlete_id_str,
                "sport": sport_str,
                "activity": activity_str,
                "height_cm": height_val,
                "weight_kg": weight_val,
                "fps": fps_val,
                "feature_version": version_str,
                # Frame / Timestamp
                "frame": actual_frame_idx,
                "timestamp_sec": round(float(t_sec), 3) if t_sec != "" else "",
                # Validity
                "pose_valid": pose_valid_str,
                "left_leg_valid": left_leg_valid_str,
                "right_leg_valid": right_leg_valid_str,
                "trunk_valid": trunk_valid_str,
                # Movement Phase
                "movement_phase": movement_phase_str,
                # Joint Angles
                "right_knee_angle_deg": _safe_get_ts(joint_ts, "right_knee", idx, decimals=2),
                "left_knee_angle_deg": _safe_get_ts(joint_ts, "left_knee", idx, decimals=2),
                "right_hip_angle_deg": _safe_get_ts(joint_ts, "right_hip", idx, decimals=2),
                "left_hip_angle_deg": _safe_get_ts(joint_ts, "left_hip", idx, decimals=2),
                "right_ankle_angle_deg": _safe_get_ts(joint_ts, "right_ankle", idx, decimals=2),
                "left_ankle_angle_deg": _safe_get_ts(joint_ts, "left_ankle", idx, decimals=2),
                "right_shoulder_angle_deg": _safe_get_ts(joint_ts, "right_shoulder", idx, decimals=2),
                "left_shoulder_angle_deg": _safe_get_ts(joint_ts, "left_shoulder", idx, decimals=2),
                "right_elbow_angle_deg": _safe_get_ts(joint_ts, "right_elbow", idx, decimals=2),
                "left_elbow_angle_deg": _safe_get_ts(joint_ts, "left_elbow", idx, decimals=2),
                # Knee Valgus
                "right_knee_valgus_deg": _safe_get_ts(valgus_ts, "right", idx, decimals=4),
                "left_knee_valgus_deg": _safe_get_ts(valgus_ts, "left", idx, decimals=4),
                # Hip / Pelvis
                "pelvic_tilt_deg": _safe_get_ts(hip_ts, "pelvic_tilt", idx, decimals=3),
                "pelvic_midpoint_y_norm": pelvic_y,
                # Trunk
                "trunk_lean_deg": _safe_get_ts(trunk_ts, "lean", idx, decimals=2),
                "lateral_trunk_lean_deg": _safe_get_ts(trunk_ts, "lateral_lean", idx, decimals=2),
                # Landing Mechanics
                "landing_phase": landing_phase_str,
                "landing_knee_flexion_deg": landing_knee_flex,
                "landing_hip_flexion_deg": landing_hip_flex,
                # Stride
                "stride_length": _safe_get_ts(stride_ts, "stride_separation", idx, decimals=4),
                "stride_velocity": "",
                "stride_asymmetry_pct": "",
                # Balance
                "com_x_norm": _safe_get_ts(balance_ts, "com_x", idx, decimals=4),
                "com_y_norm": _safe_get_ts(balance_ts, "com_y", idx, decimals=4),
                "base_of_support_width_norm": _safe_get_ts(balance_ts, "bos_width", idx, decimals=4),
                # Force
                "force_proxy_N": f_n,
                "force_proxy_BW": f_bw,
            }
            writer.writerow(row)

    return output_csv_path


def generate_recovery_summary_csv(
    athlete_profile: Dict[str, Any],
    risk_monitoring: Dict[str, Any],
    rehabilitation_plan: Optional[Any] = None,
    movement_comparison: Optional[Dict[str, Any]] = None,
    notes: Optional[List[Any]] = None,
    physiotherapist_info: Optional[Dict[str, Any]] = None,
    rehabilitation_monitoring: Optional[Dict[str, Any]] = None,
    initial_analysis: Optional[Dict[str, Any]] = None,
    latest_analysis: Optional[Dict[str, Any]] = None,
    risk_history: Optional[List[Dict[str, Any]]] = None,
    timeline: Optional[List[Dict[str, Any]]] = None,
) -> bytes:
    def display(value: Any) -> Any:
        return value if value not in (None, "") else "Not Available"

    def analysis_score(analysis: Dict[str, Any]) -> Any:
        score = analysis.get("composite_risk_score")
        return score if score is not None else analysis.get("overall_risk_score")

    buffer = StringIO()
    writer = csv.writer(buffer)
    physiotherapist_info = physiotherapist_info or {}
    rehabilitation_monitoring = rehabilitation_monitoring or {}
    risk_history = risk_history or []
    timeline = timeline or []

    writer.writerow(["Section", "Field", "Value"])
    writer.writerow(["Athlete", "Name", athlete_profile.get("name") or "Not Available"])
    writer.writerow(["Athlete", "Sport", athlete_profile.get("sport") or "Not Available"])
    writer.writerow(["Athlete", "Age", athlete_profile.get("age") if athlete_profile.get("age") is not None else "Not Available"])
    writer.writerow(["Physiotherapist", "Name", physiotherapist_info.get("name") or "Not Available"])
    writer.writerow(["Physiotherapist", "Email", physiotherapist_info.get("email") or "Not Available"])
    writer.writerow(["Physiotherapist", "Organization", physiotherapist_info.get("organization") or "Not Available"])
    writer.writerow(["Physiotherapist", "Specialization", physiotherapist_info.get("specialization") or "Not Available"])
    writer.writerow(["Risk", "Current Risk", risk_monitoring.get("current_risk") if risk_monitoring.get("current_risk") is not None else "Not Available"])
    writer.writerow(["Risk", "Risk Category", risk_monitoring.get("risk_category") or "Not Available"])
    writer.writerow(["Risk", "Previous Risk", risk_monitoring.get("previous_risk") if risk_monitoring.get("previous_risk") is not None else "No Previous Assessment"])
    writer.writerow(["Risk", "Risk Trend", risk_monitoring.get("risk_trend") or "Not Available"])

    if rehabilitation_plan:
        writer.writerow(["Rehabilitation", "Context", rehabilitation_plan.injury_context or "Not Available"])
        writer.writerow(["Rehabilitation", "Progress", rehabilitation_plan.progress if rehabilitation_plan.progress is not None else "Not Available"])
        writer.writerow(["Rehabilitation", "Phase", rehabilitation_plan.current_phase or "Not Available"])
        writer.writerow(["Rehabilitation", "Status", rehabilitation_plan.status or "Not Available"])
        writer.writerow(["Rehabilitation", "Goals", ", ".join(rehabilitation_plan.goals) if rehabilitation_plan.goals else "Not Available"])
        writer.writerow(["Rehabilitation", "Recent Assessment", rehabilitation_plan.recent_assessment or "Not Available"])
    else:
        writer.writerow(["Rehabilitation", "Plan", "No Rehabilitation Plan"])

    writer.writerow(["Progress", "Activity Completion", f"{rehabilitation_monitoring.get('completed_activity_count', 0)}/{rehabilitation_monitoring.get('activity_count', 0)}"])
    writer.writerow(["Progress", "Calculated Progress", rehabilitation_monitoring.get("calculated_progress") if rehabilitation_monitoring.get("progress_available") else "Not Available"])
    writer.writerow(["Progress", "Pending Activities", display(rehabilitation_monitoring.get("pending_activity_count"))])
    writer.writerow(["Progress", "Recent Activity", display((rehabilitation_monitoring.get("recent_rehabilitation_activity") or {}).get("title"))])
    writer.writerow(["Progress", "Next Review", display(rehabilitation_monitoring.get("next_review_date"))])

    for label, analysis in (("Initial Analysis", initial_analysis), ("Latest Analysis", latest_analysis)):
        analysis = analysis or {}
        writer.writerow([label, "Date", display(analysis.get("completed_at") or analysis.get("analysis_date"))])
        writer.writerow([label, "Risk Score", display(analysis_score(analysis))])
        writer.writerow([label, "Risk Category", display(analysis.get("risk_category"))])
        writer.writerow([label, "Knee Valgus", display(analysis.get("knee_valgus"))])
        writer.writerow([label, "Hip Stability", display(analysis.get("hip_stability"))])
        writer.writerow([label, "Trunk Lean", display(analysis.get("trunk_lean"))])
        writer.writerow([label, "Stride", display(analysis.get("stride_length"))])
        writer.writerow([label, "Symmetry", display(analysis.get("symmetry_score"))])
        writer.writerow([label, "Movement Quality", display(analysis.get("movement_quality"))])

    movement_comparison = movement_comparison or {}
    writer.writerow([
        "Movement",
        "Comparison Status",
        movement_comparison.get("comparison_status") or "Not Available",
    ])
    for metric, values in (movement_comparison.get("comparison") or {}).items():
        writer.writerow(["Movement", f"{metric} Initial", values.get("initial")])
        writer.writerow(["Movement", f"{metric} Latest", values.get("latest")])
        writer.writerow(["Movement", f"{metric} Change", values.get("change")])

    if risk_history:
        for item in risk_history:
            writer.writerow(["Risk History", display(item.get("date")), f"{display(item.get('risk_score'))} / {display(item.get('risk_category'))}"])
    else:
        writer.writerow(["Risk History", "Data", "Not Available"])

    if timeline:
        for event in timeline:
            writer.writerow(["Timeline", display(event.get("title")), display(event.get("date"))])
    else:
        writer.writerow(["Timeline", "Events", "Not Available"])

    for note in notes or []:
        writer.writerow(["Physiotherapist Note", note.title or str(note.note_id), note.note])
    if not notes:
        writer.writerow(["Physiotherapist Note", "Notes", "Not Available"])

    return buffer.getvalue().encode("utf-8")
