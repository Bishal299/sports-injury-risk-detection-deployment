"""
Centralized Configuration for Rule-Based Injury Risk Scoring Engine.

All weights, thresholds, score mappings, and corrective exercise recommendations
are defined here to ensure deterministic, explainable, and tunable operation.
"""

from typing import Dict, Any, Tuple

# =============================================================================
# 1. COMPONENT WEIGHTS (ACTIVE REDISTRIBUTION)
# =============================================================================
# Original target model:
#   Biomechanical Deviations = 35%
#   Historical Injury Factors = 20%
#   Movement Asymmetry = 20%
#   Training Load Indicators = 15%
#   Fatigue Indicators = 10%
#
# CURRENT VERSION REQUIREMENT:
# Fatigue is DISABLED (0%). Unused 10% is redistributed proportionally
# across the 4 active categories (sum of active baseline = 90%):
#   Biomechanical:  35 / 90 = 38.8888...% (38.89%)
#   Historical:     20 / 90 = 22.2222...% (22.22%)
#   Asymmetry:      20 / 90 = 22.2222...% (22.22%)
#   Training Load:  15 / 90 = 16.6666...% (16.67%)
#   Fatigue:        0%
# =============================================================================

WEIGHT_BIOMECHANICAL: float = 35.0 / 90.0       # ~0.388888...
WEIGHT_HISTORICAL: float = 20.0 / 90.0          # ~0.222222...
WEIGHT_ASYMMETRY: float = 20.0 / 90.0           # ~0.222222...
WEIGHT_TRAINING_LOAD: float = 15.0 / 90.0       # ~0.166666...
WEIGHT_FATIGUE: float = 0.0                     # Disabled in current version

COMPONENT_WEIGHTS: Dict[str, float] = {
    "biomechanical_deviations": WEIGHT_BIOMECHANICAL,
    "historical_injury_factors": WEIGHT_HISTORICAL,
    "movement_asymmetry": WEIGHT_ASYMMETRY,
    "training_load": WEIGHT_TRAINING_LOAD,
    "fatigue": WEIGHT_FATIGUE
}

# Display percentages for reports and UI
DISPLAY_WEIGHTS: Dict[str, str] = {
    "biomechanical_deviations": "38.9%",
    "historical_injury_factors": "22.2%",
    "movement_asymmetry": "22.2%",
    "training_load": "16.7%",
    "fatigue": "0.0% (Disabled)"
}

# 2. RISK CATEGORY THRESHOLDS
# Final Injury Risk Score is classified into exactly 4 categories:
#   0–24.99   : Low Risk
#   25–49.99  : Moderate Risk
#   50–74.99  : High Risk
#   75–100.0  : Critical Risk

RISK_THRESHOLDS: Dict[str, Tuple[float, float]] = {
    "Low Risk": (0.0, 24.999),
    "Moderate Risk": (25.0, 49.999),
    "High Risk": (50.0, 74.999),
    "Critical Risk": (75.0, 100.0)
}

# =============================================================================
# 3. MOVEMENT QUALITY CLASSIFICATION THRESHOLDS
# =============================================================================
# Overall Movement Quality Score (0–100):
#   90–100  : Excellent
#   75–89.9 : Good
#   60–74.9 : Fair
#   40–59.9 : Poor
#   0–39.9  : Very Poor
# =============================================================================

MOVEMENT_QUALITY_THRESHOLDS: Dict[str, Tuple[float, float]] = {
    "Excellent": (90.0, 100.0),
    "Good": (75.0, 89.999),
    "Fair": (60.0, 74.999),
    "Poor": (40.0, 59.999),
    "Very Poor": (0.0, 39.999)
}

# 4. BIOMECHANICAL SUB-METRIC RELATIVE WEIGHTS
# Within the Biomechanical Deviation domain (38.89%), sub-metrics have
# the following relative importance:
#   Knee Valgus receives the highest importance (30%).

BIOMECHANICAL_SUBMETRIC_WEIGHTS: Dict[str, float] = {
    "knee_valgus": 0.30,
    "hip_stability": 0.20,
    "landing_mechanics": 0.15,
    "trunk_lean": 0.10,
    "dynamic_balance": 0.10,
    "joint_alignment": 0.10,
    "posture": 0.05
}

# =============================================================================
# 5. KNEE VALGUS NORMATIVE THRESHOLDS
# =============================================================================
# MediaPipe 2D normalized medial displacement thresholds as established
# in knee_valgus.py (ratio relative to leg length):
#   Normal   : < 0.05
#   Mild     : 0.05 - 0.10
#   Moderate : 0.10 - 0.15
#   High     : >= 0.15
# =============================================================================

KNEE_VALGUS_THRESHOLDS: Dict[str, float] = {
    "normal": 0.05,
    "mild": 0.10,
    "moderate": 0.15
}

# =============================================================================
# 6. TRUNK LEAN THRESHOLDS (DEGREES FROM VERTICAL)
# =============================================================================

TRUNK_LEAN_THRESHOLDS: Dict[str, float] = {
    "normal": 5.0,
    "mild": 10.0,
    "moderate": 15.0,
    "severe": 20.0
}

# =============================================================================
# 7. ASYMMETRY THRESHOLDS (PERCENT DIFFERENCE)
# =============================================================================

ASYMMETRY_THRESHOLDS: Dict[str, float] = {
    "optimal": 10.0,     # < 10% difference is normal physiological variance
    "mild": 15.0,        # 10% - 15%
    "moderate": 25.0,    # 15% - 25%
    "severe": 35.0       # > 25%
}

# =============================================================================
# 8. TRAINING LOAD RISK THRESHOLDS
# =============================================================================
# When training_load (0-100 index or arbitrary acute load) is provided:
# Optimal range: 40-70 -> low risk
# Moderate fatigue/overreach: 70-85 -> moderate risk
# High fatigue/spike: > 85 -> high risk
# Under-conditioning: < 25 with high intensity -> moderate risk
# =============================================================================

TRAINING_LOAD_THRESHOLDS: Dict[str, Any] = {
    "optimal_min": 40.0,
    "optimal_max": 70.0,
    "elevated": 85.0,
    "critical": 95.0
}

# =============================================================================
# 9. HISTORICAL INJURY RISK SCORING
# =============================================================================
# Per-injury base score:
#   35% status + 35% severity + 20% recency + 10% biomechanical relevance
#
# Recency score uses exponential decay:
#   recency = 100 * exp(-years_since_injury / HISTORY_RECENCY_HALF_LIFE_YEARS)
#
# Multiple injuries are combined with a bounded complement aggregation after
# sorting by severity:
#   S_hist = 100 * (1 - product(1 - adjusted_i / 100))
# where secondary injuries are damped by HISTORY_AGGREGATION_DECAY ** index.
# =============================================================================

HISTORY_SCORING_VERSION: str = "history-risk-v1"

HISTORY_STATUS_SCORES: Dict[str, float] = {
    "ACTIVE": 95.0,
    "CHRONIC": 80.0,
    "UNKNOWN": 55.0,
    "RECOVERED": 30.0,
}

HISTORY_SEVERITY_SCORES: Dict[str, float] = {
    "MILD": 25.0,
    "MODERATE": 55.0,
    "SEVERE": 85.0,
}

HISTORY_SCORE_WEIGHTS: Dict[str, float] = {
    "status": 0.35,
    "severity": 0.35,
    "recency": 0.20,
    "relevance": 0.10,
}

HISTORY_RECENCY_HALF_LIFE_YEARS: float = 3.0
HISTORY_DEFAULT_UNKNOWN_SCORE: float = 45.0
HISTORY_AGGREGATION_DECAY: float = 0.65
HISTORY_RELEVANCE_DEFAULT: float = 35.0
HISTORY_RELEVANCE_BODY_PART_MATCH: float = 65.0
HISTORY_RELEVANCE_SIDE_MATCH: float = 80.0
HISTORY_RELEVANCE_CURRENT_FINDING_MATCH: float = 100.0

# =============================================================================
# 10. TARGETED CORRECTIVE RECOMMENDATION CATALOG
# =============================================================================
# Evidence-based corrective actions and drills mapped to detected risk factors.
# =============================================================================

RECOMMENDATIONS_CATALOG: Dict[str, Dict[str, Any]] = {
    "knee_valgus_high": {
        "category": "Knee Mechanics & Neuromuscular Control",
        "priority": "High",
        "observation": "Elevated dynamic knee valgus observed under loading.",
        "action": "Prioritize hip abductor (gluteus medius) and external rotator strengthening. Focus on cues to keep knees tracking over toes during deceleration and change-of-direction.",
        "drills": ["Banded Squats with Lateral Resistance", "Single-Leg Step-Downs with Mirror Feedback", "Monster Band Walks", "Terminal Knee Extensions (TKE)"]
    },
    "knee_valgus_moderate": {
        "category": "Knee Mechanics",
        "priority": "Medium",
        "observation": "Moderate medial knee displacement observed during movement.",
        "action": "Reinforce frontal-plane knee alignment during squatting and landing movements.",
        "drills": ["Mirror Squats for Visual Biofeedback", "Banded Glute Bridges", "Clamshells with Tempo Pause"]
    },
    "hip_stability_poor": {
        "category": "Pelvic Stability & Core Integration",
        "priority": "High",
        "observation": "Significant pelvic tilt and lateral hip drop detected during motion.",
        "action": "Target the lumbo-pelvic-hip complex. Emphasize anti-lateral flexion and quadratus lumborum/gluteal integration to eliminate Trendelenburg-like compensatory mechanics.",
        "drills": ["Suitcase Carries (Single-Arm)", "Side Planks with Leg Abduction", "Pallof Press with Rotation Resistance", "Single-Leg Romanian Deadlifts"]
    },
    "hip_stability_moderate": {
        "category": "Pelvic Stability",
        "priority": "Medium",
        "observation": "Mild to moderate pelvic displacement during cyclic loading.",
        "action": "Incorporate single-leg stability exercises to stabilize the pelvic girdle under dynamic load.",
        "drills": ["Unilateral Hip Thrusts", "Standing Cable Hip Abduction", "Lateral Step-Ups"]
    },
    "trunk_lean_high": {
        "category": "Trunk & Spinal Alignment",
        "priority": "High",
        "observation": "Compensatory trunk lean observed relative to vertical axis.",
        "action": "Strengthen anterior and posterior core to resist excessive torso flexion and lateral shear forces.",
        "drills": ["Deadbugs with Resistance Band", "Bird-Dogs with 3s Pause", "Overhead Farmer's Walks", "Half-Kneeling Cable Chops"]
    },
    "trunk_lean_moderate": {
        "category": "Trunk Alignment",
        "priority": "Medium",
        "observation": "Moderate torso inclination detected during peak movement phases.",
        "action": "Reinforce upright posture awareness and thoracic extension.",
        "drills": ["Prone Cobras", "Wall Angels", "Farmer's Walks"]
    },
    "asymmetry_high": {
        "category": "Bilateral Movement Symmetry",
        "priority": "High",
        "observation": "Noticeable kinematic asymmetry detected between right and left sides.",
        "action": "Prioritize unilateral training to balance limb strength and range of motion without allowing the dominant side to compensate.",
        "drills": ["Bulgarian Split Squats", "Single-Arm Dumbbell Rows", "Single-Leg Box Jumps (Stick Landing)", "Unilateral Leg Press"]
    },
    "asymmetry_moderate": {
        "category": "Movement Symmetry",
        "priority": "Medium",
        "observation": "Mild to moderate bilateral discrepancies between limbs.",
        "action": "Address unilateral strength differences with targeted unilateral accessories.",
        "drills": ["Single-Leg Step-Ups", "Single-Leg Calf Raises", "Unilateral Cable Glute Kickbacks"]
    },
    "landing_mechanics_poor": {
        "category": "Landing & Impact Absorption",
        "priority": "High",
        "observation": "Stiff ground contact pattern detected with inadequate knee/hip flexion attenuation.",
        "action": "Train eccentric quadriceps and hip deceleration. Emphasize soft, quiet landings with deep hip and knee flexion to dissipate vertical ground reaction forces.",
        "drills": ["Snap Down to Athletic Stance", "Box Drop to Soft Landing", "Continuous Pogo to Stick Drills", "Depth Jumps with Soft Catch"]
    },
    "landing_mechanics_moderate": {
        "category": "Landing Mechanics",
        "priority": "Medium",
        "observation": "Sub-optimal impact absorption observed on landing.",
        "action": "Focus on deceleration mechanics and soft ground contact.",
        "drills": ["Box Step-Off to Stick Landing", "Broad Jump with Controlled Deceleration"]
    },
    "balance_poor": {
        "category": "Dynamic Balance & Proprioception",
        "priority": "High",
        "observation": "Elevated Center of Mass (COM) sway and reduced base-of-support stability.",
        "action": "Improve proprioception, ankle stabilizer recruitment, and vestibular integration.",
        "drills": ["Single-Leg Balance with Ball Toss", "Tandem Stance with Eye Tracking", "BOSU Ball Single-Leg Balances", "Clock Reach Drills"]
    },
    "optimal_maintenance": {
        "category": "Movement Maintenance",
        "priority": "Low",
        "observation": "Optimal biomechanical movement patterns demonstrated across kinematic metrics.",
        "action": "Maintain balanced kinetic chain function, multi-planar core stability, and progressive strength development.",
        "drills": ["Dynamic Kinetic Chain Warm-up", "Full-Body Mobility Flow", "Multi-Planar Plyometric Jumps"]
    }
}
