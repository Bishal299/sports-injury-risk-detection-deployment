"""
Unit & Integration Test Suite for Rule-Based Injury Risk Scoring Engine.

Validates:
  Case 1: Good movement -> Low Risk (< 25)
  Case 2: Moderate biomechanical deviations -> Moderate Risk (25-49)
  Case 3: Severe knee/hip/landing deviations -> High Risk (50-74)
  Case 4: Multiple severe deviations -> Critical Risk (75-100)
  Case 5: Missing historical data -> Historical Risk = 0, marked unavailable, not penalized
  Case 6: Missing training-load data -> Training Load Risk = 0, marked unavailable, not penalized
  Case 7: Fatigue -> Disabled (0% weight, None score)
  Case 8: Left/Right asymmetry -> Affected side identified correctly
  Case 9: No double counting of same underlying measurement
  Case 10: PDF report generation test with complete risk assessment
"""

import os
import sys
import tempfile
from typing import Dict, Any

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.risk_config import (
    WEIGHT_BIOMECHANICAL,
    WEIGHT_HISTORICAL,
    WEIGHT_ASYMMETRY,
    WEIGHT_TRAINING_LOAD,
    WEIGHT_FATIGUE,
    RISK_THRESHOLDS
)
from app.services.risk_scoring import calculate_injury_risk
from app.services.reports.pdf_generator import generate_pdf_report


def _make_features(
    r_valgus: float = 0.02,
    l_valgus: float = 0.02,
    hip_score: float = 92.0,
    trunk_score: float = 95.0,
    landing_score: float = 90.0,
    has_landing: bool = True,
    balance_score: float = 90.0,
    align_score: float = 92.0,
    posture_score: float = 90.0,
    symmetry_score: float = 94.0,
    stride_asym: float = 3.0,
    avg_trunk_lean: float = 3.0,
    predominant_dir: str = "Neutral"
) -> Dict[str, Any]:
    return {
        "knee_valgus": {
            "score": 95.0,
            "max_deviation": max(r_valgus, l_valgus),
            "right": {"peak_normalized_valgus": r_valgus, "max_deviation": r_valgus, "risk": "Normal"},
            "left": {"peak_normalized_valgus": l_valgus, "max_deviation": l_valgus, "risk": "Normal"}
        },
        "hip_stability": {
            "score": hip_score,
            "right_hip_stability": hip_score,
            "left_hip_stability": hip_score,
            "avg_pelvic_tilt_deg": 2.5,
            "pelvic_displacement_range": 0.08
        },
        "trunk_lean": {
            "score": trunk_score,
            "avg_trunk_lean_deg": avg_trunk_lean,
            "max_trunk_lean_deg": avg_trunk_lean + 2.0,
            "predominant_direction": predominant_dir
        },
        "landing": {
            "has_landing_data": has_landing,
            "score": landing_score,
            "status": "Landing event analyzed" if has_landing else "No impact",
            "knee_flexion_deg": 85.0 if has_landing else None
        },
        "balance": {
            "score": balance_score,
            "status": "good" if balance_score >= 80 else "poor",
            "lateral_sway_std": 0.015
        },
        "alignment": {
            "score": align_score,
            "status": "Optimal",
            "data_quality": {"average_joint_coverage_percent": 98.0}
        },
        "posture": {
            "score": posture_score,
            "measurements": {"shoulder_tilt_deg": 1.2}
        },
        "symmetry": {
            "overall_symmetry_score": symmetry_score,
            "factors": [
                {"metric": "Knee Range of Motion", "symmetry_score": symmetry_score, "absolute_diff": 2.0},
                {"metric": "Hip Range of Motion", "symmetry_score": symmetry_score, "absolute_diff": 1.5}
            ]
        },
        "stride": {
            "normalized_stride_length": 0.65,
            "stride_asymmetry_pct": stride_asym,
            "is_locomotion_detected": True
        },
        "joint_angles": {
            "summary": {
                "right_knee": {"min_angle": 80.0, "max_angle": 175.0, "avg_angle": 140.0, "rom": 95.0},
                "left_knee": {"min_angle": 82.0, "max_angle": 176.0, "avg_angle": 141.0, "rom": 94.0}
            }
        },
        "force": {
            "peak_force_n": 1450.0,
            "peak_force_bw": 2.1,
            "estimated_body_mass_kg": 70.0
        },
        "feature_quality": {
            "total_frames": 120,
            "valid_pose_frames": 118,
            "pose_coverage_percent": 98.3,
            "left_leg_valid_frames": 118,
            "right_leg_valid_frames": 118,
            "trunk_valid_frames": 118
        }
    }


def test_case_1_good_movement():
    print("\n--- Test Case 1: Good Movement (Expected: Low Risk) ---")
    features = _make_features(
        r_valgus=0.02,
        l_valgus=0.02,
        hip_score=95.0,
        trunk_score=95.0,
        landing_score=92.0,
        balance_score=94.0,
        symmetry_score=95.0
    )
    profile = {"training_load": 55.0, "height": 178, "weight": 72}
    history = []  # No injuries

    res = calculate_injury_risk(features, profile, history)

    print(f"Risk Score: {res['injury_risk_score']} / 100")
    print(f"Risk Category: {res['risk_category']}")
    print(f"Movement Quality: {res['movement_quality_score']} / 100 ({res['movement_quality_category']})")

    assert res["injury_risk_score"] < 25.0, f"Expected Low Risk (<25), got {res['injury_risk_score']}"
    assert res["risk_category"] == "Low Risk"
    assert res["movement_quality_score"] >= 85.0
    print("[PASS] Case 1 passed.")


def test_case_2_moderate_deviations():
    print("\n--- Test Case 2: Moderate Deviations (Expected: Moderate Risk) ---")
    # Moderate valgus (0.08 normalized = ~35 risk), moderate hip stability drop
    features = _make_features(
        r_valgus=0.08,
        l_valgus=0.07,
        hip_score=68.0,      # 32 risk
        trunk_score=75.0,    # 25 risk
        landing_score=72.0,  # 28 risk
        balance_score=75.0,  # 25 risk
        symmetry_score=82.0  # 18 risk
    )
    profile = {"training_load": 78.0}  # Mild elevated training load (~33 risk)
    history = [{"injury_type": "Ankle sprain", "body_part": "Ankle", "severity": "Mild"}]  # ~27.5 risk

    res = calculate_injury_risk(features, profile, history)

    print(f"Risk Score: {res['injury_risk_score']} / 100")
    print(f"Risk Category: {res['risk_category']}")

    assert 25.0 <= res["injury_risk_score"] < 50.0, f"Expected Moderate Risk (25-49.9), got {res['injury_risk_score']}"
    assert res["risk_category"] == "Moderate Risk"
    print("[PASS] Case 2 passed.")


def test_case_3_severe_deviations():
    print("\n--- Test Case 3: Severe Deviations (Expected: High Risk) ---")
    # High knee valgus (0.15 normalized = 75 risk), poor hip stability, poor landing
    features = _make_features(
        r_valgus=0.15,
        l_valgus=0.04,
        hip_score=40.0,      # 60 risk
        trunk_score=45.0,    # 55 risk
        landing_score=35.0,  # 65 risk
        balance_score=50.0,  # 50 risk
        align_score=55.0,    # 45 risk
        posture_score=55.0,  # 45 risk
        symmetry_score=62.0  # 38 risk
    )
    profile = {"training_load": 88.0}  # Elevated load (~59 risk)
    history = [{"injury_type": "Hamstring strain", "body_part": "Hamstring", "severity": "Severe"}]

    res = calculate_injury_risk(features, profile, history)

    print(f"Risk Score: {res['injury_risk_score']} / 100")
    print(f"Risk Category: {res['risk_category']}")
    print(f"Top Risk Factors: {[f['factor'] for f in res['risk_factors'][:3]]}")

    assert 50.0 <= res["injury_risk_score"] < 75.0, f"Expected High Risk (50-74.9), got {res['injury_risk_score']}"
    assert res["risk_category"] == "High Risk"
    print("[PASS] Case 3 passed.")


def test_case_4_multiple_critical_deviations():
    print("\n--- Test Case 4: Multiple Severe Deviations (Expected: Critical Risk) ---")
    # Extreme valgus (>0.18 = 85+ risk), failure in hip, trunk, balance, landing, symmetry
    features = _make_features(
        r_valgus=0.18,
        l_valgus=0.17,
        hip_score=20.0,      # 80 risk
        trunk_score=25.0,    # 75 risk
        landing_score=15.0,  # 85 risk
        balance_score=20.0,  # 80 risk
        align_score=25.0,    # 75 risk
        posture_score=25.0,  # 75 risk
        symmetry_score=45.0, # 55 risk
        stride_asym=35.0
    )
    profile = {"training_load": 98.0}  # Acute spike (>90 risk)
    history = [
        {"injury_type": "ACL tear", "body_part": "Knee / ACL", "severity": "Severe"},
        {"injury_type": "Meniscus tear", "body_part": "Knee", "severity": "Moderate"}
    ]

    res = calculate_injury_risk(features, profile, history)

    print(f"Risk Score: {res['injury_risk_score']} / 100")
    print(f"Risk Category: {res['risk_category']}")

    assert res["injury_risk_score"] >= 75.0, f"Expected Critical Risk (>=75), got {res['injury_risk_score']}"
    assert res["risk_category"] == "Critical Risk"
    print("[PASS] Case 4 passed.")


def test_case_5_missing_historical_data():
    print("\n--- Test Case 5: Missing Historical Data ---")
    features = _make_features(r_valgus=0.03, l_valgus=0.03, hip_score=85.0)

    # Empty list and None
    res1 = calculate_injury_risk(features, athlete_profile=None, historical_data=[])
    res2 = calculate_injury_risk(features, athlete_profile=None, historical_data=None)

    assert res1["component_scores"]["historical_injury_factors"] == 0.0
    assert res2["component_scores"]["historical_injury_factors"] == 0.0
    assert res1["component_statuses"]["historical_injury"] == "No injury history recorded"
    print("[PASS] Case 5 passed: missing history produces 0 risk and is marked unavailable.")


def test_case_6_missing_training_load_data():
    print("\n--- Test Case 6: Missing Training-Load Data ---")
    features = _make_features(r_valgus=0.03, l_valgus=0.03, hip_score=85.0)

    res = calculate_injury_risk(features, athlete_profile={}, historical_data=[])

    assert res["component_scores"]["training_load"] == 0.0
    assert res["component_statuses"]["training_load"] == "Training load data unavailable"
    print("[PASS] Case 6 passed: missing training load produces 0 risk and is marked unavailable.")


def test_case_7_fatigue_disabled():
    print("\n--- Test Case 7: Fatigue Disabled ---")
    features = _make_features(r_valgus=0.03, l_valgus=0.03)

    res = calculate_injury_risk(features)

    assert res["component_scores"]["fatigue"] is None
    assert res["component_weights"]["fatigue"] == 0.0
    assert WEIGHT_FATIGUE == 0.0
    # Confirm active weights sum to 1.0
    active_sum = (
        WEIGHT_BIOMECHANICAL +
        WEIGHT_HISTORICAL +
        WEIGHT_ASYMMETRY +
        WEIGHT_TRAINING_LOAD
    )
    assert abs(active_sum - 1.0) < 1e-6, f"Active weights sum to {active_sum}, expected 1.0"
    print("[PASS] Case 7 passed: fatigue is disabled (0% weight, None score) and active weights sum to 100%.")


def test_case_8_asymmetry_and_affected_side():
    print("\n--- Test Case 8: Left vs Right Asymmetry & Affected Side Detection ---")
    # Unilateral high right knee valgus (0.14) vs normal left knee valgus (0.02)
    features = _make_features(
        r_valgus=0.14,
        l_valgus=0.02,
        symmetry_score=72.0
    )

    res = calculate_injury_risk(features)

    knee_factors = [f for f in res["risk_factors"] if "Knee" in f["factor"]]
    assert len(knee_factors) > 0, "Expected Knee Valgus risk factor to be flagged"
    assert knee_factors[0]["side"] == "Right", f"Expected Right side, got {knee_factors[0]['side']}"

    # Now unilateral high left knee valgus
    features_left = _make_features(
        r_valgus=0.02,
        l_valgus=0.14,
        symmetry_score=72.0
    )
    res_left = calculate_injury_risk(features_left)
    knee_factors_l = [f for f in res_left["risk_factors"] if "Knee" in f["factor"]]
    assert knee_factors_l[0]["side"] == "Left", f"Expected Left side, got {knee_factors_l[0]['side']}"

    print("[PASS] Case 8 passed: affected side correctly identified as Right and Left.")


def test_case_9_no_double_counting():
    print("\n--- Test Case 9: No Double Counting ---")
    # Features with severe knee valgus but high overall symmetry elsewhere
    features = _make_features(
        r_valgus=0.13,
        l_valgus=0.13,  # Bilateral identical valgus -> low asymmetry
        symmetry_score=95.0
    )

    res = calculate_injury_risk(features)

    # Knee valgus will elevate biomechanical deviations
    assert res["component_scores"]["biomechanical_deviations"] > 20.0
    # But movement asymmetry remains low because bilateral symmetry was 95%
    assert res["component_scores"]["movement_asymmetry"] <= 10.0
    print("[PASS] Case 9 passed: severity and asymmetry are evaluated independently.")


def test_case_10_pdf_generation_e2e():
    print("\n--- Test Case 10: PDF Report Generation E2E ---")
    features = _make_features(r_valgus=0.11, l_valgus=0.04, hip_score=70.0)
    athlete_info = {
        "name": "Jordan Henderson",
        "sport": "Football",
        "position": "Midfielder",
        "height": 182.0,
        "weight": 76.0,
        "training_load": 75.0
    }
    video_info = {
        "activity": "Single Leg Deceleration Test",
        "fps": 30.0,
        "duration": 4.5,
        "total_frames": 135,
        "valid_pose_frames": 132
    }

    res = calculate_injury_risk(features, athlete_info)

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tf:
        pdf_path = tf.name

    try:
        generated_path = generate_pdf_report(
            output_pdf_path=pdf_path,
            athlete_info=athlete_info,
            video_info=video_info,
            analysis_id="test-analysis-12345",
            summary_metrics=features,
            risk_assessment=res
        )

        assert os.path.exists(generated_path), "PDF file was not created"
        file_size = os.path.getsize(generated_path)
        assert file_size > 2000, f"Generated PDF suspiciously small: {file_size} bytes"
        print(f"[PASS] Case 10 passed: PDF generated successfully ({file_size} bytes).")
    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)


def run_all_tests():
    print("================================================================")
    print("RUNNING INJURY RISK SCORING ENGINE VALIDATION SUITE")
    print("================================================================")
    test_case_1_good_movement()
    test_case_2_moderate_deviations()
    test_case_3_severe_deviations()
    test_case_4_multiple_critical_deviations()
    test_case_5_missing_historical_data()
    test_case_6_missing_training_load_data()
    test_case_7_fatigue_disabled()
    test_case_8_asymmetry_and_affected_side()
    test_case_9_no_double_counting()
    test_case_10_pdf_generation_e2e()
    print("\n================================================================")
    print("ALL 10 TEST CASES PASSED SUCCESSFULLY!")
    print("================================================================")


if __name__ == "__main__":
    run_all_tests()
