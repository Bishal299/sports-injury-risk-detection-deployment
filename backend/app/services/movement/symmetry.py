from typing import Dict, Any


def analyze_symmetry(
    joint_data: Dict[str, Any],
    valgus_data: Dict[str, Any],
    hip_data: Dict[str, Any],
    stride_data: Dict[str, Any],
    balance_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Computes bilateral movement symmetry comparing right-side vs left-side metrics.
    Only compares parameters where both right and left measurements are reliably available.
    Does NOT invent fabricated symmetry values.
    """
    summary = joint_data.get("summary", {})
    factors = []
    weighted_scores = []
    total_weight = 0.0

    # 1. Knee ROM Symmetry
    r_k_stats = summary.get("right_knee", {})
    l_k_stats = summary.get("left_knee", {})
    r_knee_rom = r_k_stats.get("rom")
    l_knee_rom = l_k_stats.get("rom")

    if r_knee_rom is not None and l_knee_rom is not None and max(r_knee_rom, l_knee_rom) > 1.0:
        max_k = max(r_knee_rom, l_knee_rom)
        k_diff = abs(r_knee_rom - l_knee_rom)
        knee_rom_sym = max(0.0, 100.0 - (k_diff / max_k) * 100.0)
        knee_ratio = min(r_knee_rom, l_knee_rom) / max_k
        factors.append({
            "metric": "Knee Range of Motion",
            "right_value": f"{r_knee_rom:.1f}°",
            "left_value": f"{l_knee_rom:.1f}°",
            "absolute_diff": round(k_diff, 1),
            "ratio": round(knee_ratio, 3),
            "symmetry_score": round(knee_rom_sym, 1),
            "weight": "25%"
        })
        weighted_scores.append(knee_rom_sym * 0.25)
        total_weight += 0.25

    # 2. Hip ROM Symmetry
    r_h_stats = summary.get("right_hip", {})
    l_h_stats = summary.get("left_hip", {})
    r_hip_rom = r_h_stats.get("rom")
    l_hip_rom = l_h_stats.get("rom")

    if r_hip_rom is not None and l_hip_rom is not None and max(r_hip_rom, l_hip_rom) > 1.0:
        max_h = max(r_hip_rom, l_hip_rom)
        h_diff = abs(r_hip_rom - l_hip_rom)
        hip_rom_sym = max(0.0, 100.0 - (h_diff / max_h) * 100.0)
        hip_ratio = min(r_hip_rom, l_hip_rom) / max_h
        factors.append({
            "metric": "Hip Range of Motion",
            "right_value": f"{r_hip_rom:.1f}°",
            "left_value": f"{l_hip_rom:.1f}°",
            "absolute_diff": round(h_diff, 1),
            "ratio": round(hip_ratio, 3),
            "symmetry_score": round(hip_rom_sym, 1),
            "weight": "20%"
        })
        weighted_scores.append(hip_rom_sym * 0.20)
        total_weight += 0.20

    # 3. Shoulder ROM Symmetry
    r_s_stats = summary.get("right_shoulder", {})
    l_s_stats = summary.get("left_shoulder", {})
    r_sh_rom = r_s_stats.get("rom")
    l_sh_rom = l_s_stats.get("rom")

    if r_sh_rom is not None and l_sh_rom is not None and max(r_sh_rom, l_sh_rom) > 1.0:
        max_s = max(r_sh_rom, l_sh_rom)
        s_diff = abs(r_sh_rom - l_sh_rom)
        sh_rom_sym = max(0.0, 100.0 - (s_diff / max_s) * 100.0)
        sh_ratio = min(r_sh_rom, l_sh_rom) / max_s
        factors.append({
            "metric": "Shoulder Range of Motion",
            "right_value": f"{r_sh_rom:.1f}°",
            "left_value": f"{l_sh_rom:.1f}°",
            "absolute_diff": round(s_diff, 1),
            "ratio": round(sh_ratio, 3),
            "symmetry_score": round(sh_rom_sym, 1),
            "weight": "15%"
        })
        weighted_scores.append(sh_rom_sym * 0.15)
        total_weight += 0.15

    # 4. Knee Valgus Symmetry
    r_valgus = valgus_data.get("right", {}).get("max_deviation")
    l_valgus = valgus_data.get("left", {}).get("max_deviation")

    if r_valgus is not None and l_valgus is not None:
        v_diff = abs(r_valgus - l_valgus)
        valgus_sym = max(0.0, 100.0 - v_diff * 4.0)
        factors.append({
            "metric": "Knee Alignment / Valgus Deviation",
            "right_value": f"{r_valgus:.1f}°",
            "left_value": f"{l_valgus:.1f}°",
            "absolute_diff": round(v_diff, 1),
            "ratio": round(min(r_valgus, l_valgus) / max(r_valgus, l_valgus, 1e-4), 3),
            "symmetry_score": round(valgus_sym, 1),
            "weight": "20%"
        })
        weighted_scores.append(valgus_sym * 0.20)
        total_weight += 0.20

    # 5. Stride Symmetry
    r_stride = stride_data.get("right_normalized_stride")
    l_stride = stride_data.get("left_normalized_stride")

    if r_stride is not None and l_stride is not None and max(r_stride, l_stride) > 0.01:
        max_st = max(r_stride, l_stride)
        st_diff = abs(r_stride - l_stride)
        st_sym = max(0.0, 100.0 - (st_diff / max_st) * 100.0)
        factors.append({
            "metric": "Stride Kinematics",
            "right_value": f"{r_stride:.2f}",
            "left_value": f"{l_stride:.2f}",
            "absolute_diff": round(st_diff, 3),
            "ratio": round(min(r_stride, l_stride) / max_st, 3),
            "symmetry_score": round(st_sym, 1),
            "weight": "15%"
        })
        weighted_scores.append(st_sym * 0.15)
        total_weight += 0.15

    # Overall Symmetry Score
    if total_weight > 0:
        overall_sym = sum(weighted_scores) / total_weight
        overall_sym = round(float(max(0.0, min(100.0, overall_sym))), 1)
    else:
        overall_sym = None

    return {
        "overall_symmetry_score": overall_sym,
        "factors": factors
    }
