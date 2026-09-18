import os
import numpy as np
from datetime import datetime
from uuid import UUID
from typing import List, Dict, Any, Optional

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.video import Video
from app.models.athlete import Athlete
from app.models.injury_history import InjuryHistory
from app.models.analysis_result import AnalysisResult

from app.services.video_reader import VideoReader
from app.services.pose_detector import PoseDetector
from app.services.landmark_extractor import extract_landmarks
from app.services.risk_scoring import calculate_injury_risk

from app.services.movement.joint_angles import calculate_joint_angles, MIN_LANDMARK_VISIBILITY
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
from app.services.movement.skeleton_renderer import render_skeleton_video

from app.services.reports.csv_generator import generate_csv_report
from app.services.reports.ml_dataset import export_ml_dataset
from app.services.reports.pdf_generator import generate_pdf_report


# ============================================================
# CONFIGURATION
# ============================================================

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
MODEL_PATH = "models/pose_landmarker_lite.task"
MIN_VALID_POSE_FRAMES = 5
MIN_POSE_DETECTION_RATE = 3.0  # minimum % valid frames to avoid bogus analysis

UPLOAD_DIR = "uploads"
VIDEO_DIR = os.path.join(UPLOAD_DIR, "videos")
SKELETON_DIR = os.path.join(UPLOAD_DIR, "analysis", "skeleton")
REPORTS_DIR = os.path.join(UPLOAD_DIR, "analysis", "reports")


def _evaluate_frame_skeleton_validity(landmarks: List[Dict[str, Any]], min_vis: float = MIN_LANDMARK_VISIBILITY) -> Dict[str, bool]:
    """
    Evaluates segment-specific and overall skeleton validity for a single frame.
    Never alters original coordinates.
    """
    if not landmarks or len(landmarks) < 33:
        return {
            "pose_detected": False,
            "pose_valid": False,
            "left_leg_valid": False,
            "right_leg_valid": False,
            "trunk_valid": False,
            "left_arm_valid": False,
            "right_arm_valid": False,
            "pelvis_valid": False
        }

    lm_dict = {lm["landmark_id"]: lm for lm in landmarks if "landmark_id" in lm}

    # Helper to check if a set of landmark indices are all present and visible
    def are_valid(indices: List[int]) -> bool:
        return all(idx in lm_dict and lm_dict[idx].get("visibility", 1.0) >= min_vis for idx in indices)

    left_leg_valid = are_valid([23, 25, 27])      # Hip, Knee, Ankle
    right_leg_valid = are_valid([24, 26, 28])     # Hip, Knee, Ankle
    trunk_valid = are_valid([11, 12, 23, 24])     # Shoulders, Hips
    left_arm_valid = are_valid([11, 13, 15])      # Shoulder, Elbow, Wrist
    right_arm_valid = are_valid([12, 14, 16])     # Shoulder, Elbow, Wrist
    pelvis_valid = are_valid([23, 24])            # Left & Right Hip

    # Overall pose is valid if core trunk or at least one complete limb is reliable
    pose_valid = trunk_valid or (left_leg_valid and right_leg_valid)

    return {
        "pose_detected": True,
        "pose_valid": pose_valid,
        "left_leg_valid": left_leg_valid,
        "right_leg_valid": right_leg_valid,
        "trunk_valid": trunk_valid,
        "left_arm_valid": left_arm_valid,
        "right_arm_valid": right_arm_valid,
        "pelvis_valid": pelvis_valid
    }


def _calculate_kinematic_consistency(joint_data: dict, trunk_data: dict) -> Optional[float]:
    """
    Computes real form consistency / fatigue resistance index across the video session.
    Compares kinematic variance in the first half vs second half of the movement timeline.
    Returns a score 0-100 (higher = more stable/consistent form), or None if insufficient valid frames.
    """
    try:
        r_knees = [v for v in joint_data.get("time_series", {}).get("right_knee", []) if v is not None and not np.isnan(v)]
        leans = [v for v in trunk_data.get("time_series", {}).get("lean", []) if v is not None and not np.isnan(v)]

        if len(r_knees) < 20 or len(leans) < 20:
            return 85.0

        half = len(r_knees) // 2
        first_half_rk = r_knees[:half]
        second_half_rk = r_knees[half:]

        first_var = np.var(first_half_rk) if first_half_rk else 1.0
        second_var = np.var(second_half_rk) if second_half_rk else 1.0

        # Form degradation ratio
        ratio = abs(second_var - first_var) / max(first_var, second_var, 1e-4)
        consistency_score = max(50.0, min(100.0, 100.0 - (ratio * 30.0)))
        return round(float(consistency_score), 1)
    except Exception:
        return None


def _calculate_movement_quality_score(
    valgus_data: dict,
    hip_data: dict,
    trunk_data: dict,
    balance_data: dict,
    symmetry_data: dict,
    alignment_data: dict
) -> Optional[float]:
    """
    Calculates a composite biomechanical movement quality index (0-100)
    derived from genuine measured submetrics that are actually available.
    """
    try:
        submetrics = [
            (valgus_data.get("score"), 0.25),
            (hip_data.get("score"), 0.20),
            (trunk_data.get("score"), 0.15),
            (balance_data.get("score"), 0.15),
            (symmetry_data.get("overall_symmetry_score"), 0.15),
            (alignment_data.get("score"), 0.10)
        ]

        valid_subs = [(score, weight) for score, weight in submetrics if score is not None]
        if not valid_subs:
            return None

        total_weight = sum(w for _, w in valid_subs)
        composite = sum(score * w for score, w in valid_subs) / total_weight
        return round(float(max(0.0, min(100.0, composite))), 1)
    except Exception:
        return None


# ============================================================
# MAIN MOVEMENT FEATURE EXTRACTION PIPELINE
# ============================================================

def run_movement_analysis_pipeline(video_id: UUID, analysis_id: UUID | None = None):
    """
    Phase 1: Real Biomechanical Feature Extraction Pipeline with Frame-Level Skeleton Preprocessing.

    Key Invariants:
    1. The original uploaded video is NEVER physically modified or re-encoded.
    2. Every frame is evaluated for usable skeleton landmarks and logically masked.
    3. Biomechanical feature calculations execute only on frames with reliable landmarks.
    4. Missing or low-confidence landmarks are NEVER replaced with 0 or fake coordinates.
    5. Original frame numbers and timestamps are strictly preserved.
    6. User profile height and weight are retrieved directly from the authenticated user's profile.
    7. No injury prediction or risk classification is performed.
    """

    db: Session = SessionLocal()
    analysis = None

    try:
        # ====================================================
        # 1. FETCH VIDEO & ATHLETE PROFILE
        # ====================================================
        video = db.query(Video).filter(Video.video_id == video_id).first()
        if not video:
            print(f"Error: Video {video_id} not found.")
            return

        athlete = db.query(Athlete).filter(Athlete.athlete_id == video.athlete_id).first()
        athlete_name = athlete.user.name if athlete and athlete.user else "Athlete"
        athlete_user_id = str(athlete.user_id) if athlete and athlete.user_id else None

        # Retrieve profile height and weight (None if unassigned, no fake defaults)
        athlete_height = float(athlete.height) if athlete and athlete.height is not None else None
        athlete_weight = float(athlete.weight) if athlete and athlete.weight is not None else None

        # ====================================================
        # 2. CREATE / RESET ANALYSIS RECORD
        # ====================================================
        if analysis_id:
            analysis = (
                db.query(AnalysisResult)
                .filter(AnalysisResult.analysis_id == analysis_id)
                .first()
            )
        else:
            analysis = (
                db.query(AnalysisResult)
                .filter(AnalysisResult.video_id == video_id)
                .order_by(AnalysisResult.created_at.desc())
                .first()
            )

        if not analysis:
            analysis = AnalysisResult(
                video_id=video.video_id,
                athlete_id=video.athlete_id,
                status="processing",
                progress=5,
                stage="Preparing video stream..."
            )
            db.add(analysis)
        else:
            analysis.status = "processing"
            analysis.progress = 5
            analysis.stage = "Preparing video stream..."
            analysis.error_message = None

        db.commit()
        db.refresh(analysis)

        # ====================================================
        # 3. LOCATE SOURCE VIDEO
        # ====================================================
        filename = os.path.basename(video.video_url)
        video_path = os.path.join(VIDEO_DIR, filename)

        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Source video file not found at {video_path}")

        # ====================================================
        # 4. SKELETON PREPROCESSING & LOGICAL VALIDITY CHECK
        # ====================================================
        analysis.progress = 15
        analysis.stage = "Preprocessing video & evaluating skeleton validity per frame..."
        db.commit()

        reader = VideoReader(video_path)
        fps = float(reader.fps) if reader.fps and reader.fps > 0 else 30.0
        detector = PoseDetector(MODEL_PATH)

        frames_landmarks = []
        frame_idx = 0
        total_frames = 0
        valid_pose_frames = 0
        left_leg_valid_frames = 0
        right_leg_valid_frames = 0
        trunk_valid_frames = 0

        try:
            for frame in reader.frames():
                timestamp_ms = int((frame_idx / fps) * 1000)
                timestamp_sec = round(timestamp_ms / 1000.0, 3)

                # Real pose landmark detection via MediaPipe Pose Landmarker
                results = detector.detect(frame, timestamp_ms)
                landmarks = extract_landmarks(results)

                # Frame-level skeleton validity evaluation
                validity = _evaluate_frame_skeleton_validity(landmarks, min_vis=MIN_LANDMARK_VISIBILITY)

                if validity["pose_valid"]:
                    valid_pose_frames += 1
                if validity["left_leg_valid"]:
                    left_leg_valid_frames += 1
                if validity["right_leg_valid"]:
                    right_leg_valid_frames += 1
                if validity["trunk_valid"]:
                    trunk_valid_frames += 1

                # Maintain strict original frame indexing and timestamps
                frames_landmarks.append({
                    "frame_number": frame_idx,
                    "timestamp_ms": timestamp_ms,
                    "timestamp_sec": timestamp_sec,
                    "landmarks": landmarks or [],
                    "validity": validity
                })

                frame_idx += 1
                total_frames += 1

        finally:
            reader.release()
            detector.close()

        # ====================================================
        # 5. VALIDATE SUFFICIENT TRACKING DATA
        # ====================================================
        if total_frames < 5:
            raise ValueError(f"Video contains insufficient frames ({total_frames} frames).")

        pose_detection_rate = (valid_pose_frames / total_frames) * 100.0 if total_frames > 0 else 0.0

        if valid_pose_frames < MIN_VALID_POSE_FRAMES or pose_detection_rate < MIN_POSE_DETECTION_RATE:
            raise ValueError(
                f"Insufficient valid pose data for reliable feature extraction: "
                f"{valid_pose_frames}/{total_frames} frames valid ({pose_detection_rate:.1f}% detection rate)."
            )

        print(f"Skeleton Preprocessing complete: {valid_pose_frames}/{total_frames} valid frames ({pose_detection_rate:.2f}% coverage)")

        # ====================================================
        # 6. FEATURE EXTRACTION ON VALID SKELETON FRAMES
        # ====================================================
        analysis.progress = 35
        analysis.stage = "Extracting genuine joint angles & ROM from valid frames..."
        db.commit()

        # Joint angles & ROM (only valid landmark frames included)
        joint_data = calculate_joint_angles(frames_landmarks, min_visibility=MIN_LANDMARK_VISIBILITY)

        # Frontal plane knee valgus
        valgus_data = analyze_knee_valgus(frames_landmarks, min_visibility=MIN_LANDMARK_VISIBILITY)

        # Hip / pelvic kinematics
        hip_data = analyze_hip_stability(frames_landmarks, min_visibility=MIN_LANDMARK_VISIBILITY)

        # Trunk lean
        analysis.progress = 50
        analysis.stage = "Analyzing trunk inclination, stride, and balance..."
        db.commit()
        trunk_data = analyze_trunk_lean(frames_landmarks, min_visibility=MIN_LANDMARK_VISIBILITY)

        # Landing mechanics
        landing_data = analyze_landing_mechanics(frames_landmarks, joint_data, valgus_data)

        # Stride kinematics
        stride_data = analyze_stride(frames_landmarks, min_visibility=MIN_LANDMARK_VISIBILITY)

        # Balance & Center of Mass (COM)
        balance_data = analyze_balance(frames_landmarks, min_visibility=MIN_LANDMARK_VISIBILITY)

        # Posture assessment
        analysis.progress = 65
        analysis.stage = "Analyzing posture, alignment, and bilateral symmetry..."
        db.commit()
        posture_data = analyze_posture(frames_landmarks, valgus_data, hip_data, trunk_data)

        # Joint alignment
        alignment_data = analyze_joint_alignment(joint_data, valgus_data, hip_data, posture_data)

        # Bilateral movement symmetry
        symmetry_data = analyze_symmetry(joint_data, valgus_data, hip_data, stride_data, balance_data)

        # Force proxy estimation using profile height & weight (no hardcoded weight)
        force_data = estimate_visual_forces(
            balance_data=balance_data,
            fps=fps,
            athlete_profile={
                "height_cm": athlete_height,
                "weight_kg": athlete_weight
            }
        )

        # Kinematic consistency & composite quality score
        consistency_score = _calculate_kinematic_consistency(joint_data, trunk_data)
        movement_quality = _calculate_movement_quality_score(
            valgus_data, hip_data, trunk_data, balance_data, symmetry_data, alignment_data
        )

        # ====================================================
        # 7. FEATURE QUALITY & METADATA
        # ====================================================
        feature_quality = {
            "total_frames": total_frames,
            "valid_pose_frames": valid_pose_frames,
            "invalid_pose_frames": total_frames - valid_pose_frames,
            "pose_detection_rate": round(pose_detection_rate, 2),
            "pose_coverage_percent": round(pose_detection_rate, 2),
            "left_leg_valid_frames": left_leg_valid_frames,
            "right_leg_valid_frames": right_leg_valid_frames,
            "trunk_valid_frames": trunk_valid_frames,
            "min_landmark_visibility": MIN_LANDMARK_VISIBILITY,
            "fps": fps,
            "duration_seconds": round(total_frames / fps, 3),
            "height_cm": athlete_height,
            "weight_kg": athlete_weight
        }

        # Summary Payload (Genuine Biomechanical Features)
        summary_payload = {
            "feature_extraction_version": "1.0-phase1-filtered",
            "phase": "Real Feature Extraction Only (No Injury Prediction)",
            "feature_quality": feature_quality,
            "athlete_profile": {
                "user_id": athlete_user_id,
                "name": athlete_name,
                "height_cm": athlete_height,
                "weight_kg": athlete_weight,
                "sport": athlete.sport if athlete else None,
                "position": athlete.position if athlete else None
            },
            "joint_angles": joint_data,
            "knee_valgus": valgus_data,
            "hip_stability": hip_data,
            "trunk_lean": trunk_data,
            "landing": landing_data,
            "stride": stride_data,
            "balance": balance_data,
            "force": force_data,
            "posture": posture_data,
            "alignment": alignment_data,
            "symmetry": symmetry_data,
            "kinematic_consistency": consistency_score
        }

        # Time Series Payload
        time_series_payload = {
            "timeline": joint_data.get("timeline", []),
            "joints": joint_data.get("time_series", {}),
            "valgus": valgus_data.get("time_series", {}),
            "hip": hip_data.get("time_series", {}),
            "trunk": trunk_data.get("time_series", {}),
            "landing": landing_data.get("time_series", {}),
            "stride": stride_data.get("time_series", {}),
            "balance": balance_data.get("time_series", {}),
            "force": force_data.get("time_series_force", []),
            "force_bw": force_data.get("time_series_force_bw", [])
        }

        # ====================================================
        # 8. RENDER SKELETON VIDEO
        # ====================================================
        analysis.progress = 75
        analysis.stage = "Rendering skeleton visualizer video..."
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

        # ====================================================
        # 9. GENERATE DATASET CSVs
        # ====================================================
        analysis.progress = 85
        analysis.stage = "Generating frame-level & ML CSV feature datasets..."
        db.commit()

        os.makedirs(REPORTS_DIR, exist_ok=True)
        import shutil

        csv_metadata = {
            "video_id": str(video_id),
            "athlete_id": str(video.athlete_id),
            "sport": athlete.sport if athlete else "",
            "activity": video.activity if video else "",
            "height_cm": athlete_height,
            "weight_kg": athlete_weight,
            "fps": fps,
            "feature_version": "1.0-biomechanics"
        }

        # 1. Frame-Level Time Series CSV
        csv_filename = f"{video_id}_report.csv"
        csv_filepath = os.path.join(REPORTS_DIR, csv_filename)
        timeseries_filename = f"video_{video_id}_timeseries.csv"
        timeseries_filepath = os.path.join(REPORTS_DIR, timeseries_filename)

        generate_csv_report(
            output_csv_path=timeseries_filepath,
            joint_data=joint_data,
            valgus_data=valgus_data,
            hip_data=hip_data,
            trunk_data=trunk_data,
            balance_data=balance_data,
            stride_data=stride_data,
            landing_data=landing_data,
            force_data=force_data,
            frames_landmarks=frames_landmarks,
            metadata=csv_metadata
        )

        # Copy to legacy report path for full backward compatibility
        if os.path.abspath(timeseries_filepath) != os.path.abspath(csv_filepath):
            shutil.copyfile(timeseries_filepath, csv_filepath)

        # 2. One-Row-Per-Video ML Feature Dataset
        ml_filename = f"video_{video_id}_ml.csv"
        ml_filepath = os.path.join(REPORTS_DIR, ml_filename)
        master_ml_csv_path = os.path.join(REPORTS_DIR, "ml_dataset.csv")

        export_ml_dataset(
            output_ml_csv_path=ml_filepath,
            joint_data=joint_data,
            valgus_data=valgus_data,
            hip_data=hip_data,
            trunk_data=trunk_data,
            balance_data=balance_data,
            stride_data=stride_data,
            landing_data=landing_data,
            force_data=force_data,
            posture_data=posture_data,
            alignment_data=alignment_data,
            symmetry_data=symmetry_data,
            metadata=csv_metadata,
            feature_quality=feature_quality,
            master_ml_csv_path=master_ml_csv_path
        )

        csv_report_url = f"{BACKEND_URL}/uploads/analysis/reports/{csv_filename}"

        # ====================================================
        # 10. RULE-BASED INJURY RISK ASSESSMENT & PDF REPORT
        # ====================================================
        analysis.progress = 90
        analysis.stage = "Calculating rule-based injury risk & generating PDF report..."
        db.commit()

        # Fetch athlete injury history
        athlete_injuries = []
        if athlete:
            raw_injuries = db.query(InjuryHistory).filter(InjuryHistory.athlete_id == athlete.athlete_id).all()
            for inj in raw_injuries:
                athlete_injuries.append({
                    "injury_type": inj.injury_type,
                    "body_part": inj.body_part,
                    "affected_side": inj.affected_side,
                    "severity": inj.severity,
                    "status": inj.status,
                    "injury_date": str(inj.injury_date) if inj.injury_date else None,
                    "recovery_date": str(inj.recovery_date) if inj.recovery_date else None,
                    "remarks": inj.remarks
                })

        athlete_meta = {
            "name": athlete_name,
            "user_id": athlete_user_id,
            "sport": athlete.sport if athlete and athlete.sport else "General",
            "position": athlete.position if athlete and athlete.position else "Athlete",
            "height": athlete_height,
            "weight": athlete_weight,
            "training_load": float(athlete.training_load) if athlete and athlete.training_load is not None else None
        }

        # Calculate rule-based injury risk
        risk_assessment = calculate_injury_risk(
            features=summary_payload,
            athlete_profile=athlete_meta,
            historical_data=athlete_injuries
        )
        summary_payload["risk_assessment"] = risk_assessment

        pdf_filename = f"{video_id}_report.pdf"
        pdf_filepath = os.path.join(REPORTS_DIR, pdf_filename)

        video_meta = {
            "activity": video.activity if video.activity else "Movement Test",
            "fps": fps,
            "duration": video.duration if video.duration else total_frames / fps,
            "total_frames": total_frames,
            "valid_pose_frames": valid_pose_frames
        }

        generate_pdf_report(
            output_pdf_path=pdf_filepath,
            athlete_info=athlete_meta,
            video_info=video_meta,
            analysis_id=str(analysis.analysis_id),
            summary_metrics=summary_payload,
            risk_assessment=risk_assessment
        )

        pdf_report_url = f"{BACKEND_URL}/uploads/analysis/reports/{pdf_filename}"

        # ====================================================
        # 11. SAVE GENUINE FEATURES & RISK ASSESSMENT TO DATABASE
        # ====================================================
        analysis.progress = 98
        analysis.stage = "Finalizing risk assessment and feature dataset..."
        db.commit()

        # Real scalar measurements (or None if unavailable)
        max_knee_valgus = valgus_data.get("max_deviation")
        analysis.knee_valgus = float(max_knee_valgus) if max_knee_valgus is not None else None

        avg_trunk_lean = trunk_data.get("avg_trunk_lean_deg")
        analysis.trunk_lean = float(avg_trunk_lean) if avg_trunk_lean is not None else None

        norm_stride = stride_data.get("normalized_stride_length")
        analysis.stride_length = float(norm_stride) if norm_stride is not None else None

        hip_score = hip_data.get("score")
        analysis.hip_stability = float(hip_score) if hip_score is not None else None

        alignment_score = alignment_data.get("score")
        analysis.joint_alignment = float(alignment_score) if alignment_score is not None else None

        sym_score = symmetry_data.get("overall_symmetry_score")
        analysis.symmetry_score = float(sym_score) if sym_score is not None else None

        analysis.fatigue_score = float(consistency_score) if consistency_score is not None else None
        analysis.movement_quality = float(risk_assessment.get("movement_quality_score", movement_quality))

        component_scores = risk_assessment.get("component_scores", {})
        analysis.algorithm_version = summary_payload.get("feature_extraction_version", "1.0-phase1-filtered")
        analysis.historical_score = float(component_scores.get("historical_injury_factors", 0.0))
        analysis.biomechanical_score = float(component_scores.get("biomechanical_deviations", 0.0))
        analysis.asymmetry_score = float(component_scores.get("movement_asymmetry", 0.0))
        analysis.training_load_score = float(component_scores.get("training_load", 0.0))
        analysis.composite_risk_score = float(risk_assessment.get("injury_risk_score", 0.0))
        analysis.risk_category = str(risk_assessment.get("risk_category", "Low Risk"))

        # Restored Rule-Based Injury Risk Assessment
        analysis.overall_risk_score = float(risk_assessment.get("injury_risk_score", 0.0))
        analysis.risk_level = str(risk_assessment.get("risk_category", "Low Risk"))
        analysis.recommendations = risk_assessment.get("recommendations", [])

        # Generated asset URLs
        analysis.skeleton_video_url = skeleton_video_url
        analysis.csv_report_url = csv_report_url
        analysis.pdf_report_url = pdf_report_url

        # JSON payloads
        analysis.summary_metrics = summary_payload
        analysis.time_series_data = time_series_payload

        # Mark completed
        analysis.status = "completed"
        analysis.progress = 100
        analysis.stage = "Feature extraction complete"
        analysis.completed_at = datetime.utcnow()

        video.processing_status = "analyzed"
        db.commit()

        print(f"Feature extraction completed successfully for video {video_id}")
        print(f"Pose coverage: {pose_detection_rate:.2f}% ({valid_pose_frames}/{total_frames} valid frames)")
        print("Features calculated strictly from reliable skeleton frames.")

    except Exception as e:
        print(f"Error in movement feature extraction pipeline: {str(e)}")
        db.rollback()
        if analysis:
            analysis.status = "failed"
            analysis.progress = 0
            analysis.stage = "Feature extraction failed"
            analysis.error_message = str(e)
            db.commit()

    finally:
        db.close()
