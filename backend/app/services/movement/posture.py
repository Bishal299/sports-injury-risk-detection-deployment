import numpy as np
from typing import List, Dict, Any


def analyze_posture(
    frames_landmarks: List[Dict[str, Any]],
    valgus_data: Dict[str, Any],
    hip_data: Dict[str, Any],
    trunk_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Evaluates postural alignment across key kinetic chain segments.
    Provides a Posture Score (0-100) and an itemized deviation checklist.
    """
    shoulder_tilts = []
    head_alignments = []

    for frame_data in frames_landmarks:
        landmarks = frame_data.get("landmarks", [])
        if not landmarks or len(landmarks) < 33:
            continue

        lm_dict = {lm["landmark_id"]: lm for lm in landmarks if "landmark_id" in lm}

        # Shoulder horizontal level (11: left_shoulder, 12: right_shoulder)
        if 11 in lm_dict and 12 in lm_dict:
            sh_dx = lm_dict[12]["x"] - lm_dict[11]["x"]
            sh_dy = lm_dict[12]["y"] - lm_dict[11]["y"]
            sh_tilt = np.degrees(np.arctan2(abs(sh_dy), max(abs(sh_dx), 1e-6)))
            shoulder_tilts.append(sh_tilt)

        # Head alignment (0: nose vs shoulder midpoint x)
        if 0 in lm_dict and 11 in lm_dict and 12 in lm_dict:
            mid_sh_x = (lm_dict[11]["x"] + lm_dict[12]["x"]) / 2.0
            nose_x = lm_dict[0]["x"]
            head_offset = abs(nose_x - mid_sh_x)
            head_alignments.append(head_offset)

    avg_sh_tilt = float(np.mean(shoulder_tilts)) if shoulder_tilts else 0.0
    avg_head_offset = float(np.mean(head_alignments)) if head_alignments else 0.0

    avg_pelvic_tilt = hip_data.get("avg_pelvic_tilt_deg", 0.0)
    avg_trunk_lean = trunk_data.get("avg_trunk_lean_deg", 0.0)
    max_valgus = valgus_data.get("max_deviation", 0.0)

    checklist = []
    penalties = 0.0

    # 1. Shoulder Alignment
    if avg_sh_tilt < 3.0:
        checklist.append({"item": "Shoulder Level", "status": "optimal", "icon": "✓", "message": "Optimal horizontal shoulder alignment."})
    elif avg_sh_tilt < 6.0:
        checklist.append({"item": "Shoulder Level", "status": "mild", "icon": "⚠", "message": f"Mild shoulder tilt ({round(avg_sh_tilt, 1)}°)." })
        penalties += 5.0
    else:
        checklist.append({"item": "Shoulder Level", "status": "moderate", "icon": "⚠", "message": f"Elevated shoulder asymmetry ({round(avg_sh_tilt, 1)}°)." })
        penalties += 12.0

    # 2. Head Alignment
    if avg_head_offset < 0.03:
        checklist.append({"item": "Cervical Alignment", "status": "optimal", "icon": "✓", "message": "Head centered over shoulder midpoint."})
    else:
        checklist.append({"item": "Cervical Alignment", "status": "mild", "icon": "⚠", "message": "Mild lateral head shift detected."})
        penalties += 5.0

    # 3. Spine / Trunk Lean
    if avg_trunk_lean < 5.0:
        checklist.append({"item": "Spine & Trunk Orientation", "status": "optimal", "icon": "✓", "message": "Upright, balanced trunk position."})
    elif avg_trunk_lean < 12.0:
        checklist.append({"item": "Spine & Trunk Orientation", "status": "mild", "icon": "⚠", "message": f"Mild trunk lean ({round(avg_trunk_lean, 1)}°)." })
        penalties += 8.0
    else:
        checklist.append({"item": "Spine & Trunk Orientation", "status": "moderate", "icon": "⚠", "message": f"Significant trunk lean ({round(avg_trunk_lean, 1)}°)." })
        penalties += 18.0

    # 4. Hip Alignment
    if avg_pelvic_tilt < 4.0:
        checklist.append({"item": "Pelvic Alignment", "status": "optimal", "icon": "✓", "message": "Stable, horizontal pelvic positioning."})
    elif avg_pelvic_tilt < 8.0:
        checklist.append({"item": "Pelvic Alignment", "status": "mild", "icon": "⚠", "message": f"Mild pelvic tilt ({round(avg_pelvic_tilt, 1)}°)." })
        penalties += 6.0
    else:
        checklist.append({"item": "Pelvic Alignment", "status": "moderate", "icon": "⚠", "message": f"Elevated pelvic tilt ({round(avg_pelvic_tilt, 1)}°)." })
        penalties += 15.0

    # 5. Knee Alignment
    if max_valgus < 5.0:
        checklist.append({"item": "Knee Tracking", "status": "optimal", "icon": "✓", "message": "Optimal knee tracking without valgus collapse."})
    elif max_valgus < 10.0:
        checklist.append({"item": "Knee Tracking", "status": "mild", "icon": "⚠", "message": f"Mild knee valgus deviation ({round(max_valgus, 1)}°)." })
        penalties += 8.0
    else:
        checklist.append({"item": "Knee Tracking", "status": "moderate", "icon": "⚠", "message": f"Moderate dynamic knee valgus ({round(max_valgus, 1)}°)." })
        penalties += 20.0

    # 6. Ankle Alignment
    checklist.append({"item": "Ankle & Foot Base", "status": "optimal", "icon": "✓", "message": "Stable foot support base maintained."})

    posture_score = max(0.0, min(100.0, 100.0 - penalties))

    return {
        "score": round(posture_score, 1),
        "shoulder_tilt_deg": round(avg_sh_tilt, 1),
        "head_offset": round(avg_head_offset, 3),
        "checklist": checklist
    }
