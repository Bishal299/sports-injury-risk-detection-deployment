import os
import cv2
from typing import List, Dict, Any
import subprocess
import shutil
import gc
import time


# Pose Landmark Connections
POSE_CONNECTIONS = [
    # Torso
    (11, 12, (240, 240, 240)),  # Shoulders
    (11, 23, (0, 200, 255)),    # Left torso
    (12, 24, (255, 140, 0)),    # Right torso
    (23, 24, (240, 240, 240)),  # Hips
    
    # Left Arm
    (11, 13, (0, 220, 255)),
    (13, 15, (0, 220, 255)),
    
    # Right Arm
    (12, 14, (255, 140, 0)),
    (14, 16, (255, 140, 0)),
    
    # Left Leg
    (23, 25, (0, 255, 128)),
    (25, 27, (0, 255, 128)),
    (27, 29, (0, 255, 128)),
    (29, 31, (0, 255, 128)),
    (27, 31, (0, 255, 128)),
    
    # Right Leg
    (24, 26, (255, 100, 50)),
    (26, 28, (255, 100, 50)),
    (28, 30, (255, 100, 50)),
    (30, 32, (255, 100, 50)),
    (28, 32, (255, 100, 50)),
    
    # Head & Neck
    (9, 10, (200, 200, 200)),
    (0, 1, (200, 200, 200)),
    (0, 4, (200, 200, 200)),
    (1, 2, (200, 200, 200)),
    (2, 3, (200, 200, 200)),
    (4, 5, (200, 200, 200)),
    (5, 6, (200, 200, 200)),
    (3, 7, (200, 200, 200)),
    (6, 8, (200, 200, 200)),
]


def render_skeleton_video(
    source_video_path: str,
    output_video_path: str,
    frames_landmarks: List[Dict[str, Any]],
    fps: float = 30.0
) -> str:
    """
    Renders an AI virtual skeleton overlay on the original video frames and writes to an MP4 video.
    Optimized for memory efficiency (< 50MB RAM) on cloud container environments like Render (512MB RAM cap).
    """
    gc.collect()
    os.makedirs(os.path.dirname(output_video_path), exist_ok=True)

    cap = cv2.VideoCapture(source_video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open source video: {source_video_path}")

    raw_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    raw_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    video_fps = cap.get(cv2.CAP_PROP_FPS)
    if video_fps and 0 < video_fps <= 60:
        fps = min(video_fps, 30.0)  # Cap at 30 fps to reduce memory and processing time

    # Cap dimensions to max 720p to maintain web fidelity while minimizing memory consumption
    max_dim = 720
    scale = 1.0
    if max(raw_width, raw_height) > max_dim:
        scale = max_dim / float(max(raw_width, raw_height))
        target_width = int(raw_width * scale)
        target_height = int(raw_height * scale)
    else:
        target_width = raw_width
        target_height = raw_height

    # Ensure even dimensions required by libx264 / yuv420p
    target_width = target_width if target_width % 2 == 0 else target_width - 1
    target_height = target_height if target_height % 2 == 0 else target_height - 1

    # Map frame index to landmark dictionary
    frame_lm_map = {}
    for item in frames_landmarks:
        fn = item.get("frame_number")
        if fn is not None:
            lms = item.get("landmarks", [])
            frame_lm_map[fn] = {lm["landmark_id"]: lm for lm in lms if "landmark_id" in lm}

    # Setup VideoWriter
    temp_output = output_video_path + ".temp.mp4"
    if os.path.exists(temp_output):
        try:
            os.remove(temp_output)
        except Exception:
            pass

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_output, fourcc, fps, (target_width, target_height))

    frame_idx = 0
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Downscale frame immediately if needed to keep working memory minimal
            if scale < 1.0 or frame.shape[1] != target_width or frame.shape[0] != target_height:
                frame = cv2.resize(frame, (target_width, target_height), interpolation=cv2.INTER_AREA)

            lm_dict = frame_lm_map.get(frame_idx)
            if lm_dict:
                # Draw bone connections
                for p1_id, p2_id, color in POSE_CONNECTIONS:
                    if p1_id in lm_dict and p2_id in lm_dict:
                        p1 = lm_dict[p1_id]
                        p2 = lm_dict[p2_id]

                        if p1.get("visibility", 1.0) > 0.3 and p2.get("visibility", 1.0) > 0.3:
                            pt1 = (int(p1["x"] * target_width), int(p1["y"] * target_height))
                            pt2 = (int(p2["x"] * target_width), int(p2["y"] * target_height))

                            # Draw glow + main line
                            cv2.line(frame, pt1, pt2, (20, 20, 20), thickness=4, lineType=cv2.LINE_AA)
                            cv2.line(frame, pt1, pt2, color, thickness=2, lineType=cv2.LINE_AA)

                # Draw landmark points
                for lm_id, lm in lm_dict.items():
                    if lm.get("visibility", 1.0) > 0.3:
                        cx = int(lm["x"] * target_width)
                        cy = int(lm["y"] * target_height)

                        # Highlight key joints
                        if lm_id in [23, 24, 25, 26, 27, 28, 11, 12, 13, 14]:
                            cv2.circle(frame, (cx, cy), 5, (255, 255, 255), -1, lineType=cv2.LINE_AA)
                            cv2.circle(frame, (cx, cy), 7, (0, 0, 0), 2, lineType=cv2.LINE_AA)
                        else:
                            cv2.circle(frame, (cx, cy), 3, (220, 220, 220), -1, lineType=cv2.LINE_AA)

                # Draw subtle overlay HUD
                hud_text = "AI SKELETON TRACKING ACTIVE"
                cv2.putText(frame, hud_text, (16, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 3, cv2.LINE_AA)
                cv2.putText(frame, hud_text, (16, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 200), 2, cv2.LINE_AA)

            out.write(frame)
            frame_idx += 1
    finally:
        cap.release()
        out.release()
        del out
        del cap
        del frame_lm_map
        gc.collect()

    time.sleep(0.1)

    # Detect ffmpeg (from imageio-ffmpeg bundle or system PATH)
    ffmpeg_exe = shutil.which("ffmpeg")
    if not ffmpeg_exe:
        try:
            import imageio_ffmpeg
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            ffmpeg_exe = None

    if ffmpeg_exe and os.path.exists(temp_output):
        try:
            # Low-memory single-threaded H.264 encode for web playback
            cmd = [
                ffmpeg_exe, "-y",
                "-threads", "1",
                "-i", temp_output,
                "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2",
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-crf", "28",
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
                output_video_path
            ]
            subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                timeout=60
            )
            if os.path.exists(temp_output):
                try:
                    os.remove(temp_output)
                except Exception:
                    pass
            gc.collect()
            return output_video_path
        except Exception as e:
            print("FFmpeg low-memory encoding error or fallback:", str(e))

    # Fallback to temp output if ffmpeg is completely unavailable
    if os.path.exists(temp_output):
        try:
            if os.path.exists(output_video_path):
                os.remove(output_video_path)
            shutil.move(temp_output, output_video_path)
        except Exception as e:
            print("Fallback move error:", str(e))

    gc.collect()
    return output_video_path
