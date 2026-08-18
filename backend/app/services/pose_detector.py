import cv2
import mediapipe as mp

from mediapipe.tasks import python
from mediapipe.tasks.python import vision


class PoseDetector:

    def __init__(self, model_path: str):

        base_options = python.BaseOptions(
            model_asset_path=model_path
        )

        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_poses=1
        )

        self.detector = (
            vision.PoseLandmarker.create_from_options(
                options
            )
        )

    def detect(self, frame, timestamp_ms):

        # OpenCV uses BGR
        # MediaPipe expects RGB

        rgb_frame = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb_frame
        )

        results = self.detector.detect_for_video(
            mp_image,
            timestamp_ms
        )

        return results

    def close(self):

        self.detector.close()