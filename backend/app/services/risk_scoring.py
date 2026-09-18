"""
Transparent Rule-Based Sports Injury Risk Scoring Engine.

Consumes genuine extracted biomechanical features, athlete profile, and historical injury data.
Calculates deterministic, explainable injury risk scores without machine learning models,
neural networks, or black-box predictions.
"""

import logging
import math
from datetime import date, datetime
from typing import Dict, Any, List, Optional

from app.services.risk_config import (
    WEIGHT_BIOMECHANICAL,
    WEIGHT_HISTORICAL,
    WEIGHT_ASYMMETRY,
    WEIGHT_TRAINING_LOAD,
    WEIGHT_FATIGUE,
    COMPONENT_WEIGHTS,
    DISPLAY_WEIGHTS,
    RISK_THRESHOLDS,
    MOVEMENT_QUALITY_THRESHOLDS,
    BIOMECHANICAL_SUBMETRIC_WEIGHTS,
    KNEE_VALGUS_THRESHOLDS,
    HISTORY_AGGREGATION_DECAY,
    HISTORY_DEFAULT_UNKNOWN_SCORE,
    HISTORY_RECENCY_HALF_LIFE_YEARS,
    HISTORY_RELEVANCE_BODY_PART_MATCH,
    HISTORY_RELEVANCE_CURRENT_FINDING_MATCH,
    HISTORY_RELEVANCE_DEFAULT,
    HISTORY_RELEVANCE_SIDE_MATCH,
    HISTORY_SCORE_WEIGHTS,
    HISTORY_SEVERITY_SCORES,
    HISTORY_STATUS_SCORES,
    RECOMMENDATIONS_CATALOG
)

logger = logging.getLogger("injury_risk_engine")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter("[RISK-ENGINE] %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)


def _classify_score(score: float, thresholds: Dict[str, tuple]) -> str:
    """Classifies a scalar score using a dictionary of category bounds."""
    for category, (low, high) in thresholds.items():
        if low <= score <= high:
            return category
    # Fallback bounds check
    first_cat = list(thresholds.keys())[0]
    last_cat = list(thresholds.keys())[-1]
    return first_cat if score < 0.0 else last_cat


def _score_valgus_to_risk(norm_valgus: Optional[float]) -> Optional[float]:
    """
    Converts 2D normalized medial knee displacement into a 0-100 risk score.
    Follows normalized thresholds from knee_valgus.py:
      < 0.05  : Normal   (Risk 0 - 20)
      0.05-0.10: Mild    (Risk 20 - 45)
      0.10-0.15: Moderate (Risk 45 - 75)
      >= 0.15 : High     (Risk 75 - 100)
    """
    if norm_valgus is None:
        return None
    val = abs(float(norm_valgus))
    if val < 0.05:
        return round((val / 0.05) * 20.0, 1)
    elif val < 0.10:
        return round(20.0 + ((val - 0.05) / 0.05) * 25.0, 1)
    elif val < 0.15:
        return round(45.0 + ((val - 0.10) / 0.05) * 30.0, 1)
    else:
        return round(min(100.0, 75.0 + ((val - 0.15) / 0.10) * 25.0), 1)


def _classify_severity(risk_contribution: float) -> str:
    """Returns severity label for a single risk factor."""
    if risk_contribution >= 75.0:
        return "Critical"
    elif risk_contribution >= 50.0:
        return "High"
    elif risk_contribution >= 25.0:
        return "Moderate"
    else:
        return "Low"


def _normalize_history_value(value: Any, default: str = "UNKNOWN") -> str:
    if value is None:
        return default
    if hasattr(value, "value"):
        value = value.value
    return str(value).strip().upper().replace(" ", "_")


def _coerce_date(value: Any) -> Optional[date]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None
    return None


def _history_body_group(injury_type: str, body_part: str) -> str:
    text = f"{injury_type} {body_part}".lower()
    if any(term in text for term in ("acl", "mcl", "meniscus", "patellar", "knee")):
        return "knee"
    if any(term in text for term in ("hamstring", "quad", "thigh", "hip", "groin")):
        return "hip"
    if any(term in text for term in ("ankle", "achilles", "calf", "foot")):
        return "ankle"
    if any(term in text for term in ("back", "lumbar", "spine", "trunk")):
        return "trunk"
    if any(term in text for term in ("shoulder", "elbow", "wrist", "arm")):
        return "upper_body"
    return "general"


def _analysis_relevance_score(injury: Dict[str, Any], analysis_context: Optional[Dict[str, Any]]) -> float:
    if not analysis_context:
        return HISTORY_RELEVANCE_DEFAULT

    injury_type = str(injury.get("injury_type") or "")
    body_part = str(injury.get("body_part") or "")
    side = _normalize_history_value(injury.get("affected_side"), "NOT_APPLICABLE")
    group = _history_body_group(injury_type, body_part)

    score = HISTORY_RELEVANCE_DEFAULT

    valgus = analysis_context.get("knee_valgus", {}) if isinstance(analysis_context, dict) else {}
    hip = analysis_context.get("hip_stability", {}) if isinstance(analysis_context, dict) else {}
    trunk = analysis_context.get("trunk_lean", {}) if isinstance(analysis_context, dict) else {}
    posture = analysis_context.get("posture", {}) if isinstance(analysis_context, dict) else {}

    if group == "knee":
        score = max(score, HISTORY_RELEVANCE_BODY_PART_MATCH)
        right_valgus = valgus.get("right", {}).get("peak_normalized_valgus")
        left_valgus = valgus.get("left", {}).get("peak_normalized_valgus")
        if right_valgus is None:
            right_valgus = valgus.get("right", {}).get("max_deviation")
        if left_valgus is None:
            left_valgus = valgus.get("left", {}).get("max_deviation")
        try:
            right_risk = _score_valgus_to_risk(right_valgus)
            left_risk = _score_valgus_to_risk(left_valgus)
            if side == "RIGHT" and right_risk is not None and right_risk >= 45.0:
                score = max(score, HISTORY_RELEVANCE_CURRENT_FINDING_MATCH)
            elif side == "LEFT" and left_risk is not None and left_risk >= 45.0:
                score = max(score, HISTORY_RELEVANCE_CURRENT_FINDING_MATCH)
            elif side == "BILATERAL" and max(right_risk or 0.0, left_risk or 0.0) >= 45.0:
                score = max(score, HISTORY_RELEVANCE_CURRENT_FINDING_MATCH)
            elif max(right_risk or 0.0, left_risk or 0.0) >= 45.0:
                score = max(score, HISTORY_RELEVANCE_SIDE_MATCH)
        except (TypeError, ValueError):
            pass

    elif group == "hip":
        score = max(score, HISTORY_RELEVANCE_BODY_PART_MATCH)
        hip_score = hip.get("score")
        try:
            if hip_score is not None and float(hip_score) < 70.0:
                score = max(score, HISTORY_RELEVANCE_CURRENT_FINDING_MATCH)
        except (TypeError, ValueError):
            pass

    elif group == "ankle":
        score = max(score, HISTORY_RELEVANCE_BODY_PART_MATCH)

    elif group == "trunk":
        score = max(score, HISTORY_RELEVANCE_BODY_PART_MATCH)
        try:
            trunk_score = trunk.get("score")
            if trunk_score is not None and float(trunk_score) < 70.0:
                score = max(score, HISTORY_RELEVANCE_CURRENT_FINDING_MATCH)
        except (TypeError, ValueError):
            pass

    elif group == "upper_body":
        score = max(score, HISTORY_RELEVANCE_BODY_PART_MATCH)
        try:
            posture_score = posture.get("score")
            if posture_score is not None and float(posture_score) < 70.0:
                score = max(score, HISTORY_RELEVANCE_SIDE_MATCH)
        except (TypeError, ValueError):
            pass

    return max(0.0, min(100.0, score))


def calculate_history_score(
    injury_history: Optional[List[Dict[str, Any]]],
    analysis_context: Optional[Dict[str, Any]] = None,
    as_of: Optional[date] = None,
) -> Dict[str, Any]:
    """
    Deterministic historical injury risk score, S_hist in [0, 100].

    No injury history returns 0.0 and never blocks analysis.
    """
    if not injury_history:
        return {
            "score": 0.0,
            "status": "No injury history recorded",
            "factors": [],
            "formula": (
                "S_hist = 0 when injury_history is empty. Otherwise bounded "
                "complement aggregation of per-injury scores."
            ),
        }

    as_of = as_of or date.today()
    factors: List[Dict[str, Any]] = []

    for injury in injury_history:
        injury_date = _coerce_date(injury.get("injury_date"))
        years_since = None
        if injury_date:
            years_since = max(0.0, (as_of - injury_date).days / 365.25)

        status_key = _normalize_history_value(injury.get("status"), "UNKNOWN")
        severity_key = _normalize_history_value(injury.get("severity"), "MODERATE")

        status_score = HISTORY_STATUS_SCORES.get(status_key, HISTORY_DEFAULT_UNKNOWN_SCORE)
        severity_score = HISTORY_SEVERITY_SCORES.get(severity_key, HISTORY_DEFAULT_UNKNOWN_SCORE)
        recency_score = (
            100.0 * math.exp(-years_since / HISTORY_RECENCY_HALF_LIFE_YEARS)
            if years_since is not None
            else HISTORY_DEFAULT_UNKNOWN_SCORE
        )
        relevance_score = _analysis_relevance_score(injury, analysis_context)

        raw_score = (
            HISTORY_SCORE_WEIGHTS["status"] * status_score
            + HISTORY_SCORE_WEIGHTS["severity"] * severity_score
            + HISTORY_SCORE_WEIGHTS["recency"] * recency_score
            + HISTORY_SCORE_WEIGHTS["relevance"] * relevance_score
        )

        single_score = round(max(0.0, min(100.0, raw_score)), 1)
        factors.append({
            "injury_type": injury.get("injury_type"),
            "body_part": injury.get("body_part"),
            "affected_side": _normalize_history_value(injury.get("affected_side"), "NOT_APPLICABLE"),
            "severity": severity_key,
            "status": status_key,
            "injury_date": str(injury_date) if injury_date else None,
            "years_since_injury": round(years_since, 2) if years_since is not None else None,
            "status_score": round(status_score, 1),
            "severity_score": round(severity_score, 1),
            "recency_score": round(recency_score, 1),
            "relevance_score": round(relevance_score, 1),
            "single_injury_score": single_score,
        })

    factors.sort(key=lambda item: item["single_injury_score"], reverse=True)

    survival = 1.0
    for index, factor in enumerate(factors):
        damped_score = factor["single_injury_score"] * (HISTORY_AGGREGATION_DECAY ** index)
        factor["aggregation_weight"] = round(HISTORY_AGGREGATION_DECAY ** index, 3)
        factor["aggregated_score"] = round(damped_score, 1)
        survival *= 1.0 - (damped_score / 100.0)

    historical_score = round(max(0.0, min(100.0, 100.0 * (1.0 - survival))), 1)

    return {
        "score": historical_score,
        "status": "Evaluated",
        "factors": factors,
        "formula": (
            "single = 0.35*status + 0.35*severity + 0.20*recency + "
            "0.10*relevance; recency = 100*exp(-years/3.0); "
            "S_hist = 100*(1 - product(1 - damped_single_i/100))"
        ),
    }


def calculate_injury_risk(
    features: Dict[str, Any],
    athlete_profile: Optional[Dict[str, Any]] = None,
    historical_data: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Primary Entry Point: Rule-Based Injury Risk Scoring Engine.

    Parameters:
        features: Genuine biomechanical features dictionary containing:
                  knee_valgus, hip_stability, trunk_lean, landing,
                  balance, stride, posture, alignment, symmetry, force.
        athlete_profile: Optional athlete metadata (height, weight, sport, training_load).
        historical_data: Optional list of past injury records.

    Returns:
        Structured explainable risk assessment payload.
    """
    explanation_logs: List[str] = []

    def log_step(msg: str):
        explanation_logs.append(msg)
        logger.info(msg)

    log_step("================================================================")
    log_step("STARTING RULE-BASED INJURY RISK ASSESSMENT")
    log_step("================================================================")

    risk_factors: List[Dict[str, Any]] = []

    # =========================================================================
    # 1. BIOMECHANICAL DEVIATIONS DOMAIN (38.89%)
    # =========================================================================
    log_step("\n[1. BIOMECHANICAL DEVIATIONS DOMAIN]")

    # 1A. Frontal Plane Knee Valgus
    valgus_data = features.get("knee_valgus", {})
    r_valgus_norm = valgus_data.get("right", {}).get("peak_normalized_valgus")
    l_valgus_norm = valgus_data.get("left", {}).get("peak_normalized_valgus")

    # If peak_normalized_valgus is not found, fallback to max_deviation
    if r_valgus_norm is None and valgus_data.get("right", {}).get("max_deviation") is not None:
        r_valgus_norm = valgus_data.get("right", {}).get("max_deviation")
    if l_valgus_norm is None and valgus_data.get("left", {}).get("max_deviation") is not None:
        l_valgus_norm = valgus_data.get("left", {}).get("max_deviation")

    r_knee_risk = _score_valgus_to_risk(r_valgus_norm)
    l_knee_risk = _score_valgus_to_risk(l_valgus_norm)

    knee_valgus_risk = None
    knee_affected_side = "General"

    if r_knee_risk is not None and l_knee_risk is not None:
        # Weighted bilateral risk: 70% worse side + 30% other side to prevent diluting severe unilateral deviation
        worse_risk = max(r_knee_risk, l_knee_risk)
        better_risk = min(r_knee_risk, l_knee_risk)
        knee_valgus_risk = round(worse_risk * 0.70 + better_risk * 0.30, 1)

        if r_knee_risk >= 50.0 and l_knee_risk >= 50.0:
            knee_affected_side = "Bilateral"
        elif r_knee_risk >= 45.0 and r_knee_risk > l_knee_risk + 15.0:
            knee_affected_side = "Right"
        elif l_knee_risk >= 45.0 and l_knee_risk > r_knee_risk + 15.0:
            knee_affected_side = "Left"
        elif abs(r_knee_risk - l_knee_risk) >= 20.0:
            knee_affected_side = "Right" if r_knee_risk > l_knee_risk else "Left"
        else:
            knee_affected_side = "Bilateral"

    elif r_knee_risk is not None:
        knee_valgus_risk = r_knee_risk
        knee_affected_side = "Right"
    elif l_knee_risk is not None:
        knee_valgus_risk = l_knee_risk
        knee_affected_side = "Left"
    elif valgus_data.get("score") is not None:
        knee_valgus_risk = round(max(0.0, 100.0 - float(valgus_data["score"])), 1)
        knee_affected_side = "Bilateral"

    log_step(f"  - Right Knee Valgus: Observed = {r_valgus_norm}, Risk Score = {r_knee_risk}/100")
    log_step(f"  - Left Knee Valgus:  Observed = {l_valgus_norm}, Risk Score = {l_knee_risk}/100")
    log_step(f"  - Combined Knee Valgus Risk: {knee_valgus_risk}/100 (Affected Side: {knee_affected_side})")

    if knee_valgus_risk is not None and knee_valgus_risk >= 25.0:
        if r_valgus_norm is not None and l_valgus_norm is not None:
            try:
                obs_str = f"R: {float(r_valgus_norm):.2f}, L: {float(l_valgus_norm):.2f}"
            except (ValueError, TypeError):
                obs_str = f"R: {r_valgus_norm}, L: {l_valgus_norm}"
        elif r_valgus_norm is not None:
            try:
                obs_str = f"R: {float(r_valgus_norm):.2f}"
            except (ValueError, TypeError):
                obs_str = f"R: {r_valgus_norm}"
        elif l_valgus_norm is not None:
            try:
                obs_str = f"L: {float(l_valgus_norm):.2f}"
            except (ValueError, TypeError):
                obs_str = f"L: {l_valgus_norm}"
        else:
            obs_str = "Observed valgus deviation"

        risk_factors.append({
            "factor": f"Dynamic Knee Valgus ({knee_affected_side})",
            "observed_value": obs_str,
            "risk_contribution": knee_valgus_risk,
            "severity": _classify_severity(knee_valgus_risk),
            "side": knee_affected_side
        })

    # 1B. Hip / Pelvic Stability
    hip_data = features.get("hip_stability", {})
    hip_score = hip_data.get("score")
    hip_risk = None
    hip_affected_side = "Bilateral"

    if hip_score is not None:
        hip_risk = round(max(0.0, min(100.0, 100.0 - float(hip_score))), 1)
        r_hip = hip_data.get("right_hip_stability")
        l_hip = hip_data.get("left_hip_stability")
        if r_hip is not None and l_hip is not None:
            if r_hip < l_hip - 10.0:
                hip_affected_side = "Right"
            elif l_hip < r_hip - 10.0:
                hip_affected_side = "Left"
            else:
                hip_affected_side = "Bilateral"

        log_step(f"  - Hip Stability Score: {hip_score}/100 -> Risk Contribution: {hip_risk}/100 (Side: {hip_affected_side})")
        if hip_risk >= 25.0:
            avg_tilt = hip_data.get("avg_pelvic_tilt_deg", "N/A")
            risk_factors.append({
                "factor": f"Reduced Hip/Pelvic Stability ({hip_affected_side})",
                "observed_value": f"Stability {hip_score}/100 (Avg tilt: {avg_tilt}°)",
                "risk_contribution": hip_risk,
                "severity": _classify_severity(hip_risk),
                "side": hip_affected_side
            })

    # 1C. Torso / Trunk Lean
    trunk_data = features.get("trunk_lean", {})
    trunk_score = trunk_data.get("score")
    avg_trunk_lean = trunk_data.get("avg_trunk_lean_deg")
    predominant_dir = trunk_data.get("predominant_direction", "Neutral")
    trunk_risk = None
    trunk_side = "General"

    if "Left" in predominant_dir:
        trunk_side = "Left"
    elif "Right" in predominant_dir:
        trunk_side = "Right"
    else:
        trunk_side = "Bilateral"

    if trunk_score is not None:
        trunk_risk = round(max(0.0, min(100.0, 100.0 - float(trunk_score))), 1)
    elif avg_trunk_lean is not None:
        trunk_risk = round(min(100.0, max(0.0, (float(avg_trunk_lean) / 20.0) * 100.0)), 1)

    if trunk_risk is not None:
        log_step(f"  - Trunk Lean: Observed = {avg_trunk_lean}°, Score = {trunk_score} -> Risk Contribution: {trunk_risk}/100")
        if trunk_risk >= 25.0:
            risk_factors.append({
                "factor": f"Compensatory Trunk Lean ({trunk_side})",
                "observed_value": f"{avg_trunk_lean}° avg ({predominant_dir})",
                "risk_contribution": trunk_risk,
                "severity": _classify_severity(trunk_risk),
                "side": trunk_side
            })

    # 1D. Landing Mechanics
    landing_data = features.get("landing", {})
    has_landing = landing_data.get("has_landing_data", False)
    landing_score = landing_data.get("score")
    landing_risk = None
    landing_status_note = "Landing mechanics data unavailable / no impact event"

    if has_landing and landing_score is not None:
        landing_risk = round(max(0.0, min(100.0, 100.0 - float(landing_score))), 1)
        landing_status_note = "Evaluated"
        log_step(f"  - Landing Mechanics: Quality = {landing_score}/100 -> Risk Contribution: {landing_risk}/100")
        if landing_risk >= 25.0:
            risk_factors.append({
                "factor": "Stiff Impact Landing Mechanics",
                "observed_value": f"Score {landing_score}/100",
                "risk_contribution": landing_risk,
                "severity": _classify_severity(landing_risk),
                "side": "Bilateral"
            })
    else:
        log_step(f"  - Landing Mechanics: {landing_status_note}")

    # 1E. Dynamic Balance
    balance_data = features.get("balance", {})
    balance_score = balance_data.get("score")
    balance_risk = None

    if balance_score is not None:
        balance_risk = round(max(0.0, min(100.0, 100.0 - float(balance_score))), 1)
        log_step(f"  - Dynamic Balance: Score = {balance_score}/100 -> Risk Contribution: {balance_risk}/100")
        if balance_risk >= 25.0:
            lat_sway = balance_data.get("lateral_sway_std", "N/A")
            risk_factors.append({
                "factor": "Dynamic Balance & Postural Sway Instability",
                "observed_value": f"Score {balance_score}/100 (Sway std: {lat_sway})",
                "risk_contribution": balance_risk,
                "severity": _classify_severity(balance_risk),
                "side": "General"
            })

    # 1F. Joint Alignment
    alignment_data = features.get("alignment", {})
    align_score = alignment_data.get("score")
    align_risk = None

    if align_score is not None:
        align_risk = round(max(0.0, min(100.0, 100.0 - float(align_score))), 1)
        log_step(f"  - Joint Alignment: Score = {align_score}/100 -> Risk Contribution: {align_risk}/100")
        if align_risk >= 25.0:
            risk_factors.append({
                "factor": "Kinematic Chain Joint Malalignment",
                "observed_value": f"Score {align_score}/100",
                "risk_contribution": align_risk,
                "severity": _classify_severity(align_risk),
                "side": "General"
            })

    # 1G. Posture Assessment
    posture_data = features.get("posture", {})
    posture_score = posture_data.get("score")
    posture_risk = None

    if posture_score is not None:
        posture_risk = round(max(0.0, min(100.0, 100.0 - float(posture_score))), 1)
        log_step(f"  - Posture Assessment: Score = {posture_score}/100 -> Risk Contribution: {posture_risk}/100")
        if posture_risk >= 25.0:
            risk_factors.append({
                "factor": "Postural Alignment Deviations",
                "observed_value": f"Score {posture_score}/100",
                "risk_contribution": posture_risk,
                "severity": _classify_severity(posture_risk),
                "side": "General"
            })

    # Composite Biomechanical Risk Calculation with dynamic re-weighting for missing metrics
    submetric_risks = [
        (knee_valgus_risk, BIOMECHANICAL_SUBMETRIC_WEIGHTS["knee_valgus"]),
        (hip_risk, BIOMECHANICAL_SUBMETRIC_WEIGHTS["hip_stability"]),
        (landing_risk, BIOMECHANICAL_SUBMETRIC_WEIGHTS["landing_mechanics"]),
        (trunk_risk, BIOMECHANICAL_SUBMETRIC_WEIGHTS["trunk_lean"]),
        (balance_risk, BIOMECHANICAL_SUBMETRIC_WEIGHTS["dynamic_balance"]),
        (align_risk, BIOMECHANICAL_SUBMETRIC_WEIGHTS["joint_alignment"]),
        (posture_risk, BIOMECHANICAL_SUBMETRIC_WEIGHTS["posture"])
    ]

    valid_submetrics = [(r, w) for r, w in submetric_risks if r is not None]
    if valid_submetrics:
        total_sub_w = sum(w for _, w in valid_submetrics)
        biomechanical_deviations_risk = round(sum(r * w for r, w in valid_submetrics) / total_sub_w, 1)
    else:
        biomechanical_deviations_risk = 0.0

    log_step(f"-> FINAL BIOMECHANICAL DEVIATIONS RISK: {biomechanical_deviations_risk}/100 (Active Weight: {DISPLAY_WEIGHTS['biomechanical_deviations']})")

    # =========================================================================
    # 2. MOVEMENT ASYMMETRY DOMAIN (22.22%)
    # =========================================================================
    log_step("\n[2. MOVEMENT ASYMMETRY DOMAIN]")

    symmetry_data = features.get("symmetry", {})
    overall_sym_score = symmetry_data.get("overall_symmetry_score")
    stride_data = features.get("stride", {})
    stride_asym = stride_data.get("stride_asymmetry_pct")

    affected_asym_metrics: List[str] = []

    # Derive asymmetry risk (100 - symmetry)
    if overall_sym_score is not None:
        base_asym_risk = max(0.0, min(100.0, 100.0 - float(overall_sym_score)))
    else:
        base_asym_risk = 0.0

    # Inspect component asymmetries for specific affected metrics
    sym_factors = symmetry_data.get("factors", []) if isinstance(symmetry_data, dict) else []
    for factor in sym_factors:
        if not isinstance(factor, dict):
            continue
        m_name = factor.get("metric", "Kinematic Parameter")
        f_score = factor.get("symmetry_score")
        f_diff = factor.get("absolute_diff", "-")
        if f_score is not None:
            try:
                f_score_num = float(f_score)
                if f_score_num < 80.0:
                    affected_asym_metrics.append(f"{m_name} ({f_score_num:.0f}% symmetry, diff: {f_diff})")
            except (ValueError, TypeError):
                pass

    if stride_asym is not None:
        try:
            stride_asym_num = float(stride_asym)
            if stride_asym_num > 15.0:
                affected_asym_metrics.append(f"Stride Kinematics Asymmetry ({stride_asym_num:.1f}%)")
        except (ValueError, TypeError):
            pass

    # Assess knee valgus asymmetry directly
    if r_valgus_norm is not None and l_valgus_norm is not None:
        try:
            valgus_diff = abs(float(r_valgus_norm) - float(l_valgus_norm))
            if valgus_diff > 0.05:
                affected_asym_metrics.append(f"Frontal Knee Valgus Asymmetry (diff: {valgus_diff:.2f})")
        except (ValueError, TypeError):
            pass

    asymmetry_risk = round(base_asym_risk, 1)
    log_step(f"  - Overall Symmetry Match: {overall_sym_score}% -> Asymmetry Risk: {asymmetry_risk}/100")
    if affected_asym_metrics:
        log_step(f"  - Affected Asymmetry Metrics: {', '.join(affected_asym_metrics)}")

    if asymmetry_risk >= 25.0:
        side_label = "Bilateral"
        if r_valgus_norm is not None and l_valgus_norm is not None and abs(r_valgus_norm - l_valgus_norm) > 0.06:
            side_label = "Right" if r_valgus_norm > l_valgus_norm else "Left"

        risk_factors.append({
            "factor": "Bilateral Kinematic Movement Asymmetry",
            "observed_value": f"{overall_sym_score}% symmetry index",
            "risk_contribution": asymmetry_risk,
            "severity": _classify_severity(asymmetry_risk),
            "side": side_label
        })

    log_step(f"-> FINAL MOVEMENT ASYMMETRY RISK: {asymmetry_risk}/100 (Active Weight: {DISPLAY_WEIGHTS['movement_asymmetry']})")

    # =========================================================================
    # 3. HISTORICAL INJURY FACTORS DOMAIN (22.22%)
    # =========================================================================
    log_step("\n[3. HISTORICAL INJURY FACTORS DOMAIN]")
    history_result = calculate_history_score(historical_data or [], analysis_context=features)
    historical_risk = history_result["score"]
    historical_status = history_result["status"]

    if history_result["factors"]:
        for factor in history_result["factors"]:
            log_step(
                "  - Injury Record: "
                f"{factor.get('injury_type')} ({factor.get('body_part')}, "
                f"{factor.get('affected_side')}, {factor.get('severity')}, "
                f"{factor.get('status')}) -> Single Risk: "
                f"{factor.get('single_injury_score')}/100"
            )

        if historical_risk >= 25.0:
            risk_factors.append({
                "factor": "Prior Orthopedic Injury History",
                "observed_value": f"{len(history_result['factors'])} recorded injuries",
                "risk_contribution": historical_risk,
                "severity": _classify_severity(historical_risk),
                "side": "General"
            })
    else:
        log_step("  - No injury history recorded. Risk contribution set to 0.0 (athlete not penalized).")

    log_step(f"-> FINAL HISTORICAL INJURY RISK: {historical_risk}/100 (Active Weight: {DISPLAY_WEIGHTS['historical_injury_factors']})")

    # =========================================================================
    # 4. TRAINING LOAD INDICATORS DOMAIN (16.67%)
    # =========================================================================
    log_step("\n[4. TRAINING LOAD INDICATORS DOMAIN]")
    training_load_risk = 0.0
    training_load_status = "Training load data unavailable"

    training_load_val = athlete_profile.get("training_load") if athlete_profile else None
    if training_load_val is not None:
        training_load_status = "Evaluated"
        try:
            load = float(training_load_val)
            # Evaluate against sports science load balance curve:
            # 40-70: Optimal range (0-15 risk)
            # 70-85: Elevated load / fatigue threshold (15-50 risk)
            # 85-95: High acute overload (50-80 risk)
            # > 95 : Extreme acute spike (80-100 risk)
            # < 40 : Under-conditioned spike risk (0-30 risk)
            if 40.0 <= load <= 70.0:
                training_load_risk = ((load - 40.0) / 30.0) * 15.0
            elif 70.0 < load <= 85.0:
                training_load_risk = 15.0 + ((load - 70.0) / 15.0) * 35.0
            elif 85.0 < load <= 95.0:
                training_load_risk = 50.0 + ((load - 85.0) / 10.0) * 30.0
            elif load > 95.0:
                training_load_risk = min(100.0, 80.0 + ((load - 95.0) / 5.0) * 20.0)
            else:
                training_load_risk = ((40.0 - load) / 40.0) * 30.0

            training_load_risk = round(training_load_risk, 1)
            log_step(f"  - Athlete Training Load Index: {load} -> Risk Contribution: {training_load_risk}/100")

            if training_load_risk >= 35.0:
                risk_factors.append({
                    "factor": "Elevated Acute Training Load",
                    "observed_value": f"Load Index: {load:.1f}",
                    "risk_contribution": training_load_risk,
                    "severity": _classify_severity(training_load_risk),
                    "side": "General"
                })
        except (ValueError, TypeError):
            training_load_status = "Training load data invalid"
            training_load_risk = 0.0
    else:
        log_step(f"  - {training_load_status}. Risk contribution set to 0.0 (athlete not penalized).")

    log_step(f"-> FINAL TRAINING LOAD RISK: {training_load_risk}/100 (Active Weight: {DISPLAY_WEIGHTS['training_load']})")

    # =========================================================================
    # 5. FATIGUE INDICATORS DOMAIN (0% - DISABLED)
    # =========================================================================
    log_step("\n[5. FATIGUE INDICATORS DOMAIN]")
    log_step("  - Fatigue Indicators = DISABLED in current version. Weight = 0%, score = None.")
    fatigue_risk = None
    fatigue_status = "Disabled in current version"

    # =========================================================================
    # 6. FINAL COMPOSITE INJURY RISK SCORE
    # =========================================================================
    composite_risk = (
        biomechanical_deviations_risk * WEIGHT_BIOMECHANICAL +
        historical_risk * WEIGHT_HISTORICAL +
        asymmetry_risk * WEIGHT_ASYMMETRY +
        training_load_risk * WEIGHT_TRAINING_LOAD
    )
    final_injury_risk_score = round(max(0.0, min(100.0, composite_risk)), 1)
    risk_category = _classify_score(final_injury_risk_score, RISK_THRESHOLDS)

    log_step("\n================================================================")
    log_step(f"COMPOSITE INJURY RISK SCORE: {final_injury_risk_score} / 100")
    log_step(f"RISK CATEGORY: {risk_category}")
    log_step("================================================================")

    # =========================================================================
    # 7. OVERALL MOVEMENT QUALITY SCORE (0–100)
    # =========================================================================
    # Evaluates genuine biomechanical movement execution.
    # Higher score = better movement quality.
    quality_submetrics = [
        (valgus_data.get("score"), 0.25),
        (hip_data.get("score"), 0.20),
        (trunk_data.get("score"), 0.15),
        (balance_data.get("score"), 0.15),
        (symmetry_data.get("overall_symmetry_score"), 0.15),
        (alignment_data.get("score"), 0.10)
    ]
    valid_q = [(s, w) for s, w in quality_submetrics if s is not None]
    if valid_q:
        q_sum_w = sum(w for _, w in valid_q)
        movement_quality_score = round(sum(s * w for s, w in valid_q) / q_sum_w, 1)
    else:
        movement_quality_score = round(max(0.0, min(100.0, 100.0 - final_injury_risk_score)), 1)

    movement_quality_category = _classify_score(movement_quality_score, MOVEMENT_QUALITY_THRESHOLDS)

    # =========================================================================
    # 8. BIOMECHANICAL EFFICIENCY SCORE (0–100)
    # =========================================================================
    # Reflects kinematic efficiency, smoothness, and energy preservation.
    consistency = features.get("kinematic_consistency")
    consistency_val = float(consistency) if consistency is not None else 85.0
    sym_eff = float(overall_sym_score) if overall_sym_score is not None else 85.0
    posture_eff = float(posture_score) if posture_score is not None else 85.0
    hip_eff = float(hip_score) if hip_score is not None else 85.0

    efficiency_calc = (
        consistency_val * 0.30 +
        sym_eff * 0.25 +
        hip_eff * 0.25 +
        posture_eff * 0.20
    )
    biomechanical_efficiency_score = round(max(0.0, min(100.0, efficiency_calc)), 1)

    # =========================================================================
    # 9. OVERALL ATHLETE HEALTH SCORE (0–100)
    # =========================================================================
    # Transparent formula combining active domains:
    # 30% Movement Quality + 30% Biomechanical Efficiency + 20% Symmetry + 20% (100 - Injury Risk)
    health_calc = (
        0.30 * movement_quality_score +
        0.30 * biomechanical_efficiency_score +
        0.20 * (overall_sym_score if overall_sym_score is not None else 85.0) +
        0.20 * (100.0 - final_injury_risk_score)
    )
    overall_athlete_health_score = round(max(0.0, min(100.0, health_calc)), 1)

    # =========================================================================
    # 10. RISK FACTORS SORTING & PRIORITIZATION
    # =========================================================================
    risk_factors.sort(key=lambda x: x["risk_contribution"], reverse=True)

    # =========================================================================
    # 11. TARGETED CORRECTIVE RECOMMENDATIONS
    # =========================================================================
    recommendations: List[Dict[str, Any]] = []

    # Map detected deviations directly to targeted drills
    if knee_valgus_risk is not None:
        if knee_valgus_risk >= 50.0:
            rec = dict(RECOMMENDATIONS_CATALOG["knee_valgus_high"])
            rec["observation"] = f"Elevated dynamic knee valgus observed ({knee_affected_side} side dominant, {knee_valgus_risk:.0f}/100 risk contribution)."
            recommendations.append(rec)
        elif knee_valgus_risk >= 25.0:
            rec = dict(RECOMMENDATIONS_CATALOG["knee_valgus_moderate"])
            rec["observation"] = f"Mild to moderate knee valgus observed ({knee_affected_side} side)."
            recommendations.append(rec)

    if hip_risk is not None:
        if hip_risk >= 50.0:
            rec = dict(RECOMMENDATIONS_CATALOG["hip_stability_poor"])
            rec["observation"] = f"Marked pelvic tilt and lateral hip displacement ({hip_affected_side} side stability deficiency)."
            recommendations.append(rec)
        elif hip_risk >= 25.0:
            rec = dict(RECOMMENDATIONS_CATALOG["hip_stability_moderate"])
            recommendations.append(rec)

    if trunk_risk is not None:
        if trunk_risk >= 50.0:
            rec = dict(RECOMMENDATIONS_CATALOG["trunk_lean_high"])
            rec["observation"] = f"Substantial compensatory trunk lean ({avg_trunk_lean}° inclination toward {trunk_side})."
            recommendations.append(rec)
        elif trunk_risk >= 25.0:
            rec = dict(RECOMMENDATIONS_CATALOG["trunk_lean_moderate"])
            recommendations.append(rec)

    if asymmetry_risk >= 30.0:
        rec = dict(RECOMMENDATIONS_CATALOG["asymmetry_high"])
        if affected_asym_metrics:
            rec["observation"] = f"Kinematic asymmetry observed in: {'; '.join(affected_asym_metrics[:2])}."
        recommendations.append(rec)
    elif asymmetry_risk >= 20.0:
        recommendations.append(dict(RECOMMENDATIONS_CATALOG["asymmetry_moderate"]))

    if landing_risk is not None:
        if landing_risk >= 50.0:
            recommendations.append(dict(RECOMMENDATIONS_CATALOG["landing_mechanics_poor"]))
        elif landing_risk >= 25.0:
            recommendations.append(dict(RECOMMENDATIONS_CATALOG["landing_mechanics_moderate"]))

    if balance_risk is not None and balance_risk >= 35.0:
        recommendations.append(dict(RECOMMENDATIONS_CATALOG["balance_poor"]))

    # If no deviations triggered recommendations, provide general maintenance protocol
    if not recommendations:
        recommendations.append(dict(RECOMMENDATIONS_CATALOG["optimal_maintenance"]))

    # =========================================================================
    # 12. ASSEMBLE FINAL STRUCTURED RESPONSE
    # =========================================================================
    result = {
        "injury_risk_score": final_injury_risk_score,
        "risk_category": risk_category,
        "movement_quality_score": movement_quality_score,
        "movement_quality_category": movement_quality_category,
        "biomechanical_efficiency_score": biomechanical_efficiency_score,
        "overall_athlete_health_score": overall_athlete_health_score,
        "risk_factors": risk_factors,
        "component_scores": {
            "biomechanical_deviations": biomechanical_deviations_risk,
            "historical_injury_factors": historical_risk,
            "movement_asymmetry": asymmetry_risk,
            "training_load": training_load_risk,
            "fatigue": fatigue_risk
        },
        "component_weights": COMPONENT_WEIGHTS,
        "display_weights": DISPLAY_WEIGHTS,
        "component_statuses": {
            "historical_injury": historical_status,
            "training_load": training_load_status,
            "landing_mechanics": landing_status_note,
            "fatigue": fatigue_status
        },
        "historical_injury_details": history_result,
        "asymmetry_details": {
            "symmetry_score": overall_sym_score,
            "asymmetry_risk": asymmetry_risk,
            "affected_metrics": affected_asym_metrics
        },
        "recommendations": recommendations,
        "explanation_log": explanation_logs
    }

    return result
