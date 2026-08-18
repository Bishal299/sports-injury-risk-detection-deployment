import cv2
import os


FRAMES_DIR = "uploads/frames"


def extract_frames(
    video_path: str,
    video_id: str,
    frame_interval: int = 5
):
    """
    Extract frames from a video.

    frame_interval=5 means:
    save every 5th frame.
    """

    output_dir = os.path.join(
        FRAMES_DIR,
        str(video_id)
    )

    os.makedirs(
        output_dir,
        exist_ok=True
    )

    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        raise ValueError(
            "Could not open video"
        )

    frame_number = 0
    saved_frames = 0

    while True:

        success, frame = cap.read()

        if not success:
            break

        if frame_number % frame_interval == 0:

            frame_filename = (
                f"frame_{frame_number:06d}.jpg"
            )

            frame_path = os.path.join(
                output_dir,
                frame_filename
            )

            cv2.imwrite(
                frame_path,
                frame
            )

            saved_frames += 1

        frame_number += 1

    cap.release()

    return {
        "total_frames": frame_number,
        "saved_frames": saved_frames,
        "frames_directory": output_dir
    }