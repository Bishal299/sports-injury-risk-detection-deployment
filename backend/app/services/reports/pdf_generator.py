import os
from datetime import datetime
from typing import Dict, Any, List
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch


def generate_pdf_report(
    output_pdf_path: str,
    athlete_info: Dict[str, Any],
    video_info: Dict[str, Any],
    analysis_id: str,
    overall_score: float,
    risk_level: str,
    summary_metrics: Dict[str, Any],
    recommendations: List[Dict[str, Any]]
) -> str:
    """
    Generates a professional multi-page PDF movement analysis report.
    """
    os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)

    doc = SimpleDocTemplate(
        output_pdf_path,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Custom styles
    primary_color = colors.HexColor("#1e3a8a")   # Deep navy
    accent_color = colors.HexColor("#2563eb")    # Bright blue
    dark_text = colors.HexColor("#0f172a")       # Slate dark
    muted_text = colors.HexColor("#64748b")      # Slate muted
    light_bg = colors.HexColor("#f8fafc")        # Slate light
    card_border = colors.HexColor("#e2e8f0")

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
        fontSize=13,
        leading=16,
        textColor=primary_color,
        spaceBefore=10,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
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
        fontSize=8,
        leading=10,
        textColor=muted_text
    )

    story = []

    # 1. Header Banner
    story.append(Paragraph("SPORTS INJURY RISK DETECTION SYSTEM", subtitle_style))
    story.append(Paragraph("Biomechanical Movement Analysis Report", title_style))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1.5, color=accent_color, spaceBefore=2, spaceAfter=10))

    # 2. Metadata Table
    athlete_name = athlete_info.get("name", "Athlete")
    sport = athlete_info.get("sport", "General Sports")
    position = athlete_info.get("position", "N/A")
    video_title = video_info.get("activity", "Movement Test")
    date_str = datetime.utcnow().strftime("%B %d, %Y")

    meta_data = [
        [
            Paragraph("<b>Athlete:</b> " + athlete_name, body_style),
            Paragraph("<b>Sport / Position:</b> " + f"{sport} ({position})", body_style),
        ],
        [
            Paragraph("<b>Video:</b> " + str(video_title), body_style),
            Paragraph("<b>Analysis Date:</b> " + date_str, body_style),
        ],
        [
            Paragraph("<b>Analysis ID:</b> " + str(analysis_id)[:8] + "...", body_style),
            Paragraph("<b>FPS / Duration:</b> " + f"{video_info.get('fps', 30)} fps / {float(video_info.get('duration', 0.0)):.1f}s", body_style)
        ]
    ]

    meta_table = Table(meta_data, colWidths=[260, 280])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), light_bg),
        ('BOX', (0, 0), (-1, -1), 1, card_border),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, card_border),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # 3. Overall Score Card
    risk_color = colors.HexColor("#16a34a") if overall_score >= 80 else (colors.HexColor("#d97706") if overall_score >= 65 else colors.HexColor("#dc2626"))
    score_data = [
        [
            Paragraph(f"<font size=24><b>{overall_score:.0f} / 100</b></font><br/><font size=9 color='#64748b'>Overall Movement Quality Score</font>", body_style),
            Paragraph(f"<font size=14><b>Status: {risk_level}</b></font><br/><font size=8.5 color='#334155'>Composite metric based on knee alignment, hip stability, symmetry, and landing mechanics.</font>", body_style)
        ]
    ]
    score_table = Table(score_data, colWidths=[200, 340])
    score_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#eff6ff")),
        ('BOX', (0, 0), (-1, -1), 1.5, accent_color),
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(score_table)
    story.append(Spacer(1, 10))

    # 4. Movement Metrics Summary Table
    story.append(Paragraph("Kinematic & Biomechanical Metrics", section_heading))
    valgus = summary_metrics.get("knee_valgus", {})
    hip = summary_metrics.get("hip_stability", {})
    trunk = summary_metrics.get("trunk_lean", {})
    stride = summary_metrics.get("stride", {})
    balance = summary_metrics.get("balance", {})
    landing = summary_metrics.get("landing", {})
    symmetry = summary_metrics.get("symmetry", {})
    posture = summary_metrics.get("posture", {})

    metrics_rows = [
        ["Biomechanical Metric", "Observed Value", "Status / Classification"],
        ["Right Knee Valgus", f"{valgus.get('right', {}).get('max_deviation', 0):.1f}° max deviation", valgus.get('right', {}).get('risk', 'Normal')],
        ["Left Knee Valgus", f"{valgus.get('left', {}).get('max_deviation', 0):.1f}° max deviation", valgus.get('left', {}).get('risk', 'Normal')],
        ["Hip & Pelvic Stability", f"{hip.get('score', 85):.1f} / 100", f"Avg tilt: {hip.get('avg_pelvic_tilt_deg', 0):.1f}°"],
        ["Trunk Inclination", f"{trunk.get('avg_trunk_lean_deg', 0):.1f}° avg ({trunk.get('max_trunk_lean_deg', 0):.1f}° peak)", trunk.get('predominant_direction', 'Neutral')],
        ["Bilateral Symmetry", f"{symmetry.get('overall_symmetry_score', 90):.1f}%", "Optimal" if symmetry.get('overall_symmetry_score', 90) >= 85 else "Mild Asymmetry"],
        ["Dynamic Balance Score", f"{balance.get('score', 85):.1f} / 100", f"Lateral sway: {balance.get('lateral_sway_std', 0):.3f}"],
        ["Landing Mechanics", f"{landing.get('score', 'N/A')} / 100" if landing.get('has_landing_data') else "Insufficient visual data", landing.get('status', 'Analyzed')],
        ["Normalized Stride Length", f"{stride.get('normalized_stride_length', 0):.2f} (norm)", f"Asymmetry: {stride.get('stride_asymmetry_pct', 0):.1f}%"],
        ["Posture Assessment Score", f"{posture.get('score', 90):.1f} / 100", "Optimal Alignment" if posture.get('score', 90) >= 85 else "Minor Deviations Detected"]
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
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(metrics_table)
    story.append(Spacer(1, 10))

    # 5. Joint Angles & Range of Motion Table
    story.append(Paragraph("Joint Angles & Range of Motion (ROM)", section_heading))
    joints_summary = summary_metrics.get("joint_angles", {}).get("summary", {})

    joint_rows = [
        ["Joint", "Min Angle", "Max Angle", "Mean Angle", "Range of Motion (ROM)"],
        ["Right Knee", f"{joints_summary.get('right_knee', {}).get('min_angle', 0):.1f}°", f"{joints_summary.get('right_knee', {}).get('max_angle', 0):.1f}°", f"{joints_summary.get('right_knee', {}).get('avg_angle', 0):.1f}°", f"{joints_summary.get('right_knee', {}).get('rom', 0):.1f}°"],
        ["Left Knee", f"{joints_summary.get('left_knee', {}).get('min_angle', 0):.1f}°", f"{joints_summary.get('left_knee', {}).get('max_angle', 0):.1f}°", f"{joints_summary.get('left_knee', {}).get('avg_angle', 0):.1f}°", f"{joints_summary.get('left_knee', {}).get('rom', 0):.1f}°"],
        ["Right Hip", f"{joints_summary.get('right_hip', {}).get('min_angle', 0):.1f}°", f"{joints_summary.get('right_hip', {}).get('max_angle', 0):.1f}°", f"{joints_summary.get('right_hip', {}).get('avg_angle', 0):.1f}°", f"{joints_summary.get('right_hip', {}).get('rom', 0):.1f}°"],
        ["Left Hip", f"{joints_summary.get('left_hip', {}).get('min_angle', 0):.1f}°", f"{joints_summary.get('left_hip', {}).get('max_angle', 0):.1f}°", f"{joints_summary.get('left_hip', {}).get('avg_angle', 0):.1f}°", f"{joints_summary.get('left_hip', {}).get('rom', 0):.1f}°"],
        ["Right Ankle", f"{joints_summary.get('right_ankle', {}).get('min_angle', 0):.1f}°", f"{joints_summary.get('right_ankle', {}).get('max_angle', 0):.1f}°", f"{joints_summary.get('right_ankle', {}).get('avg_angle', 0):.1f}°", f"{joints_summary.get('right_ankle', {}).get('rom', 0):.1f}°"],
        ["Left Ankle", f"{joints_summary.get('left_ankle', {}).get('min_angle', 0):.1f}°", f"{joints_summary.get('left_ankle', {}).get('max_angle', 0):.1f}°", f"{joints_summary.get('left_ankle', {}).get('avg_angle', 0):.1f}°", f"{joints_summary.get('left_ankle', {}).get('rom', 0):.1f}°"],
        ["Right Shoulder", f"{joints_summary.get('right_shoulder', {}).get('min_angle', 0):.1f}°", f"{joints_summary.get('right_shoulder', {}).get('max_angle', 0):.1f}°", f"{joints_summary.get('right_shoulder', {}).get('avg_angle', 0):.1f}°", f"{joints_summary.get('right_shoulder', {}).get('rom', 0):.1f}°"],
        ["Left Shoulder", f"{joints_summary.get('left_shoulder', {}).get('min_angle', 0):.1f}°", f"{joints_summary.get('left_shoulder', {}).get('max_angle', 0):.1f}°", f"{joints_summary.get('left_shoulder', {}).get('avg_angle', 0):.1f}°", f"{joints_summary.get('left_shoulder', {}).get('rom', 0):.1f}°"],
    ]

    joint_table = Table(joint_rows, colWidths=[140, 100, 100, 100, 100])
    joint_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, light_bg]),
        ('BOX', (0, 0), (-1, -1), 1, card_border),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, card_border),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(joint_table)
    story.append(Spacer(1, 10))

    # 6. Force Estimation & Visual Proxy Section
    force_data = summary_metrics.get("force_estimation", {})
    story.append(Paragraph("Estimated Force / Visual Proxy", section_heading))
    force_text = f"<b>Peak Estimated Force:</b> {force_data.get('peak_force_n', 'N/A')} N ({force_data.get('peak_force_bw', 'N/A')}x Body Weight) | <b>Estimated Body Mass:</b> {force_data.get('estimated_body_mass_kg', 70)} kg"
    story.append(Paragraph(force_text, body_style))
    story.append(Spacer(1, 3))
    story.append(Paragraph("<b>Note:</b> " + force_data.get("disclaimer", "This is an estimation derived from video-based movement data and is not equivalent to force-plate measurement."), disclaimer_style))
    story.append(Spacer(1, 10))

    # 7. Recommendations Section
    story.append(Paragraph("Targeted Corrective Recommendations", section_heading))
    for rec in recommendations[:4]:
        rec_title = f"<b>[{rec.get('priority', 'Medium')} Priority] {rec.get('category', 'Exercise')}</b>"
        story.append(Paragraph(rec_title, bold_body))
        story.append(Paragraph(f"• <b>Observation:</b> {rec.get('observation', '')}", body_style))
        story.append(Paragraph(f"• <b>Corrective Focus:</b> {rec.get('action', '')}", body_style))
        if rec.get("drills"):
            story.append(Paragraph(f"• <b>Suggested Drills:</b> {', '.join(rec.get('drills', []))}", body_style))
        story.append(Spacer(1, 4))

    story.append(Spacer(1, 8))

    # 8. Clinical Disclaimer Footer
    story.append(HRFlowable(width="100%", thickness=0.5, color=card_border, spaceBefore=4, spaceAfter=6))
    med_disclaimer = (
        "<b>Medical & Safety Disclaimer:</b> This video-based biomechanical movement analysis provides sports performance and injury risk indicators based on computer vision estimations. "
        "It is not a medical device and is not a substitute for clinical orthopedic examination, force-plate laboratory testing, or formal medical diagnosis. "
        "Athletes experiencing pain or discomfort should consult a qualified sports physician or physical therapist."
    )
    story.append(Paragraph(med_disclaimer, disclaimer_style))

    doc.build(story)
    return output_pdf_path
