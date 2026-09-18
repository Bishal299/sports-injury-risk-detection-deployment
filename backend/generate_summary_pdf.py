import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Preformatted,
    HRFlowable,
    KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(36, 756, "Sports Injury Risk Detection System — Project Summary")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(36, 750, 576, 750)
            
        # Footer (all pages)
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.5)
        self.line(36, 40, 576, 40)
        
        footer_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(576, 28, footer_text)
        self.drawString(36, 28, "CONFIDENTIAL & PROPRIETARY — ACADEMIC / MENTOR PRESENTATION")
        self.restoreState()


def generate_summary_pdf(output_pdf_path: str):
    os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)

    doc = SimpleDocTemplate(
        output_pdf_path,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=46,
        bottomMargin=46
    )

    # Color palette
    c_primary = colors.HexColor("#1e3a8a")     # Deep Navy
    c_secondary = colors.HexColor("#0284c7")   # Bright Blue / Sky
    c_dark = colors.HexColor("#0f172a")        # Slate 900
    c_muted = colors.HexColor("#475569")       # Slate 600
    c_card_bg = colors.HexColor("#f8fafc")     # Slate 50
    c_border = colors.HexColor("#cbd5e1")      # Slate 300
    c_code_bg = colors.HexColor("#f1f5f9")     # Slate 100
    c_code_border = colors.HexColor("#94a3b8") # Slate 400

    styles = getSampleStyleSheet()

    doc_title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=c_primary,
        spaceAfter=3
    )

    doc_subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        textColor=c_secondary,
        textTransform="uppercase",
        spaceAfter=4
    )

    h1_style = ParagraphStyle(
        "Heading1_Custom",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=c_primary,
        spaceBefore=10,
        spaceAfter=5
    )

    h2_style = ParagraphStyle(
        "Heading2_Custom",
        parent=styles["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=13.5,
        textColor=c_secondary,
        spaceBefore=7,
        spaceAfter=3
    )

    body_style = ParagraphStyle(
        "Body_Custom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11.5,
        textColor=c_dark
    )

    body_bold = ParagraphStyle(
        "BodyBold_Custom",
        parent=body_style,
        fontName="Helvetica-Bold"
    )

    bullet_style = ParagraphStyle(
        "Bullet_Custom",
        parent=body_style,
        leftIndent=12,
        firstLineIndent=-8,
        spaceAfter=2
    )

    sub_bullet_style = ParagraphStyle(
        "SubBullet_Custom",
        parent=body_style,
        leftIndent=24,
        firstLineIndent=-8,
        spaceAfter=1.5
    )

    diagram_style = ParagraphStyle(
        "Diagram_Custom",
        fontName="Courier",
        fontSize=7.2,
        leading=8.8,
        textColor=colors.HexColor("#1e293b")
    )

    story = []

    # -------------------------------------------------------------
    # 1. HEADER BANNER
    # -------------------------------------------------------------
    story.append(Paragraph("SPORTS INJURY RISK DETECTION SYSTEM", doc_subtitle_style))
    story.append(Paragraph("Executive Progress & Implementation Summary", doc_title_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_secondary, spaceBefore=2, spaceAfter=8))

    # -------------------------------------------------------------
    # 2. OVERVIEW & TECH STACK (2-COLUMN TABLE)
    # -------------------------------------------------------------
    col1_content = [
        Paragraph("<b>📌 Project Overview</b>", h2_style),
        Paragraph("• <b>Goal:</b> Real-time video-based biomechanical movement analysis and injury risk screening from standard 2D smartphone/broadcast video (eliminating the need for $100k+ motion-capture labs).", bullet_style),
        Paragraph("• <b>Current Status:</b> Fully operational end-to-end pipeline (Video Upload ➔ MediaPipe Landmark Extraction ➔ Kinematic Analysis ➔ Risk Scoring).", bullet_style)
    ]

    col2_content = [
        Paragraph("<b>🛠️ Technology Stack</b>", h2_style),
        Paragraph("• <b>Backend:</b> Python 3.11, FastAPI, SQLAlchemy, PostgreSQL, OpenCV, MediaPipe Pose, ReportLab, NumPy", bullet_style),
        Paragraph("• <b>Frontend:</b> React 18, Vite, Lucide Icons, Vanilla CSS", bullet_style),
        Paragraph("• <b>Infrastructure:</b> Docker, Docker Compose", bullet_style)
    ]

    meta_table = Table([[col1_content, col2_content]], colWidths=[270, 270])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), c_card_bg),
        ('BOX', (0, 0), (-1, -1), 1, c_border),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 8))

    # -------------------------------------------------------------
    # 3. END-TO-END PIPELINE DIAGRAM
    # -------------------------------------------------------------
    story.append(Paragraph("🚀 What Has Been Done & How It Is Implemented", h1_style))

    ascii_diagram = """[Uploaded 2D Video]
        │
        ▼
[OpenCV VideoReader] ──► Extracts metadata (FPS, duration, resolution)
        │
        ▼
[MediaPipe Pose] ───────► Extracts 33 landmarks per frame (x, y, z, visibility)
        │
        ▼
[Validity Filter] ─────► Masks low-confidence frames; preserves frame indices & timestamps
        │
        ▼
[10 Kinematic Modules] ─► Computes angles, valgus, pelvic tilt, lean, balance, forces
        │
        ▼
[Rule-Based Risk Engine]► Weighted combination (38.9% Bio, 22.2% Hist, 22.2% Asym, 16.7% Load)
        │
        ├──► [Side-by-Side Dual Player] (Original Video + Skeleton Overlay)
        ├──► [Interactive SVG Charts] (Continuous angle trajectories over time)
        ├──► [38-Col Time-Series CSV] (Frame-by-frame scientific kinematic metrics)
        └──► [2-Page Vector Clinical PDF] (Demographics, risk score, ROM, drills)"""

    diag_flow = Preformatted(ascii_diagram, diagram_style)
    diag_table = Table([[diag_flow]], colWidths=[540])
    diag_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), c_code_bg),
        ('BOX', (0, 0), (-1, -1), 1, c_code_border),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(diag_table)
    story.append(Spacer(1, 8))

    # -------------------------------------------------------------
    # 4. IMPLEMENTATION MODULES
    # -------------------------------------------------------------

    # Module 1
    story.append(Paragraph("1. Authentication & Athlete Profile System", h2_style))
    story.append(Paragraph("• <b>What was done:</b> User registration, login, JWT authorization, Google OAuth, and athlete profiling.", bullet_style))
    story.append(Paragraph("• <b>How it works:</b> Uses FastAPI dependencies with bcrypt-hashed passwords in PostgreSQL. Stores athlete demographics (sport, position, age, height, weight) and baseline metrics (training load, flexibility, strength, endurance) alongside historical injury logs. Athlete height and weight are passed dynamically into the biomechanics engine (no hardcoded defaults).", bullet_style))
    story.append(Spacer(1, 4))

    # Module 2
    story.append(Paragraph("2. Video Ingestion & Skeleton Preprocessing", h2_style))
    story.append(Paragraph("• <b>What was done:</b> Multi-format video upload (.mp4, .mov, .avi, .mkv), metadata detection, and landmark tracking.", bullet_style))
    story.append(Paragraph("• <b>How it works:</b> OpenCV VideoReader streams frames and extracts FPS and duration. MediaPipe Pose Landmarker tracks 33 full-body anatomical landmarks. Implements skeleton validity evaluation checking left leg (23, 25, 27), right leg (24, 26, 28), trunk (11, 12, 23, 24), and pelvis (23, 24) with visibility threshold ≥ 0.5. <b>Zero hallucination:</b> Occluded joints are masked as None; original frame numbers and timestamps are strictly preserved.", bullet_style))
    story.append(Spacer(1, 4))

    # Module 3 (Keep together if possible)
    m3_story = [
        Paragraph("3. Deep Biomechanical Kinematics Engine (10 Modules)", h2_style),
        Paragraph("• <b>What was done:</b> 10 quantitative movement analysis modules located in backend/app/services/movement/:", bullet_style),
        Paragraph("1. <b>Joint Angles & ROM:</b> Vector dot-product calculation of flexion/extension for 8 bilateral joints (knees, hips, ankles, shoulders, elbows) across time (min, max, mean, ROM).", sub_bullet_style),
        Paragraph("2. <b>Frontal Knee Valgus:</b> Normalized medial knee displacement: <i>d_norm = |Knee_x - Midpoint(Hip_x, Ankle_x)| / Thigh_Length</i>.", sub_bullet_style),
        Paragraph("3. <b>Pelvic & Hip Stability:</b> Quantifies pelvic tilt angle relative to horizontal plane and evaluates Trendelenburg drop / lateral sway.", sub_bullet_style),
        Paragraph("4. <b>Trunk Inclination:</b> Angular deviation of the shoulder-hip spinal vector from vertical in sagittal and frontal planes.", sub_bullet_style),
        Paragraph("5. <b>Landing Shock Absorption:</b> Evaluates knee flexion buffering angle during ground contact impact to detect dangerous stiff landings.", sub_bullet_style),
        Paragraph("6. <b>Stride & Locomotion:</b> Calculates normalized stride length (scaled by leg length), cadence, and stride length asymmetry.", sub_bullet_style),
        Paragraph("7. <b>Dynamic Balance & COM:</b> Approximates 2D Center of Mass (torso/pelvic midpoint) and measures lateral sway standard deviation.", sub_bullet_style),
        Paragraph("8. <b>Kinematic Joint Alignment:</b> Measures hip-knee-ankle collinearity and kinetic chain alignment.", sub_bullet_style),
        Paragraph("9. <b>Bilateral Movement Symmetry:</b> Calculates percentage limb-to-limb difference across joint ranges of motion and valgus.", sub_bullet_style),
        Paragraph("10. <b>Visual Ground Reaction Force Proxy:</b> Differentiates COM vertical velocity to obtain vertical acceleration <i>a_y(t)</i>, computing Newtonian force <i>F(t) = m(g + a_y(t))</i> using the athlete's real profile weight.", sub_bullet_style),
    ]
    story.extend(m3_story)
    story.append(Spacer(1, 6))

    # Module 4
    m4_story = [
        Paragraph("4. Transparent Rule-Based Risk Scoring Engine", h2_style),
        Paragraph("• <b>What was done:</b> Deterministic, explainable scoring engine.", bullet_style),
        Paragraph("• <b>How it works:</b>", bullet_style),
        Paragraph("— <b>Proportional Weight Redistribution:</b> Fatigue indicators disabled (0%). Unused 10% weight redistributed proportionally (W_i = W_i_orig / 90): Biomechanical Deviations: <b>38.89%</b> | Historical Injury: <b>22.22%</b> | Movement Asymmetry: <b>22.22%</b> | Training Load: <b>16.67%</b>.", sub_bullet_style),
        Paragraph("— <b>4-Tier Classification Matrix:</b> Low Risk (&lt;25), Moderate Risk (25–49.9), High Risk (50–74.9), Critical Risk (75–100).", sub_bullet_style),
        Paragraph("— <b>Affected Side Isolation:</b> Automatically isolates whether mechanical risk is on the Right limb, Left limb, or is Bilateral.", sub_bullet_style),
        Paragraph("— <b>Corrective Drill Catalog:</b> Maps identified dysfunctions to evidence-based drills (Banded squats, single-leg step-downs, suitcase carries).", sub_bullet_style),
    ]
    story.extend(m4_story)
    story.append(Spacer(1, 6))

    # Module 5 & 6
    m56_story = [
        Paragraph("5. Multi-Format Scientific Export Suite", h2_style),
        Paragraph("• <b>What was done:</b> Generating scientific deliverables:", bullet_style),
        Paragraph("1. <b>Skeleton Overlay Video:</b> OpenCV-rendered skeleton overlay ({video_id}_skeleton.mp4) color-coded by joint deviation severity.", sub_bullet_style),
        Paragraph("2. <b>Clinical 2-Page Vector PDF ({video_id}_report.pdf):</b> Generated via ReportLab containing athlete header banner, risk gauge card, 10-row kinematic table, joint ROM table, force proxy, corrective drills, and medical safety disclaimers.", sub_bullet_style),
        Spacer(1, 4),
        Paragraph("6. Interactive Frontend Analytics Dashboard", h2_style),
        Paragraph("• <b>What was done:</b> Single-page analysis workspace in React 18 (Analysis.jsx).", bullet_style),
        Paragraph("• <b>How it works:</b>", bullet_style),
        Paragraph("— <b>Synchronized Dual-Video Player:</b> Plays raw original video alongside the MediaPipe skeleton visualizer with synchronized play, pause, and seek controls.", sub_bullet_style),
        Paragraph("— <b>Interactive Time-Series SVG Charts:</b> Displays continuous angle curves across time with hover tooltips and dynamic scaling.", sub_bullet_style),
        Paragraph("— <b>Risk Breakdown Cards:</b> Highlights primary risk factors with severity badges and affected side tags.", sub_bullet_style),
    ]
    story.extend(m56_story)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF generated successfully at: {output_pdf_path}")
    return output_pdf_path


if __name__ == "__main__":
    out_path = sys.argv[1] if len(sys.argv) > 1 else "docs/PROJECT_SUMMARY.pdf"
    generate_summary_pdf(out_path)
