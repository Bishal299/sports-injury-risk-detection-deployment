import os
import cv2
from typing import List, Dict, Any
import subprocess
import shutil


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
    """
    os.makedirs(os.path.dirname(output_video_path), exist_ok=True)

    cap = cv2.VideoCapture(source_video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open source video: {source_video_path}")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    video_fps = cap.get(cv2.CAP_PROP_FPS)
    if video_fps and video_fps > 0:
        fps = video_fps

    # Map frame index to landmark dictionary
    frame_lm_map = {}
    for item in frames_landmarks:
        fn = item.get("frame_number")
        if fn is not None:
            lms = item.get("landmarks", [])
            frame_lm_map[fn] = {lm["landmark_id"]: lm for lm in lms if "landmark_id" in lm}

    # Setup VideoWriter
    temp_output = output_video_path + ".temp.mp4"
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_output, fourcc, fps, (width, height))

    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        lm_dict = frame_lm_map.get(frame_idx)
        if lm_dict:
            # Draw bone connections
            for p1_id, p2_id, color in POSE_CONNECTIONS:
                if p1_id in lm_dict and p2_id in lm_dict:
                    p1 = lm_dict[p1_id]
                    p2 = lm_dict[p2_id]

                    if p1.get("visibility", 1.0) > 0.3 and p2.get("visibility", 1.0) > 0.3:
                        pt1 = (int(p1["x"] * width), int(p1["y"] * height))
                        pt2 = (int(p2["x"] * width), int(p2["y"] * height))

                        # Draw glow + main line
                        cv2.line(frame, pt1, pt2, (20, 20, 20), thickness=5, lineType=cv2.LINE_AA)
                        cv2.line(frame, pt1, pt2, color, thickness=3, lineType=cv2.LINE_AA)

            # Draw landmark points
            for lm_id, lm in lm_dict.items():
                if lm.get("visibility", 1.0) > 0.3:
                    cx = int(lm["x"] * width)
                    cy = int(lm["y"] * height)

                    # Highlight key joints
                    if lm_id in [23, 24, 25, 26, 27, 28, 11, 12, 13, 14]:
                        cv2.circle(frame, (cx, cy), 6, (255, 255, 255), -1, lineType=cv2.LINE_AA)
                        cv2.circle(frame, (cx, cy), 8, (0, 0, 0), 2, lineType=cv2.LINE_AA)
                    else:
                        cv2.circle(frame, (cx, cy), 4, (220, 220, 220), -1, lineType=cv2.LINE_AA)

            # Draw subtle overlay HUD
            hud_text = "AI SKELETON TRACKING ACTIVE"
            cv2.putText(frame, hud_text, (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 0), 3, cv2.LINE_AA)
            cv2.putText(frame, hud_text, (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 200), 2, cv2.LINE_AA)

        out.write(frame)
        frame_idx += 1

    cap.release()
    out.release()
    del out
    import time
    time.sleep(0.1)

    # Detect ffmpeg (from imageio-ffmpeg bundle or system PATH)
    ffmpeg_exe = shutil.which("ffmpeg")
    if not ffmpeg_exe:
        try:
            import imageio_ffmpeg
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            ffmpeg_exe = None

    if ffmpeg_exe:
        try:
            cmd = [
                ffmpeg_exe, "-y",
                "-i", temp_output,
                "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2",
                "-c:v", "libx264",
                "-preset", "fast",
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
                output_video_path
            ]
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            if os.path.exists(temp_output):
                try:
                    os.remove(temp_output)
                except Exception:
                    pass
            return output_video_path
        except Exception as e:
            print("FFmpeg encoding error:", str(e))

    # Fallback to temp output if ffmpeg is completely unavailable
    if os.path.exists(temp_output):
        try:
            if os.path.exists(output_video_path):
                os.remove(output_video_path)
            shutil.move(temp_output, output_video_path)
        except Exception as e:
            print("Fallback move error:", str(e))
    return output_video_path
