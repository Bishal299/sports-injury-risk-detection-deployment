from app.services.video_reader import VideoReader


VIDEO_PATH = r"C:\Sports_injury_detection\sports-injury-risk-detection\backend\uploads\videos\b36254b2-6ae9-47b4-89b3-b0b64059cfa9.mp4"


reader = VideoReader(VIDEO_PATH)

print("\n========== VIDEO METADATA ==========")

metadata = reader.get_metadata()

print("FPS:", metadata["fps"])
print("Total Frames:", metadata["total_frames"])
print("Width:", metadata["width"])
print("Height:", metadata["height"])
print("Duration:", metadata["duration"])

print("\n========== READING FRAMES ==========")

count = 0

for frame in reader.frames():

    count += 1

    if count <= 5:
        print(
            f"Frame {count}: "
            f"{frame.shape}"
        )

    if count >= 5:
        break

reader.release()

print("\nVideoReader working successfully!")