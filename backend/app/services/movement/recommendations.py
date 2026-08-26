from typing import Dict, Any, List


def generate_recommendations(
    valgus_data: Dict[str, Any],
    hip_data: Dict[str, Any],
    trunk_data: Dict[str, Any],
    symmetry_data: Dict[str, Any],
    landing_data: Dict[str, Any],
    posture_data: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Generates tailored, evidence-based movement recommendations from detected biomechanical deviations.
    Uses strict non-diagnostic, sports-science terminology.
    """
    recommendations = []

    # 1. Knee Valgus Check
    max_valgus = valgus_data.get("max_deviation", 0.0)
    if max_valgus >= 10.0:
        recommendations.append({
            "category": "Knee Mechanics & Neuromuscular Control",
            "priority": "High",
            "observation": f"Elevated dynamic knee valgus observed (peak deviation {max_valgus:.1f}°).",
            "action": "Incorporate hip abductor and gluteus medius strengthening (e.g., lateral band walks, clamshells, single-leg Romanian deadlifts). Focus on cues to keep knees aligned over toes during deceleration.",
            "drills": ["Banded Squats with External Cueing", "Single-Leg Step-Downs", "Monster Band Walks"]
        })
    elif max_valgus >= 5.0:
        recommendations.append({
            "category": "Knee Mechanics",
            "priority": "Medium",
            "observation": f"Mild knee valgus observed under loading ({max_valgus:.1f}°).",
            "action": "Maintain awareness of frontal knee tracking during jump landings and direction changes.",
            "drills": ["Mirror Squats for Visual Biofeedback", "Banded Glute Bridges"]
        })

    # 2. Hip Stability Check
    hip_score = hip_data.get("score", 85.0)
    avg_tilt = hip_data.get("avg_pelvic_tilt_deg", 0.0)
    if hip_score < 70.0 or avg_tilt >= 7.0:
        recommendations.append({
            "category": "Pelvic Stability & Core Integration",
            "priority": "High",
            "observation": f"Pelvic tilt and lateral hip displacement detected during movement (average tilt {avg_tilt:.1f}°).",
            "action": "Target lumbo-pelvic-hip complex stability. Emphasize anti-lateral flexion and gluteal engagement to reduce pelvic drop.",
            "drills": ["Suitcase Carries", "Side Planks with Leg Abduction", "Pallof Press with Rotation"]
        })

    # 3. Trunk Lean Check
    avg_trunk_lean = trunk_data.get("avg_trunk_lean_deg", 0.0)
    if avg_trunk_lean >= 10.0:
        recommendations.append({
            "category": "Trunk & Spinal Alignment",
            "priority": "Medium",
            "observation": f"Compensatory trunk lean observed ({avg_trunk_lean:.1f}° average inclination).",
            "action": "Strengthen anterior and posterior core to resist excessive torso flexion and shear forces.",
            "drills": ["Deadbugs with Resistance Band", "Bird-Dogs with Pause", "Overhead Farmer's Walks"]
        })

    # 4. Movement Symmetry Check
    symmetry_score = symmetry_data.get("overall_symmetry_score", 90.0)
    if symmetry_score < 80.0:
        recommendations.append({
            "category": "Bilateral Movement Symmetry",
            "priority": "High",
            "observation": f"Bilateral asymmetry observed ({symmetry_score:.1f}% symmetry index).",
            "action": "Prioritize unilateral training to balance limb strength and range of motion without compensation from the dominant side.",
            "drills": ["Bulgarian Split Squats", "Single-Arm Dumbbell Row", "Single-Leg Box Jumps"]
        })

    # 5. Landing Mechanics Check
    if landing_data.get("has_landing_data"):
        landing_score = landing_data.get("score", 80.0)
        if landing_score is not None and landing_score < 70.0:
            recommendations.append({
                "category": "Landing & Impact Absorption",
                "priority": "High",
                "observation": f"Stiff ground contact pattern detected (landing mechanics score {landing_score:.1f}/100).",
                "action": "Train eccentric quad and hip deceleration. Emphasize soft, quiet landings with deep hip and knee flexion to dissipate impact forces.",
                "drills": ["Snap Down to Athletic Stance", "Box Drop to Soft Landing", "Continuous Pogo to Stick Drills"]
            })

    # Default general recommendation if everything is optimal
    if not recommendations:
        recommendations.append({
            "category": "Movement Maintenance",
            "priority": "Low",
            "observation": "Optimal biomechanical movement patterns demonstrated across kinematic parameters.",
            "action": "Continue structured mobility, multi-planar core stability, and progressive strength training.",
            "drills": ["Dynamic Warm-up Routines", "Full Kinetic Chain Mobility Flow"]
        })

    return recommendations
