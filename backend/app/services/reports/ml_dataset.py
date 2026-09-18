import os
import csv
import numpy as np
from typing import Dict, Any, List, Optional


ML_DATASET_COLUMNS = [
    # Metadata
    "video_id",
    "athlete_id",
    "sport",
    "activity",
    "height_cm",
    "weight_kg",
    "fps",
    "feature_version",
    # Data Quality Information
    "valid_frame_ratio",
    "total_frames",
    "analysis_duration_sec",
    # Knee
    "right_knee_angle_mean",
    "right_knee_angle_min",
    "right_knee_angle_max",
    "right_knee_angle_rom",
    "left_knee_angle_mean",
    "left_knee_angle_min",
    "left_knee_angle_max",
    "left_knee_angle_rom",
    "right_knee_valgus_mean",
    "right_knee_valgus_max",
    "left_knee_valgus_mean",
    "left_knee_valgus_max",
    # Hip / Pelvis
    "pelvic_tilt_mean",
    "pelvic_tilt_max",
    "pelvic_tilt_min",
    "pelvic_tilt_rom",
    # Trunk
    "trunk_lean_mean",
    "trunk_lean_max",
    "trunk_lean_rom",
    "lateral_trunk_lean_mean",
    "lateral_trunk_lean_max",
    # Stride
    "stride_length_mean",
    "stride_length_variability",
    "stride_asymmetry_pct",
    # Landing
    "landing_knee_flexion_mean",
    "landing_knee_flexion_min",
    "landing_knee_flexion_max",
    "landing_hip_flexion_mean",
    "landing_hip_flexion_min",
    "landing_hip_flexion_max",
    # Balance
    "com_x_mean",
    "com_x_std",
    "com_y_mean",
    "com_y_std",
    "base_of_support_width_mean",
    "base_of_support_width_std",
    # Force
    "force_proxy_N_mean",
    "force_proxy_N_max",
    "force_proxy_BW_mean",
    "force_proxy_BW_max",
    # Symmetry / Existing Scores
    "symmetry_score",
    "hip_stability_score",
    "landing_mechanics_score",
    "balance_score",
    "posture_score",
    "joint_alignment_score",
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


def _safe_mean(series: Optional[List[Any]], decimals: Optional[int] = None) -> Any:
    if not series:
        return ""
    valid = [float(v) for v in series if v is not None and np.isfinite(float(v))]
    if not valid:
        return ""
    m = float(np.mean(valid))
    return round(m, decimals) if decimals is not None else m


def _safe_std(series: Optional[List[Any]], decimals: Optional[int] = None) -> Any:
    if not series:
        return ""
    valid = [float(v) for v in series if v is not None and np.isfinite(float(v))]
    if len(valid) < 2:
        return ""
    s = float(np.std(valid))
    return round(s, decimals) if decimals is not None else s


def _safe_min(series: Optional[List[Any]], decimals: Optional[int] = None) -> Any:
    if not series:
        return ""
    valid = [float(v) for v in series if v is not None and np.isfinite(float(v))]
    if not valid:
        return ""
    m = float(np.min(valid))
    return round(m, decimals) if decimals is not None else m


def _safe_max(series: Optional[List[Any]], decimals: Optional[int] = None) -> Any:
    if not series:
        return ""
    valid = [float(v) for v in series if v is not None and np.isfinite(float(v))]
    if not valid:
        return ""
    m = float(np.max(valid))
    return round(m, decimals) if decimals is not None else m


def _safe_rom(series: Optional[List[Any]], decimals: Optional[int] = None) -> Any:
    if not series:
        return ""
    valid = [float(v) for v in series if v is not None and np.isfinite(float(v))]
    if len(valid) < 2:
        return ""
    r = float(np.max(valid) - np.min(valid))
    return round(r, decimals) if decimals is not None else r


def extract_ml_features(
    joint_data: Dict[str, Any],
    valgus_data: Dict[str, Any],
    hip_data: Dict[str, Any],
    trunk_data: Dict[str, Any],
    balance_data: Dict[str, Any],
    stride_data: Optional[Dict[str, Any]] = None,
    landing_data: Optional[Dict[str, Any]] = None,
    force_data: Optional[Dict[str, Any]] = None,
    posture_data: Optional[Dict[str, Any]] = None,
    alignment_data: Optional[Dict[str, Any]] = None,
    symmetry_data: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    feature_quality: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Extracts a clean, single-row dictionary of aggregated ML biomechanics features.
    Strictly avoids future information/data leakage and does not produce predictions.
    """
    metadata = metadata or {}
    feature_quality = feature_quality or {}

    joint_summary = joint_data.get("summary", {}) if isinstance(joint_data, dict) else {}
    joint_ts = joint_data.get("time_series", {}) if isinstance(joint_data, dict) else {}

    valgus_data = valgus_data or {}
    valgus_right = valgus_data.get("right", {}) if isinstance(valgus_data.get("right"), dict) else {}
    valgus_left = valgus_data.get("left", {}) if isinstance(valgus_data.get("left"), dict) else {}

    hip_data = hip_data or {}
    hip_ts = hip_data.get("time_series", {}) if isinstance(hip_data, dict) else {}

    trunk_data = trunk_data or {}
    trunk_ts = trunk_data.get("time_series", {}) if isinstance(trunk_data, dict) else {}

    stride_data = stride_data or {}
    stride_ts = stride_data.get("time_series", {}) if isinstance(stride_data, dict) else {}

    landing_data = landing_data or {}

    balance_data = balance_data or {}
    balance_ts = balance_data.get("time_series", {}) if isinstance(balance_data, dict) else {}

    force_data = force_data or {}

    posture_data = posture_data or {}
    alignment_data = alignment_data or {}
    symmetry_data = symmetry_data or {}

    # Total frames & quality
    total_frames = feature_quality.get("total_frames", len(joint_data.get("timeline", [])))
    valid_pose_frames = feature_quality.get("valid_pose_frames", total_frames)
    fps_val = float(metadata.get("fps", feature_quality.get("fps", 30.0)))
    duration_sec = feature_quality.get("duration_seconds")
    if duration_sec is None and total_frames > 0:
        duration_sec = round(total_frames / max(fps_val, 1e-4), 3)

    valid_ratio = round(valid_pose_frames / max(total_frames, 1), 3) if total_frames > 0 else 0.0

    # Knee Angles (Right / Left)
    r_k_sum = joint_summary.get("right_knee", {})
    l_k_sum = joint_summary.get("left_knee", {})

    rk_mean = _format_val(r_k_sum.get("avg_angle"), 2) or _safe_mean(joint_ts.get("right_knee"), 2)
    rk_min = _format_val(r_k_sum.get("min_angle"), 2) or _safe_min(joint_ts.get("right_knee"), 2)
    rk_max = _format_val(r_k_sum.get("max_angle"), 2) or _safe_max(joint_ts.get("right_knee"), 2)
    rk_rom = _format_val(r_k_sum.get("rom"), 2) or _safe_rom(joint_ts.get("right_knee"), 2)

    lk_mean = _format_val(l_k_sum.get("avg_angle"), 2) or _safe_mean(joint_ts.get("left_knee"), 2)
    lk_min = _format_val(l_k_sum.get("min_angle"), 2) or _safe_min(joint_ts.get("left_knee"), 2)
    lk_max = _format_val(l_k_sum.get("max_angle"), 2) or _safe_max(joint_ts.get("left_knee"), 2)
    lk_rom = _format_val(l_k_sum.get("rom"), 2) or _safe_rom(joint_ts.get("left_knee"), 2)

    # Knee Valgus
    rv_mean = _format_val(valgus_right.get("avg_normalized_valgus"), 4)
    rv_max = _format_val(valgus_right.get("peak_normalized_valgus"), 4)
    lv_mean = _format_val(valgus_left.get("avg_normalized_valgus"), 4)
    lv_max = _format_val(valgus_left.get("peak_normalized_valgus"), 4)

    # Pelvic Tilt
    pelvic_tilt_series = hip_ts.get("pelvic_tilt", [])
    pt_mean = _format_val(hip_data.get("mean_pelvic_tilt_deg"), 2) or _safe_mean(pelvic_tilt_series, 2)
    pt_max = _format_val(hip_data.get("max_pelvic_tilt_deg"), 2) or _safe_max(pelvic_tilt_series, 2)
    pt_min = _safe_min(pelvic_tilt_series, 2)
    pt_rom = _safe_rom(pelvic_tilt_series, 2)

    # Trunk Lean
    lean_series = trunk_ts.get("lean", [])
    lat_lean_series = trunk_ts.get("lateral_lean", [])
    tl_mean = _format_val(trunk_data.get("avg_trunk_lean_deg"), 2) or _safe_mean(lean_series, 2)
    tl_max = _format_val(trunk_data.get("max_trunk_lean_deg"), 2) or _safe_max(lean_series, 2)
    tl_rom = _safe_rom(lean_series, 2)
    tll_mean = _safe_mean(lat_lean_series, 2)
    tll_max = _safe_max([abs(v) for v in lat_lean_series if v is not None and np.isfinite(v)] if lat_lean_series else [], 2)

    # Stride
    stride_sep_series = stride_ts.get("stride_separation", [])
    stride_mean = _format_val(stride_data.get("normalized_stride_length"), 3) or _safe_mean(stride_sep_series, 3)
    stride_var = _safe_std(stride_sep_series, 4)
    stride_asym = _format_val(stride_data.get("stride_asymmetry_pct"), 2)

    # Landing
    landing_k_mean = _format_val(landing_data.get("knee_flexion_deg"), 2)
    landing_k_min = _format_val(landing_data.get("knee_flexion_min"), 2)
    landing_k_max = _format_val(landing_data.get("knee_flexion_max"), 2)
    landing_h_mean = _format_val(landing_data.get("hip_flexion_deg"), 2)
    landing_h_min = _format_val(landing_data.get("hip_flexion_min"), 2)
    landing_h_max = _format_val(landing_data.get("hip_flexion_max"), 2)

    # Balance
    com_x_series = balance_ts.get("com_x", [])
    com_y_series = balance_ts.get("com_y", [])
    bos_series = balance_ts.get("bos_width", [])

    com_x_mean = _safe_mean(com_x_series, 4)
    com_x_std = _format_val(balance_data.get("lateral_sway_std"), 4) or _safe_std(com_x_series, 4)
    com_y_mean = _safe_mean(com_y_series, 4)
    com_y_std = _format_val(balance_data.get("ap_sway_std"), 4) or _safe_std(com_y_series, 4)
    bos_mean = _format_val(balance_data.get("avg_base_of_support"), 4) or _safe_mean(bos_series, 4)
    bos_std = _safe_std(bos_series, 4)

    # Force
    force_n_mean = _format_val(force_data.get("avg_force_n"), 2) or _safe_mean(force_data.get("time_series_force"), 2)
    force_n_max = _format_val(force_data.get("peak_force_n"), 2) or _safe_max(force_data.get("time_series_force"), 2)
    force_bw_mean = _safe_mean(force_data.get("time_series_force_bw"), 3)
    force_bw_max = _format_val(force_data.get("peak_force_bw"), 2) or _safe_max(force_data.get("time_series_force_bw"), 3)

    # Scores
    sym_score = _format_val(symmetry_data.get("overall_symmetry_score"), 1)
    hip_score = _format_val(hip_data.get("score"), 1)
    landing_score = _format_val(landing_data.get("score"), 1)
    balance_score = _format_val(balance_data.get("score"), 1)
    posture_score = _format_val(posture_data.get("score"), 1)
    alignment_score = _format_val(alignment_data.get("score"), 1)

    return {
        # Metadata
        "video_id": str(metadata.get("video_id", "")),
        "athlete_id": str(metadata.get("athlete_id", "")),
        "sport": str(metadata.get("sport", "") or ""),
        "activity": str(metadata.get("activity", "") or ""),
        "height_cm": _format_val(metadata.get("height_cm"), 1),
        "weight_kg": _format_val(metadata.get("weight_kg"), 1),
        "fps": _format_val(fps_val, 2),
        "feature_version": str(metadata.get("feature_version", "1.0-biomechanics")),
        # Data Quality Information
        "valid_frame_ratio": valid_ratio,
        "total_frames": total_frames,
        "analysis_duration_sec": _format_val(duration_sec, 3),
        # Knee
        "right_knee_angle_mean": rk_mean,
        "right_knee_angle_min": rk_min,
        "right_knee_angle_max": rk_max,
        "right_knee_angle_rom": rk_rom,
        "left_knee_angle_mean": lk_mean,
        "left_knee_angle_min": lk_min,
        "left_knee_angle_max": lk_max,
        "left_knee_angle_rom": lk_rom,
        "right_knee_valgus_mean": rv_mean,
        "right_knee_valgus_max": rv_max,
        "left_knee_valgus_mean": lv_mean,
        "left_knee_valgus_max": lv_max,
        # Hip / Pelvis
        "pelvic_tilt_mean": pt_mean,
        "pelvic_tilt_max": pt_max,
        "pelvic_tilt_min": pt_min,
        "pelvic_tilt_rom": pt_rom,
        # Trunk
        "trunk_lean_mean": tl_mean,
        "trunk_lean_max": tl_max,
        "trunk_lean_rom": tl_rom,
        "lateral_trunk_lean_mean": tll_mean,
        "lateral_trunk_lean_max": tll_max,
        # Stride
        "stride_length_mean": stride_mean,
        "stride_length_variability": stride_var,
        "stride_asymmetry_pct": stride_asym,
        # Landing
        "landing_knee_flexion_mean": landing_k_mean,
        "landing_knee_flexion_min": landing_k_min,
        "landing_knee_flexion_max": landing_k_max,
        "landing_hip_flexion_mean": landing_h_mean,
        "landing_hip_flexion_min": landing_h_min,
        "landing_hip_flexion_max": landing_h_max,
        # Balance
        "com_x_mean": com_x_mean,
        "com_x_std": com_x_std,
        "com_y_mean": com_y_mean,
        "com_y_std": com_y_std,
        "base_of_support_width_mean": bos_mean,
        "base_of_support_width_std": bos_std,
        # Force
        "force_proxy_N_mean": force_n_mean,
        "force_proxy_N_max": force_n_max,
        "force_proxy_BW_mean": force_bw_mean,
        "force_proxy_BW_max": force_bw_max,
        # Symmetry / Existing Scores
        "symmetry_score": sym_score,
        "hip_stability_score": hip_score,
        "landing_mechanics_score": landing_score,
        "balance_score": balance_score,
        "posture_score": posture_score,
        "joint_alignment_score": alignment_score,
    }


def export_ml_dataset(
    output_ml_csv_path: str,
    joint_data: Dict[str, Any],
    valgus_data: Dict[str, Any],
    hip_data: Dict[str, Any],
    trunk_data: Dict[str, Any],
    balance_data: Dict[str, Any],
    stride_data: Optional[Dict[str, Any]] = None,
    landing_data: Optional[Dict[str, Any]] = None,
    force_data: Optional[Dict[str, Any]] = None,
    posture_data: Optional[Dict[str, Any]] = None,
    alignment_data: Optional[Dict[str, Any]] = None,
    symmetry_data: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    feature_quality: Optional[Dict[str, Any]] = None,
    master_ml_csv_path: Optional[str] = None
) -> str:
    """
    Exports a single-video ML feature row to output_ml_csv_path, and updates/appends
    it into the master_ml_csv_path ensuring exactly one row per video.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_ml_csv_path)), exist_ok=True)

    row = extract_ml_features(
        joint_data=joint_data,
        valgus_data=valgus_data,
        hip_data=hip_data,
        trunk_data=trunk_data,
        balance_data=balance_data,
        stride_data=stride_data,
        landing_data=landing_data,
        force_data=force_data,
        posture_data=posture_data,
        alignment_data=alignment_data,
        symmetry_data=symmetry_data,
        metadata=metadata,
        feature_quality=feature_quality
    )

    # 1. Write per-video ML dataset CSV (exactly 1 header + 1 row)
    with open(output_ml_csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=ML_DATASET_COLUMNS)
        writer.writeheader()
        writer.writerow(row)

    # 2. If master_ml_csv_path is specified, update or append without duplicates
    if master_ml_csv_path:
        os.makedirs(os.path.dirname(os.path.abspath(master_ml_csv_path)), exist_ok=True)
        video_id = row.get("video_id", "")
        existing_rows: List[Dict[str, Any]] = []

        if os.path.exists(master_ml_csv_path):
            try:
                with open(master_ml_csv_path, mode="r", newline="", encoding="utf-8") as mf:
                    reader = csv.DictReader(mf)
                    for r in reader:
                        # Keep rows not matching current video_id
                        if r.get("video_id") != video_id:
                            existing_rows.append(r)
            except Exception:
                existing_rows = []

        existing_rows.append(row)

        with open(master_ml_csv_path, mode="w", newline="", encoding="utf-8") as mf:
            writer = csv.DictWriter(mf, fieldnames=ML_DATASET_COLUMNS)
            writer.writeheader()
            for r in existing_rows:
                writer.writerow(r)

    return output_ml_csv_path
