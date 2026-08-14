import cv2


def extract_video_metadata(video_path: str):
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        raise ValueError("Unable to open video")

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    cap.release()

    if fps and fps > 0:
        duration = frame_count / fps
    else:
        duration = None

    resolution = None

    if width > 0 and height > 0:
        resolution = f"{width}x{height}"

    return {
        "duration": duration,
        "fps": int(round(fps)) if fps else None,
        "resolution": resolution
    }