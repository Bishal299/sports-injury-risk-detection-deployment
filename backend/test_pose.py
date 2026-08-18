from app.services.pose_detection import detect_pose


image_path = r"C:\Sports_injury_detection\sports-injury-risk-detection\backend\uploads\frames\51d8e9d0-68e2-4545-aa1a-ef26c7f61cbb\frame_000000.jpg"

landmarks = detect_pose(image_path)


if landmarks is None:

    print("❌ No pose detected")

else:

    print("✅ Pose detected!")

    print(
        "Number of landmarks:",
        len(landmarks)
    )

    print(
        "First landmark:",
        landmarks[0]
    )