from datetime import date, timedelta

from app.services.risk_config import (
    WEIGHT_ASYMMETRY,
    WEIGHT_BIOMECHANICAL,
    WEIGHT_HISTORICAL,
    WEIGHT_TRAINING_LOAD,
)
from app.services.risk_scoring import calculate_history_score, calculate_injury_risk


TODAY = date(2026, 9, 8)


def test_no_history_score_is_zero():
    result = calculate_history_score([], as_of=TODAY)
    assert result["score"] == 0.0


def test_old_recovered_mild_injury_has_low_nonzero_score():
    result = calculate_history_score(
        [
            {
                "injury_type": "Ankle sprain",
                "body_part": "Ankle",
                "affected_side": "RIGHT",
                "severity": "MILD",
                "status": "RECOVERED",
                "injury_date": TODAY - timedelta(days=365 * 6),
            }
        ],
        as_of=TODAY,
    )

    assert 0.0 < result["score"] < 45.0


def test_recent_severe_recovered_scores_higher_than_old_mild():
    old_mild = calculate_history_score(
        [
            {
                "injury_type": "Ankle sprain",
                "body_part": "Ankle",
                "severity": "MILD",
                "status": "RECOVERED",
                "injury_date": TODAY - timedelta(days=365 * 6),
            }
        ],
        as_of=TODAY,
    )
    recent_severe = calculate_history_score(
        [
            {
                "injury_type": "ACL injury",
                "body_part": "Knee",
                "severity": "SEVERE",
                "status": "RECOVERED",
                "injury_date": TODAY - timedelta(days=60),
            }
        ],
        as_of=TODAY,
    )

    assert recent_severe["score"] > old_mild["score"]


def test_active_injury_scores_high_and_bounded():
    result = calculate_history_score(
        [
            {
                "injury_type": "ACL injury",
                "body_part": "Knee",
                "affected_side": "LEFT",
                "severity": "SEVERE",
                "status": "ACTIVE",
                "injury_date": TODAY - timedelta(days=14),
            }
        ],
        as_of=TODAY,
    )

    assert result["score"] >= 75.0
    assert result["score"] <= 100.0


def test_multiple_injuries_are_bounded():
    result = calculate_history_score(
        [
            {
                "injury_type": "ACL injury",
                "body_part": "Knee",
                "severity": "SEVERE",
                "status": "ACTIVE",
                "injury_date": TODAY - timedelta(days=10),
            },
            {
                "injury_type": "Hamstring strain",
                "body_part": "Thigh",
                "severity": "MODERATE",
                "status": "RECOVERED",
                "injury_date": TODAY - timedelta(days=180),
            },
            {
                "injury_type": "Shoulder soreness",
                "body_part": "Shoulder",
                "severity": "MILD",
                "status": "UNKNOWN",
                "injury_date": TODAY - timedelta(days=500),
            },
        ],
        as_of=TODAY,
    )

    assert 0.0 <= result["score"] <= 100.0


def test_relevant_knee_history_not_lower_than_unrelated_history():
    context = {
        "knee_valgus": {
            "left": {"peak_normalized_valgus": 0.14},
            "right": {"peak_normalized_valgus": 0.02},
        }
    }

    relevant = calculate_history_score(
        [
            {
                "injury_type": "ACL injury",
                "body_part": "Left knee",
                "affected_side": "LEFT",
                "severity": "SEVERE",
                "status": "RECOVERED",
                "injury_date": TODAY - timedelta(days=120),
            }
        ],
        analysis_context=context,
        as_of=TODAY,
    )
    unrelated = calculate_history_score(
        [
            {
                "injury_type": "Shoulder strain",
                "body_part": "Shoulder",
                "affected_side": "RIGHT",
                "severity": "SEVERE",
                "status": "RECOVERED",
                "injury_date": TODAY - timedelta(days=120),
            }
        ],
        analysis_context=context,
        as_of=TODAY,
    )

    assert relevant["score"] >= unrelated["score"]


def test_composite_score_uses_existing_weights():
    features = {
        "knee_valgus": {"score": 80},
        "hip_stability": {"score": 80},
        "trunk_lean": {"score": 80},
        "landing": {"has_landing_data": True, "score": 80},
        "balance": {"score": 80},
        "alignment": {"score": 80},
        "posture": {"score": 80},
        "symmetry": {"overall_symmetry_score": 70, "factors": []},
        "stride": {"stride_asymmetry_pct": 10},
    }
    historical_data = [
        {
            "injury_type": "ACL injury",
            "body_part": "Knee",
            "severity": "SEVERE",
            "status": "ACTIVE",
            "injury_date": str(TODAY - timedelta(days=14)),
        }
    ]

    result = calculate_injury_risk(
        features=features,
        athlete_profile={"training_load": 80},
        historical_data=historical_data,
    )
    components = result["component_scores"]
    expected = round(
        components["biomechanical_deviations"] * WEIGHT_BIOMECHANICAL
        + components["historical_injury_factors"] * WEIGHT_HISTORICAL
        + components["movement_asymmetry"] * WEIGHT_ASYMMETRY
        + components["training_load"] * WEIGHT_TRAINING_LOAD,
        1,
    )

    assert result["injury_risk_score"] == expected


def test_historical_snapshot_changes_only_for_new_calculation():
    analysis_a_score = calculate_history_score([], as_of=TODAY)["score"]

    analysis_b_score = calculate_history_score(
        [
            {
                "injury_type": "ACL injury",
                "body_part": "Knee",
                "severity": "SEVERE",
                "status": "ACTIVE",
                "injury_date": TODAY - timedelta(days=3),
            }
        ],
        as_of=TODAY,
    )["score"]

    assert analysis_a_score == 0.0
    assert analysis_b_score != analysis_a_score
