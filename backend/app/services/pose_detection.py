import cv2
import mediapipe as mp


# MediaPipe Tasks API
BaseOptions = mp.tasks.BaseOptions
PoseLandmarker = mp.tasks.vision.PoseLandmarker
PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode


# IMPORTANT:
# We will need a MediaPipe pose model file.
MODEL_PATH = "models/pose_landmarker_lite.task"


def detect_pose(image_path: str):

    image = cv2.imread(image_path)

    if image is None:
        raise ValueError(
            f"Could not read image: {image_path}"
        )

    # OpenCV BGR -> RGB
    rgb_image = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2RGB
    )

    # Convert OpenCV image to MediaPipe image
    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=rgb_image
    )

    options = PoseLandmarkerOptions(
        base_options=BaseOptions(
            model_asset_path=MODEL_PATH
        ),
        running_mode=VisionRunningMode.IMAGE,
        num_poses=1,
        min_pose_detection_confidence=0.5,
        min_pose_presence_confidence=0.5,
        min_tracking_confidence=0.5
    )

    with PoseLandmarker.create_from_options(options) as landmarker:

        result = landmarker.detect(mp_image)

    if not result.pose_landmarks:
        return None

    landmarks = []

    for landmark in result.pose_landmarks[0]:

        landmarks.append({
            "x": landmark.x,
            "y": landmark.y,
            "z": landmark.z,
            "visibility": landmark.visibility
        })

    return landmarks