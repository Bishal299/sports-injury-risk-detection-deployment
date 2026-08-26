import os
import cv2
from datetime import datetime
from uuid import UUID
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.video import Video
from app.models.athlete import Athlete
from app.models.analysis_result import AnalysisResult

from app.services.video_reader import VideoReader
from app.services.pose_detector import PoseDetector
from app.services.landmark_extractor import extract_landmarks

from app.services.movement.joint_angles import calculate_joint_angles
from app.services.movement.knee_valgus import analyze_knee_valgus
from app.services.movement.hip_stability import analyze_hip_stability
from app.services.movement.trunk_analysis import analyze_trunk_lean
from app.services.movement.landing_analysis import analyze_landing_mechanics
from app.services.movement.stride_analysis import analyze_stride
from app.services.movement.balance import analyze_balance
from app.services.movement.posture import analyze_posture
from app.services.movement.joint_alignment import analyze_joint_alignment
from app.services.movement.symmetry import analyze_symmetry
from app.services.movement.force_estimation import estimate_visual_forces
from app.services.movement.recommendations import generate_recommendations
from app.services.movement.skeleton_renderer import render_skeleton_video
from app.services.reports.csv_generator import generate_csv_report
from app.services.reports.pdf_generator import generate_pdf_report


BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
MODEL_PATH = "models/pose_landmarker_lite.task"
UPLOAD_DIR = "uploads"
SKELETON_DIR = "uploads/analysis/skeleton"
REPORTS_DIR = "uploads/analysis/reports"


def run_movement_analysis_pipeline(video_id: UUID):
    """
    Main asynchronous pipeline for sports movement analysis.
    Executes in FastAPI BackgroundTasks with real-time stage & progress updates.
    """
    db: Session = SessionLocal()
    try:
        # 1. Fetch video and athlete record
        video = db.query(Video).filter(Video.video_id == video_id).first()
        if not video:
            print(f"Error: Video {video_id} not found.")
            return

        athlete = db.query(Athlete).filter(Athlete.athlete_id == video.athlete_id).first()
        athlete_name = athlete.user.name if athlete and athlete.user else "Athlete"
        athlete_weight = float(athlete.weight) if athlete and athlete.weight else 70.0

        # 2. Get or create AnalysisResult record
        analysis = db.query(AnalysisResult).filter(AnalysisResult.video_id == video_id).first()
        if not analysis:
            analysis = AnalysisResult(
                video_id=video.video_id,
                athlete_id=video.athlete_id,
                status="processing",
                progress=5,
                stage="Preparing video..."
            )
            db.add(analysis)
        else:
            analysis.status = "processing"
            analysis.progress = 5
            analysis.stage = "Preparing video..."
            analysis.error_message = None

        db.commit()
        db.refresh(analysis)

        # 3. Locate source video file
        filename = os.path.basename(video.video_url)
        video_path = os.path.join("uploads/videos", filename)

        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found at {video_path}")

        # Update progress: 15%
        analysis.progress = 15
        analysis.stage = "Detecting pose landmarks..."
        db.commit()

        # 4. Extract frames & Run MediaPipe Pose Detection
        reader = VideoReader(video_path)
        fps = reader.fps if reader.fps and reader.fps > 0 else 30.0
        detector = PoseDetector(MODEL_PATH)

        frames_landmarks = []
        frame_idx = 0

        for frame in reader.frames():
            timestamp_ms = int((frame_idx / fps) * 1000)
            results = detector.detect(frame, timestamp_ms)
            landmarks = extract_landmarks(results)

            if landmarks:
                frames_landmarks.append({
                    "frame_number": frame_idx,
                    "timestamp_ms": timestamp_ms,
                    "landmarks": landmarks
                })
            else:
                frames_landmarks.append({
                    "frame_number": frame_idx,
                    "timestamp_ms": timestamp_ms,
                    "landmarks": []
                })

            frame_idx += 1

        reader.release()
        detector.close()

        if not frames_landmarks or len(frames_landmarks) < 5:
            raise ValueError("Insufficient pose landmarks detected in video.")

        # Update progress: 35%
        analysis.progress = 35
        analysis.stage = "Calculating joint angles & kinematics..."
        db.commit()

        # 5. Calculate Kinematic Metrics
        # Joint angles & ROM
        joint_data = calculate_joint_angles(frames_landmarks)

        # Knee Valgus
        valgus_data = analyze_knee_valgus(frames_landmarks)

        # Hip Stability
        hip_data = analyze_hip_stability(frames_landmarks)

        # Trunk Lean
        analysis.progress = 50
        analysis.stage = "Analyzing movement symmetry & balance..."
        db.commit()
        trunk_data = analyze_trunk_lean(frames_landmarks)

        # Landing Mechanics
        landing_data = analyze_landing_mechanics(frames_landmarks, joint_data, valgus_data)

        # Stride Kinematics
        stride_data = analyze_stride(frames_landmarks)

        # Balance & Center of Mass Sway
        balance_data = analyze_balance(frames_landmarks)

        # Posture Assessment
        posture_data = analyze_posture(frames_landmarks, valgus_data, hip_data, trunk_data)

        # Joint Alignment Table
        alignment_data = analyze_joint_alignment(joint_data, valgus_data, hip_data, posture_data)

        # Movement Symmetry
        symmetry_data = analyze_symmetry(joint_data, valgus_data, hip_data, stride_data, balance_data)

        # Visual Force Proxy Estimation
        force_data = estimate_visual_forces(balance_data, fps=fps, athlete_weight_kg=athlete_weight)

        # Targeted Recommendations
        recommendations_list = generate_recommendations(
            valgus_data,
            hip_data,
            trunk_data,
            symmetry_data,
            landing_data,
            posture_data
        )

        # 6. Composite Score & Risk Classification
        k_score = valgus_data.get("score", 85.0)
        h_score = hip_data.get("score", 85.0)
        t_score = trunk_data.get("score", 85.0)
        sym_score = symmetry_data.get("overall_symmetry_score", 90.0)
        bal_score = balance_data.get("score", 85.0)
        post_score = posture_data.get("score", 90.0)
        align_score = alignment_data.get("score", 90.0)

        # Overall Movement Quality Score (0 to 100)
        movement_quality = round(
            k_score * 0.22 +
            h_score * 0.18 +
            t_score * 0.12 +
            sym_score * 0.18 +
            bal_score * 0.12 +
            post_score * 0.10 +
            align_score * 0.08,
            1
        )

        # Risk Score (0 = lowest risk, 100 = highest risk)
        overall_risk_score = round(max(0.0, min(100.0, 100.0 - movement_quality)), 1)

        if overall_risk_score <= 20.0:
            risk_level = "Low Risk"
        elif overall_risk_score <= 40.0:
            risk_level = "Moderate Risk"
        elif overall_risk_score <= 65.0:
            risk_level = "Elevated Risk"
        else:
            risk_level = "High Risk"

        # 7. Render Skeleton Overlay Video
        analysis.progress = 75
        analysis.stage = "Generating skeleton video..."
        db.commit()

        os.makedirs(SKELETON_DIR, exist_ok=True)
        skeleton_filename = f"{video_id}_skeleton.mp4"
        skeleton_filepath = os.path.join(SKELETON_DIR, skeleton_filename)

        render_skeleton_video(
            source_video_path=video_path,
            output_video_path=skeleton_filepath,
            frames_landmarks=frames_landmarks,
            fps=fps
        )

        skeleton_video_url = f"{BACKEND_URL}/uploads/analysis/skeleton/{skeleton_filename}"

        # 8. Generate CSV & PDF Reports
        analysis.progress = 88
        analysis.stage = "Generating downloadable reports..."
        db.commit()

        os.makedirs(REPORTS_DIR, exist_ok=True)
        csv_filename = f"{video_id}_report.csv"
        csv_filepath = os.path.join(REPORTS_DIR, csv_filename)
        generate_csv_report(
            output_csv_path=csv_filepath,
            joint_data=joint_data,
            valgus_data=valgus_data,
            hip_data=hip_data,
            trunk_data=trunk_data,
            balance_data=balance_data,
            force_data=force_data
        )
        csv_report_url = f"{BACKEND_URL}/uploads/analysis/reports/{csv_filename}"

        pdf_filename = f"{video_id}_report.pdf"
        pdf_filepath = os.path.join(REPORTS_DIR, pdf_filename)

        athlete_meta = {
            "name": athlete_name,
            "sport": athlete.sport if athlete and athlete.sport else "General",
            "position": athlete.position if athlete and athlete.position else "Athlete"
        }
        video_meta = {
            "activity": video.activity or "Training Session",
            "fps": fps,
            "duration": video.duration or (frame_idx / fps)
        }
        summary_payload = {
            "joint_angles": joint_data,
            "knee_valgus": valgus_data,
            "hip_stability": hip_data,
            "trunk_lean": trunk_data,
            "landing": landing_data,
            "stride": stride_data,
            "balance": balance_data,
            "posture": posture_data,
            "alignment": alignment_data,
            "symmetry": symmetry_data,
            "force_estimation": force_data
        }

        generate_pdf_report(
            output_pdf_path=pdf_filepath,
            athlete_info=athlete_meta,
            video_info=video_meta,
            analysis_id=str(analysis.analysis_id),
            overall_score=movement_quality,
            risk_level=risk_level,
            summary_metrics=summary_payload,
            recommendations=recommendations_list
        )
        pdf_report_url = f"{BACKEND_URL}/uploads/analysis/reports/{pdf_filename}"

        # 9. Commit Completed Analysis to Database
        analysis.knee_valgus = float(valgus_data.get("max_deviation", 0.0))
        analysis.hip_stability = float(hip_data.get("score", 85.0))
        analysis.trunk_lean = float(trunk_data.get("avg_trunk_lean_deg", 0.0))
        analysis.stride_length = float(stride_data.get("normalized_stride_length", 0.0))
        analysis.joint_alignment = float(align_score)
        analysis.symmetry_score = float(sym_score)
        analysis.fatigue_score = round(max(10.0, 100.0 - (hip_data.get("tilt_variation_std", 0.0) * 15.0)), 1)
        analysis.movement_quality = float(movement_quality)
        analysis.overall_risk_score = float(overall_risk_score)
        analysis.risk_level = risk_level

        analysis.skeleton_video_url = skeleton_video_url
        analysis.csv_report_url = csv_report_url
        analysis.pdf_report_url = pdf_report_url

        analysis.summary_metrics = summary_payload
        analysis.time_series_data = {
            "timeline": joint_data.get("timeline", []),
            "joints": joint_data.get("time_series", {}),
            "valgus": valgus_data.get("time_series", {}),
            "hip": hip_data.get("time_series", {}),
            "trunk": trunk_data.get("time_series", {}),
            "balance": balance_data.get("time_series", {}),
            "force": force_data.get("time_series_force", [])
        }
        analysis.recommendations = recommendations_list

        analysis.status = "completed"
        analysis.progress = 100
        analysis.stage = "Analysis complete"
        analysis.completed_at = datetime.utcnow()

        video.processing_status = "analyzed"
        db.commit()
        print(f"Analysis completed successfully for video {video_id}")

    except Exception as e:
        print(f"Error in movement analysis pipeline: {str(e)}")
        if analysis:
            analysis.status = "failed"
            analysis.progress = 0
            analysis.stage = "Processing failed"
            analysis.error_message = str(e)
            db.commit()
    finally:
        db.close()
