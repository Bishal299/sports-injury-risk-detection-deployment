import os
from datetime import datetime
from io import BytesIO
from typing import Dict, Any, List, Optional
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


def _safe_float(val: Any, default: Optional[float] = None) -> Optional[float]:
    """Safely cast value to float, handling None, empty strings, and invalid types."""
    if val is None or val == "":
        return default
    try:
        f = float(val)
        return f if (f == f and f != float("inf") and f != float("-inf")) else default
    except (ValueError, TypeError):
        return default


def _fmt_deg(val: Any, default: str = "N/A") -> str:
    """Safely formats a degree value, preventing NoneType format crashes."""
    f = _safe_float(val)
    return f"{f:.1f}°" if f is not None else default


def _fmt_score(val: Any, default: str = "N/A", max_score: int = 100) -> str:
    """Safely formats a score / max_score value, preventing NoneType format crashes."""
    f = _safe_float(val)
    return f"{f:.1f} / {max_score}" if f is not None else default


def _fmt_val(val: Any, decimals: int = 1, suffix: str = "", default: str = "N/A") -> str:
    """Safely formats a generic float with specified decimals and suffix."""
    f = _safe_float(val)
    return f"{f:.{decimals}f}{suffix}" if f is not None else default


def generate_pdf_report(
    output_pdf_path: str,
    athlete_info: Dict[str, Any],
    video_info: Dict[str, Any],
    analysis_id: str,
    summary_metrics: Dict[str, Any],
    risk_assessment: Optional[Dict[str, Any]] = None,
    overall_score: Optional[float] = None,
    risk_level: Optional[str] = None,
    recommendations: Optional[List[Dict[str, Any]]] = None
) -> str:
    """
    Generates a professional 2-page PDF Biomechanical Movement Analysis Report.
    Bulletproof against None / missing values for any landmark, angle, or metric.
    """
    os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)

    # Extract or compute risk assessment
    if risk_assessment is None and isinstance(summary_metrics, dict):
        risk_assessment = summary_metrics.get("risk_assessment")

    if risk_assessment is None:
        from app.services.risk_scoring import calculate_injury_risk
        risk_assessment = calculate_injury_risk(summary_metrics, athlete_info)

    risk_score_raw = _safe_float(risk_assessment.get("injury_risk_score") if isinstance(risk_assessment, dict) else None)
    if risk_score_raw is None:
        risk_score_raw = _safe_float(overall_score, 25.0)
    risk_score = float(risk_score_raw or 0.0)

    risk_cat = str(risk_assessment.get("risk_category") if isinstance(risk_assessment, dict) else (risk_level or "Low Risk"))
    quality_score_raw = _safe_float(risk_assessment.get("movement_quality_score") if isinstance(risk_assessment, dict) else None)
    if quality_score_raw is None:
        quality_score_raw = _safe_float(overall_score, max(0.0, 100.0 - risk_score))
    quality_score = float(quality_score_raw or 80.0)

    recs_list = (risk_assessment.get("recommendations") if isinstance(risk_assessment, dict) else None) or recommendations or []

    doc = SimpleDocTemplate(
        output_pdf_path,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Brand palette
    primary_color = colors.HexColor("#1e3a8a")   # Deep navy
    accent_color = colors.HexColor("#2563eb")    # Bright blue
    dark_text = colors.HexColor("#0f172a")       # Slate dark
    muted_text = colors.HexColor("#64748b")      # Slate muted
    light_bg = colors.HexColor("#f8fafc")        # Slate light
    card_border = colors.HexColor("#e2e8f0")     # Light gray border

    # Risk-based color
    if "Critical" in risk_cat:
        risk_color = colors.HexColor("#dc2626")  # Critical red
    elif "High" in risk_cat:
        risk_color = colors.HexColor("#ea580c")  # High orange-red
    elif "Moderate" in risk_cat:
        risk_color = colors.HexColor("#d97706")  # Moderate amber
    else:
        risk_color = colors.HexColor("#16a34a")  # Low green

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=primary_color
    )

    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        textColor=accent_color,
        textTransform="uppercase"
    )

    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=15,
        textColor=primary_color,
        spaceBefore=8,
        spaceAfter=4
    )

    body_style = ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=dark_text
    )

    bold_body = ParagraphStyle(
        "BoldBody",
        parent=body_style,
        fontName="Helvetica-Bold"
    )

    disclaimer_style = ParagraphStyle(
        "Disclaimer",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=7.5,
        leading=9.5,
        textColor=muted_text
    )

    story = []

    # =========================================================================
    # PAGE 1: HEADER BANNER
    # =========================================================================
    story.append(Paragraph("SPORTS INJURY RISK DETECTION SYSTEM", subtitle_style))
    story.append(Paragraph("Biomechanical Movement Analysis Report", title_style))
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=1.5, color=accent_color, spaceBefore=2, spaceAfter=8))

    # =========================================================================
    # PAGE 1: METADATA TABLE
    # =========================================================================
    athlete_name = athlete_info.get("name", "Athlete") if isinstance(athlete_info, dict) else "Athlete"
    sport = athlete_info.get("sport", "General Sports") if isinstance(athlete_info, dict) else "General Sports"
    position = athlete_info.get("position", "N/A") if isinstance(athlete_info, dict) else "N/A"
    video_title = video_info.get("activity", "Movement Test") if isinstance(video_info, dict) else "Movement Test"
    date_str = datetime.utcnow().strftime("%B %d, %Y")

    raw_fps = video_info.get("fps") if isinstance(video_info, dict) else None
    fps_val = f"{raw_fps}" if raw_fps is not None else "30"

    raw_dur = _safe_float(video_info.get("duration") if isinstance(video_info, dict) else None)
    duration_str = f"{raw_dur:.1f}s" if raw_dur is not None else "N/A"

    meta_data = [
        [
            Paragraph(f"<b>Athlete:</b> {athlete_name}", body_style),
            Paragraph(f"<b>Sport / Position:</b> {sport} ({position})", body_style),
        ],
        [
            Paragraph(f"<b>Video:</b> {video_title}", body_style),
            Paragraph(f"<b>Analysis Date:</b> {date_str}", body_style),
        ],
        [
            Paragraph(f"<b>Analysis ID:</b> {str(analysis_id)[:8]}...", body_style),
            Paragraph(f"<b>FPS / Duration:</b> {fps_val} fps / {duration_str}", body_style)
        ]
    ]

    meta_table = Table(meta_data, colWidths=[265, 275])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), light_bg),
        ('BOX', (0, 0), (-1, -1), 1, card_border),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, card_border),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 8))

    # =========================================================================
    # PAGE 1: INJURY RISK & STATUS SCORE CARD
    # =========================================================================
    score_data = [
        [
            Paragraph(
                f"<font size=26 color='{risk_color}'><b>{risk_score:.0f} / 100</b></font><br/>"
                f"<font size=9.5 color='#1e3a8a'><b>Injury Risk Score</b></font><br/>"
                f"<font size=8 color='#64748b'>Movement Quality: <b>{quality_score:.0f} / 100</b></font>",
                body_style
            ),
            Paragraph(
                f"<font size=14 color='{risk_color}'><b>Status: {risk_cat}</b></font><br/>"
                f"<font size=8.5 color='#334155'>Composite rule-based metric evaluating knee alignment, hip stability, bilateral symmetry, and landing mechanics.</font>",
                body_style
            )
        ]
    ]

    score_table = Table(score_data, colWidths=[190, 350])
    score_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#eff6ff")),
        ('BOX', (0, 0), (-1, -1), 1.5, accent_color),
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(score_table)
    story.append(Spacer(1, 8))

    # =========================================================================
    # PAGE 1: KINEMATIC & BIOMECHANICAL METRICS TABLE
    # =========================================================================
    story.append(Paragraph("Kinematic & Biomechanical Metrics", section_heading))
    valgus = summary_metrics.get("knee_valgus", {}) if isinstance(summary_metrics, dict) else {}
    hip = summary_metrics.get("hip_stability", {}) if isinstance(summary_metrics, dict) else {}
    trunk = summary_metrics.get("trunk_lean", {}) if isinstance(summary_metrics, dict) else {}
    stride = summary_metrics.get("stride", {}) if isinstance(summary_metrics, dict) else {}
    balance = summary_metrics.get("balance", {}) if isinstance(summary_metrics, dict) else {}
    landing = summary_metrics.get("landing", {}) if isinstance(summary_metrics, dict) else {}
    symmetry = summary_metrics.get("symmetry", {}) if isinstance(summary_metrics, dict) else {}
    posture = summary_metrics.get("posture", {}) if isinstance(summary_metrics, dict) else {}

    # Safe Knee Valgus formatting
    r_v_dict = valgus.get("right") if isinstance(valgus, dict) and isinstance(valgus.get("right"), dict) else {}
    l_v_dict = valgus.get("left") if isinstance(valgus, dict) and isinstance(valgus.get("left"), dict) else {}

    r_v_num = _safe_float(r_v_dict.get("max_deviation") if r_v_dict.get("max_deviation") is not None else r_v_dict.get("peak_normalized_valgus"))
    if r_v_num is not None:
        r_v_str = f"{r_v_num:.1f}° max deviation" if r_v_num > 1.0 else f"{r_v_num:.2f} norm deviation"
    else:
        r_v_str = "Optimal (No valgus)"

    l_v_num = _safe_float(l_v_dict.get("max_deviation") if l_v_dict.get("max_deviation") is not None else l_v_dict.get("peak_normalized_valgus"))
    if l_v_num is not None:
        l_v_str = f"{l_v_num:.1f}° max deviation" if l_v_num > 1.0 else f"{l_v_num:.2f} norm deviation"
    else:
        l_v_str = "Optimal (No valgus)"

    r_v_risk = str(r_v_dict.get("risk") or "Normal")
    l_v_risk = str(l_v_dict.get("risk") or "Normal")

    # Safe Hip Stability
    hip_score = _safe_float(hip.get("score") if isinstance(hip, dict) else None)
    hip_val_str = f"{hip_score:.1f} / 100" if hip_score is not None else "N/A"

    hip_avg_tilt = _safe_float(hip.get("avg_pelvic_tilt_deg") if isinstance(hip, dict) and hip.get("avg_pelvic_tilt_deg") is not None else (hip.get("mean_pelvic_tilt_deg") if isinstance(hip, dict) else None))
    hip_status = f"Avg tilt: {hip_avg_tilt:.1f}°" if hip_avg_tilt is not None else ("Optimal Alignment" if (hip_score and hip_score >= 80.0) else "Analyzed")

    # Safe Trunk Inclination
    trunk_avg = _safe_float(trunk.get("avg_trunk_lean_deg") if isinstance(trunk, dict) else None)
    trunk_max = _safe_float(trunk.get("max_trunk_lean_deg") if isinstance(trunk, dict) else None, trunk_avg)
    if trunk_avg is not None and trunk_max is not None:
        trunk_obs = f"{trunk_avg:.1f}° avg ({trunk_max:.1f}° peak)"
    elif trunk_avg is not None:
        trunk_obs = f"{trunk_avg:.1f}° avg"
    else:
        trunk_obs = "Optimal Alignment"
    trunk_status = str(trunk.get("predominant_direction", "Neutral") if isinstance(trunk, dict) else "Neutral")

    # Safe Bilateral Symmetry
    sym_score = _safe_float(symmetry.get("overall_symmetry_score") if isinstance(symmetry, dict) else None)
    if sym_score is not None:
        sym_obs = f"{sym_score:.1f}%"
        sym_status = "Optimal" if sym_score >= 85.0 else ("Mild Asymmetry" if sym_score >= 70.0 else "Significant Asymmetry")
    else:
        sym_obs = "N/A"
        sym_status = "Symmetric"

    # Safe Dynamic Balance
    bal_score = _safe_float(balance.get("score") if isinstance(balance, dict) else None)
    bal_obs = f"{bal_score:.1f} / 100" if bal_score is not None else "N/A"
    lat_sway = _safe_float(balance.get("lateral_sway_std") if isinstance(balance, dict) else None)
    bal_status = f"Lateral sway: {lat_sway:.3f}" if lat_sway is not None else str(balance.get("status", "Good") if isinstance(balance, dict) else "Good")

    # Safe Landing Mechanics
    has_landing = bool(landing.get("has_landing_data") if isinstance(landing, dict) else False)
    land_score = _safe_float(landing.get("score") if isinstance(landing, dict) else None)
    if has_landing and land_score is not None:
        landing_obs = f"{land_score:.1f} / 100"
        landing_status = str(landing.get("status", "Landing event analyzed"))
    elif has_landing:
        landing_obs = "Landing Tracked"
        landing_status = str(landing.get("status", "Landing event analyzed"))
    else:
        landing_obs = "Insufficient visual data"
        landing_status = "No landing event detected"

    # Safe Stride Length
    stride_norm = _safe_float(stride.get("normalized_stride_length") if isinstance(stride, dict) else None)
    stride_obs = f"{stride_norm:.2f} (norm)" if stride_norm is not None else "N/A"
    stride_asym = _safe_float(stride.get("stride_asymmetry_pct") if isinstance(stride, dict) else None)
    stride_status = f"Asymmetry: {stride_asym:.1f}%" if stride_asym is not None else "Symmetric"

    # Safe Posture Assessment
    posture_score = _safe_float(posture.get("score") if isinstance(posture, dict) else None)
    if posture_score is not None:
        posture_obs = f"{posture_score:.1f} / 100"
        posture_status = "Optimal Alignment" if posture_score >= 85.0 else "Minor Deviations Detected"
    else:
        posture_obs = "N/A"
        posture_status = "Optimal Alignment"

    metrics_rows = [
        ["Biomechanical Metric", "Observed Value", "Status / Classification"],
        ["Right Knee Valgus", r_v_str, r_v_risk],
        ["Left Knee Valgus", l_v_str, l_v_risk],
        ["Hip & Pelvic Stability", hip_val_str, hip_status],
        ["Trunk Inclination", trunk_obs, trunk_status],
        ["Bilateral Symmetry", sym_obs, sym_status],
        ["Dynamic Balance Score", bal_obs, bal_status],
        ["Landing Mechanics", landing_obs, landing_status],
        ["Normalized Stride Length", stride_obs, stride_status],
        ["Posture Assessment Score", posture_obs, posture_status]
    ]

    metrics_table = Table(metrics_rows, colWidths=[180, 200, 160])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, light_bg]),
        ('BOX', (0, 0), (-1, -1), 1, card_border),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, card_border),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(metrics_table)
    story.append(Spacer(1, 8))

    # =========================================================================
    # PAGE 1: JOINT ANGLES & RANGE OF MOTION (ROM)
    # =========================================================================
    story.append(Paragraph("Joint Angles & Range of Motion (ROM)", section_heading))
    joints_summary = summary_metrics.get("joint_angles", {}).get("summary", {}) if isinstance(summary_metrics, dict) and isinstance(summary_metrics.get("joint_angles"), dict) else {}

    joint_specs = [
        ("right_knee", "Right Knee"),
        ("left_knee", "Left Knee"),
        ("right_hip", "Right Hip"),
        ("left_hip", "Left Hip"),
        ("right_ankle", "Right Ankle"),
        ("left_ankle", "Left Ankle"),
        ("right_shoulder", "Right Shoulder"),
        ("left_shoulder", "Left Shoulder"),
    ]

    joint_rows = [["Joint", "Min Angle", "Max Angle", "Mean Angle", "Range of Motion (ROM)"]]
    for j_key, j_label in joint_specs:
        j_data = joints_summary.get(j_key) if isinstance(joints_summary, dict) else {}
        if not isinstance(j_data, dict):
            j_data = {}
        min_a = _fmt_deg(j_data.get("min_angle"))
        max_a = _fmt_deg(j_data.get("max_angle"))
        mean_a = _fmt_deg(j_data.get("avg_angle"))
        rom_a = _fmt_deg(j_data.get("rom"))
        joint_rows.append([j_label, min_a, max_a, mean_a, rom_a])

    joint_table = Table(joint_rows, colWidths=[140, 100, 100, 100, 100])
    joint_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, light_bg]),
        ('BOX', (0, 0), (-1, -1), 1, card_border),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, card_border),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(joint_table)

    # Clean Page Break between Page 1 and Page 2
    story.append(PageBreak())

    # =========================================================================
    # PAGE 2: ESTIMATED FORCE / VISUAL PROXY
    # =========================================================================
    force_data = (summary_metrics.get("force") if isinstance(summary_metrics, dict) else None) or (summary_metrics.get("force_estimation") if isinstance(summary_metrics, dict) else {})
    if not isinstance(force_data, dict):
        force_data = {}

    story.append(Paragraph("Estimated Force / Visual Proxy", section_heading))
    peak_f_num = _safe_float(force_data.get("peak_force_n"))
    peak_force_str = f"{peak_f_num:.1f} N" if peak_f_num is not None else "N/A"

    peak_bw_num = _safe_float(force_data.get("peak_force_bw"))
    peak_bw_str = f"({peak_bw_num:.2f}x Body Weight)" if peak_bw_num is not None else ""

    body_mass_num = _safe_float(force_data.get("estimated_body_mass_kg") or (athlete_info.get("weight") if isinstance(athlete_info, dict) else None), 70.0)
    body_mass_str = f"{body_mass_num:.1f} kg" if body_mass_num is not None else "70.0 kg"

    force_text = f"<b>Peak Estimated Force:</b> {peak_force_str} {peak_bw_str} | <b>Estimated Body Mass:</b> {body_mass_str}"
    story.append(Paragraph(force_text, body_style))
    story.append(Spacer(1, 3))
    disclaimer_text = force_data.get(
        "disclaimer",
        "This is an estimation derived from video-based movement data and is not equivalent to force-plate measurement."
    )
    story.append(Paragraph(f"<b>Note:</b> {disclaimer_text}", disclaimer_style))
    story.append(Spacer(1, 14))

    # =========================================================================
    # PAGE 2: TARGETED CORRECTIVE RECOMMENDATIONS
    # =========================================================================
    story.append(Paragraph("Targeted Corrective Recommendations", section_heading))
    if recs_list and isinstance(recs_list, list):
        for rec in recs_list[:4]:
            if not isinstance(rec, dict):
                continue
            prio = rec.get("priority", "Medium")
            rec_title = f"<b>[{prio} Priority] {rec.get('category', 'Exercise')}</b>"
            story.append(Paragraph(rec_title, bold_body))
            obs = rec.get("observation", "")
            if obs:
                story.append(Paragraph(f"• <b>Observation:</b> {obs}", body_style))
            act = rec.get("action", "")
            if act:
                story.append(Paragraph(f"• <b>Corrective Focus:</b> {act}", body_style))
            drills = rec.get("drills")
            if drills and isinstance(drills, list):
                story.append(Paragraph(f"• <b>Suggested Drills:</b> {', '.join(str(d) for d in drills)}", body_style))
            story.append(Spacer(1, 6))
    else:
        story.append(Paragraph("• <b>Optimal Movement:</b> Continue standard athletic maintenance and movement preparation drills.", body_style))

    story.append(Spacer(1, 14))

    # =========================================================================
    # PAGE 2: CLINICAL / SAFETY DISCLAIMER FOOTER
    # =========================================================================
    story.append(HRFlowable(width="100%", thickness=0.5, color=card_border, spaceBefore=6, spaceAfter=8))
    med_disclaimer = (
        "<b>Medical & Safety Disclaimer:</b> This video-based biomechanical movement analysis provides sports performance and injury risk indicators based on "
        "computer vision estimations. It is not a medical device and is not a substitute for clinical orthopedic examination, force-plate laboratory testing, or "
        "formal medical diagnosis. Athletes experiencing pain or discomfort should consult a qualified sports physician or physical therapist."
    )
    story.append(Paragraph(med_disclaimer, disclaimer_style))

    doc.build(story)
    return output_pdf_path


def generate_recovery_summary_pdf(
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
    def display(value: Any) -> str:
        if value is None or value == "":
            return "Not Available"
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d")
        return str(value)

    def table(rows):
        return Table(rows, colWidths=[170, 350])

    def analysis_score(analysis: Dict[str, Any]) -> Any:
        score = analysis.get("composite_risk_score")
        return score if score is not None else analysis.get("overall_risk_score")

    def metric_rows(title: str, analysis: Optional[Dict[str, Any]]):
        story.extend([Spacer(1, 8), Paragraph(title, styles["Heading2"])])
        if not analysis:
            story.append(Paragraph("Not Available", styles["Normal"]))
            return
        rows = [
            ["Analysis Date", display(analysis.get("completed_at") or analysis.get("analysis_date"))],
            ["Risk Score", display(analysis_score(analysis))],
            ["Risk Category", display(analysis.get("risk_category"))],
            ["Knee Valgus", display(analysis.get("knee_valgus"))],
            ["Hip Stability", display(analysis.get("hip_stability"))],
            ["Trunk Lean", display(analysis.get("trunk_lean"))],
            ["Stride", display(analysis.get("stride_length"))],
            ["Symmetry", display(analysis.get("symmetry_score"))],
            ["Movement Quality", display(analysis.get("movement_quality"))],
        ]
        story.append(table(rows))

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    movement_comparison = movement_comparison or {}
    physiotherapist_info = physiotherapist_info or {}
    rehabilitation_monitoring = rehabilitation_monitoring or {}
    risk_history = risk_history or []
    timeline = timeline or []

    story = [
        Paragraph("Physiotherapy Recovery Report", styles["Title"]),
        Spacer(1, 12),
        Paragraph("Athlete Information", styles["Heading2"]),
        Paragraph(f"Athlete: {athlete_profile.get('name') or 'Not Available'}", styles["Normal"]),
        Paragraph(f"Sport: {athlete_profile.get('sport') or 'Not Available'}", styles["Normal"]),
        Paragraph(f"Age: {athlete_profile.get('age') if athlete_profile.get('age') is not None else 'Not Available'}", styles["Normal"]),
        Spacer(1, 12),
        Paragraph("Physiotherapist Information", styles["Heading2"]),
        Paragraph(f"Name: {physiotherapist_info.get('name') or 'Not Available'}", styles["Normal"]),
        Paragraph(f"Email: {physiotherapist_info.get('email') or 'Not Available'}", styles["Normal"]),
        Paragraph(f"Organization: {physiotherapist_info.get('organization') or 'Not Available'}", styles["Normal"]),
        Paragraph(f"Specialization: {physiotherapist_info.get('specialization') or 'Not Available'}", styles["Normal"]),
        Spacer(1, 12),
        Paragraph("Risk Monitoring", styles["Heading2"]),
        table([
            ["Current Risk", risk_monitoring.get("current_risk") if risk_monitoring.get("current_risk") is not None else "Not Available"],
            ["Risk Category", risk_monitoring.get("risk_category") or "Not Available"],
            ["Previous Risk", risk_monitoring.get("previous_risk") if risk_monitoring.get("previous_risk") is not None else "No Previous Assessment"],
            ["Trend", risk_monitoring.get("risk_trend") or "Not Available"],
        ]),
    ]

    story.extend([Spacer(1, 12), Paragraph("Rehabilitation", styles["Heading2"])])
    if rehabilitation_plan:
        goals = rehabilitation_plan.goals if isinstance(rehabilitation_plan.goals, list) else []
        story.append(table([
            ["Context", rehabilitation_plan.injury_context or "Not Available"],
            ["Phase", rehabilitation_plan.current_phase or "Not Available"],
            ["Progress", f"{rehabilitation_plan.progress}%" if rehabilitation_plan.progress is not None else "Not Available"],
            ["Status", rehabilitation_plan.status or "Not Available"],
            ["Start Date", display(rehabilitation_plan.start_date)],
            ["Review Date", display(rehabilitation_plan.target_date)],
            ["Goals", ", ".join(goals) if goals else "Not Available"],
            ["Recent Assessment", rehabilitation_plan.recent_assessment or "Not Available"],
        ]))
    else:
        story.append(Paragraph("No Rehabilitation Plan", styles["Normal"]))

    story.extend([Spacer(1, 12), Paragraph("Activity Completion / Progress", styles["Heading2"])])
    story.append(table([
        ["Activity Completion", f"{rehabilitation_monitoring.get('completed_activity_count', 0)}/{rehabilitation_monitoring.get('activity_count', 0)}"],
        ["Calculated Progress", f"{rehabilitation_monitoring.get('calculated_progress')}%" if rehabilitation_monitoring.get("progress_available") else "Not Available"],
        ["Pending Activities", display(rehabilitation_monitoring.get("pending_activity_count"))],
        ["Recent Activity", display((rehabilitation_monitoring.get("recent_rehabilitation_activity") or {}).get("title"))],
        ["Next Review", display(rehabilitation_monitoring.get("next_review_date"))],
    ]))

    metric_rows("Initial Available Analysis", initial_analysis)
    metric_rows("Latest Available Analysis", latest_analysis)

    story.extend([Spacer(1, 12), Paragraph("Movement Correction", styles["Heading2"])])
    comparison_status = movement_comparison.get("comparison_status") or "Not Available"
    story.append(Paragraph(f"Comparison: {comparison_status}", styles["Normal"]))
    comparison_rows = [["Metric", "Initial", "Latest", "Change"]]
    for metric, values in (movement_comparison.get("comparison") or {}).items():
        comparison_rows.append([
            metric,
            values.get("initial", "Not Available"),
            values.get("latest", "Not Available"),
            values.get("change", "Not Available"),
        ])
    if len(comparison_rows) > 1:
        story.append(Table(comparison_rows))

    story.extend([Spacer(1, 12), Paragraph("Risk History", styles["Heading2"])])
    risk_rows = [["Date", "Risk Score", "Category"]]
    for item in risk_history:
        risk_rows.append([
            display(item.get("date")),
            display(item.get("risk_score")),
            display(item.get("risk_category")),
        ])
    story.append(Table(risk_rows) if len(risk_rows) > 1 else Paragraph("Not Available", styles["Normal"]))

    story.extend([Spacer(1, 12), Paragraph("Rehabilitation Timeline", styles["Heading2"])])
    timeline_rows = [["Date", "Event", "Type"]]
    for event in timeline[:12]:
        timeline_rows.append([
            display(event.get("date")),
            display(event.get("title")),
            display(event.get("type")),
        ])
    story.append(Table(timeline_rows) if len(timeline_rows) > 1 else Paragraph("Not Available", styles["Normal"]))

    if notes:
        story.extend([Spacer(1, 12), Paragraph("Physiotherapist Notes", styles["Heading2"])])
        for note in notes[:6]:
            story.append(Paragraph(f"{note.title or 'Note'}: {note.note}", styles["Normal"]))
    else:
        story.extend([Spacer(1, 12), Paragraph("Physiotherapist Notes", styles["Heading2"])])
        story.append(Paragraph("Not Available", styles["Normal"]))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def generate_research_report_pdf(report: Dict[str, Any]) -> bytes:
    def display(value: Any) -> str:
        if value is None or value == "":
            return "Not Available"
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d")
        if isinstance(value, float):
            return f"{value:.1f}"
        return str(value)

    def add_section(title: str):
        story.append(Spacer(1, 10))
        story.append(Paragraph(title, styles["Heading2"]))

    def add_table(rows: list[list[Any]], widths: Optional[list[int]] = None):
        if not rows:
            story.append(Paragraph("Not Available", styles["Normal"]))
            return
        table_obj = Table([[display(cell) for cell in row] for row in rows], colWidths=widths)
        table_obj.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#e2e8f0")),
            ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#e2e8f0")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(table_obj)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("Sports Scientist Research Report", styles["Title"]),
        Paragraph(display(report.get("title")), styles["Heading1"]),
        Spacer(1, 8),
    ]

    overview = report.get("overview") or {}
    add_section("Report Overview")
    add_table([
        ["Field", "Value"],
        ["Scope", overview.get("scope")],
        ["Date Range", overview.get("date_range")],
        ["Athletes", overview.get("athlete_count")],
        ["Analyses", overview.get("analysis_count")],
        ["Generated By", overview.get("created_by")],
        ["Generated At", overview.get("created_at")],
    ], [150, 370])

    add_section("Performance Summary")
    add_table(
        [["Metric", "Average", "Values"]] + [
            [item.get("label"), item.get("average"), item.get("count")]
            for item in report.get("performance_summary", [])
        ],
        [220, 120, 100],
    )

    add_section("Biomechanical Analysis")
    add_table(
        [["Metric", "Average", "Values"]] + [
            [item.get("label"), item.get("average"), item.get("count")]
            for item in report.get("biomechanical_analysis", [])
        ],
        [220, 120, 100],
    )

    add_section("Risk Analysis")
    risk = report.get("risk_analysis") or {}
    add_table(
        [["Risk Band", "Count", "Percentage"]] + [
            [item.get("category"), item.get("count"), item.get("percentage")]
            for item in risk.get("distribution", [])
        ],
        [160, 100, 120],
    )
    story.append(Spacer(1, 6))
    add_table(
        [["Recurring Factor", "Occurrences"]] + [
            [item.get("label"), item.get("count")]
            for item in risk.get("recurring_factors", [])
        ],
        [280, 120],
    )

    add_section("Observed Patterns")
    patterns = report.get("observed_patterns") or []
    if patterns:
        for pattern in patterns:
            story.append(Paragraph(f"<b>{display(pattern.get('title'))}</b>: {display(pattern.get('description'))}", styles["Normal"]))
    else:
        story.append(Paragraph("No repeated observed patterns were available for this scope.", styles["Normal"]))

    add_section("Analysis Methodology")
    story.append(Paragraph(display(report.get("methodology")), styles["Normal"]))

    add_section("Limitations / Disclaimer")
    story.append(Paragraph(display(report.get("disclaimer")), styles["Normal"]))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
