from app.services.video_service import get_video_metadata


video_path = r"PUT_YOUR_VIDEO_PATH_HERE"


metadata = get_video_metadata(video_path)

print("\nVideo Metadata")
print("----------------------")

for key, value in metadata.items():
    print(f"{key}: {value}")