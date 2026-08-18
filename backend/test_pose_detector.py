from app.services.video_reader import VideoReader
from app.services.pose_detector import PoseDetector
from app.services.landmark_extractor import extract_landmarks


VIDEO_PATH = r"C:\Sports_injury_detection\sports-injury-risk-detection\backend\uploads\videos\b36254b2-6ae9-47b4-89b3-b0b64059cfa9.mp4"
MODEL_PATH = "models/pose_landmarker_lite.task"


reader = VideoReader(VIDEO_PATH)
detector = PoseDetector(MODEL_PATH)

fps = reader.fps

all_frames = []

frame_number = 0
detected_frames = 0


for frame in reader.frames():

    timestamp_ms = int(
        (frame_number / fps) * 1000
    )

    results = detector.detect(
        frame,
        timestamp_ms
    )

    landmarks = extract_landmarks(results)

    if landmarks:

        detected_frames += 1

        all_frames.append({
            "frame_number": frame_number,
            "timestamp_ms": timestamp_ms,
            "landmarks": landmarks
        })

    frame_number += 1

    # Test only first 100 frames
    if frame_number >= 100:
        break


reader.release()
detector.close()


print("\n========== RESULT ==========")

print("Frames processed:", frame_number)
print("Frames with pose:", detected_frames)

print(
    "Frames stored:",
    len(all_frames)
)


if all_frames:

    first_frame = all_frames[0]

    print("\nFirst frame number:")
    print(first_frame["frame_number"])

    print("\nNumber of landmarks:")
    print(len(first_frame["landmarks"]))

    print("\nKnee/leg landmarks:")

    for landmark in first_frame["landmarks"]:

        if landmark["landmark_id"] in [23, 24, 25, 26, 27, 28]:

            print(landmark)