from typing import Dict, Any, List


def analyze_symmetry(
    joint_data: Dict[str, Any],
    valgus_data: Dict[str, Any],
    hip_data: Dict[str, Any],
    stride_data: Dict[str, Any],
    balance_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Computes bilateral movement symmetry comparing right-side vs left-side metrics.
    Provides an overall symmetry score and transparent contributing measurement breakdowns.
    """
    summary = joint_data.get("summary", {})

    # 1. Knee ROM Symmetry
    r_knee_rom = summary.get("right_knee", {}).get("rom", 0.0)
    l_knee_rom = summary.get("left_knee", {}).get("rom", 0.0)
    max_k_rom = max(r_knee_rom, l_knee_rom, 1.0)
    knee_rom_sym = max(0.0, 100.0 - (abs(r_knee_rom - l_knee_rom) / max_k_rom) * 100.0)

    # 2. Hip ROM Symmetry
    r_hip_rom = summary.get("right_hip", {}).get("rom", 0.0)
    l_hip_rom = summary.get("left_hip", {}).get("rom", 0.0)
    max_h_rom = max(r_hip_rom, l_hip_rom, 1.0)
    hip_rom_sym = max(0.0, 100.0 - (abs(r_hip_rom - l_hip_rom) / max_h_rom) * 100.0)

    # 3. Shoulder ROM Symmetry
    r_sh_rom = summary.get("right_shoulder", {}).get("rom", 0.0)
    l_sh_rom = summary.get("left_shoulder", {}).get("rom", 0.0)
    max_s_rom = max(r_sh_rom, l_sh_rom, 1.0)
    shoulder_rom_sym = max(0.0, 100.0 - (abs(r_sh_rom - l_sh_rom) / max_s_rom) * 100.0)

    # 4. Knee Valgus Symmetry
    r_valgus = valgus_data.get("right", {}).get("max_deviation", 0.0)
    l_valgus = valgus_data.get("left", {}).get("max_deviation", 0.0)
    valgus_diff = abs(r_valgus - l_valgus)
    valgus_sym = max(0.0, 100.0 - valgus_diff * 4.0)

    # 5. Hip Stability Symmetry
    hip_sym = hip_data.get("symmetry_score", 90.0)

    # 6. Stride Symmetry
    stride_asym = stride_data.get("stride_asymmetry_pct", 5.0)
    stride_sym = max(0.0, 100.0 - stride_asym)

    # Breakdown components
    factors = [
        {
            "metric": "Knee Range of Motion",
            "right_value": f"{r_knee_rom:.1f}°",
            "left_value": f"{l_knee_rom:.1f}°",
            "symmetry_score": round(knee_rom_sym, 1),
            "weight": "25%"
        },
        {
            "metric": "Hip Range of Motion",
            "right_value": f"{r_hip_rom:.1f}°",
            "left_value": f"{l_hip_rom:.1f}°",
            "symmetry_score": round(hip_rom_sym, 1),
            "weight": "20%"
        },
        {
            "metric": "Knee Alignment / Valgus",
            "right_value": f"{r_valgus:.1f}°",
            "left_value": f"{l_valgus:.1f}°",
            "symmetry_score": round(valgus_sym, 1),
            "weight": "20%"
        },
        {
            "metric": "Hip & Pelvic Stability",
            "right_value": f"{hip_data.get('right_hip_stability', 85):.1f}",
            "left_value": f"{hip_data.get('left_hip_stability', 85):.1f}",
            "symmetry_score": round(hip_sym, 1),
            "weight": "15%"
        },
        {
            "metric": "Stride Kinematics",
            "right_value": f"{stride_data.get('right_normalized_stride', 0.5):.2f}",
            "left_value": f"{stride_data.get('left_normalized_stride', 0.5):.2f}",
            "symmetry_score": round(stride_sym, 1),
            "weight": "10%"
        },
        {
            "metric": "Upper Body / Shoulder ROM",
            "right_value": f"{r_sh_rom:.1f}°",
            "left_value": f"{l_sh_rom:.1f}°",
            "symmetry_score": round(shoulder_rom_sym, 1),
            "weight": "10%"
        }
    ]

    overall_symmetry = (
        knee_rom_sym * 0.25 +
        hip_rom_sym * 0.20 +
        valgus_sym * 0.20 +
        hip_sym * 0.15 +
        stride_sym * 0.10 +
        shoulder_rom_sym * 0.10
    )

    return {
        "overall_symmetry_score": round(max(0.0, min(100.0, overall_symmetry)), 1),
        "factors": factors
    }
