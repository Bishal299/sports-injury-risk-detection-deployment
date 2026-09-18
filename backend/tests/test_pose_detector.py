from types import SimpleNamespace

import numpy as np

from app.services import pose_detector as pose_detector_module
from app.services.landmark_extractor import extract_landmarks
from app.services.pose_detector import PoseDetector


def test_pose_detector_converts_frame_and_uses_video_timestamp(monkeypatch):
    calls = {}

    class FakeDetector:
        def detect_for_video(self, image, timestamp_ms):
            calls["image"] = image
            calls["timestamp_ms"] = timestamp_ms
            return SimpleNamespace(pose_landmarks=[])

        def close(self):
            calls["closed"] = True

    class FakePoseLandmarker:
        @staticmethod
        def create_from_options(options):
            calls["options"] = options
            return FakeDetector()

    monkeypatch.setattr(pose_detector_module.python, "BaseOptions", lambda model_asset_path: {"model": model_asset_path})
    monkeypatch.setattr(
        pose_detector_module.vision,
        "PoseLandmarkerOptions",
        lambda base_options, running_mode, num_poses: {
            "base_options": base_options,
            "running_mode": running_mode,
            "num_poses": num_poses,
        },
    )
    monkeypatch.setattr(pose_detector_module.vision, "PoseLandmarker", FakePoseLandmarker)
    monkeypatch.setattr(pose_detector_module.vision, "RunningMode", SimpleNamespace(VIDEO="VIDEO"))
    monkeypatch.setattr(pose_detector_module.mp, "ImageFormat", SimpleNamespace(SRGB="SRGB"))
    monkeypatch.setattr(
        pose_detector_module.mp,
        "Image",
        lambda image_format, data: {"image_format": image_format, "data": data},
    )

    detector = PoseDetector("models/pose_landmarker_lite.task")
    frame = np.zeros((8, 8, 3), dtype=np.uint8)
    result = detector.detect(frame, timestamp_ms=123)
    detector.close()

    assert result.pose_landmarks == []
    assert calls["options"]["base_options"] == {"model": "models/pose_landmarker_lite.task"}
    assert calls["options"]["num_poses"] == 1
    assert calls["timestamp_ms"] == 123
    assert calls["image"]["image_format"] == "SRGB"
    assert calls["image"]["data"].shape == frame.shape
    assert calls["closed"] is True


def test_extract_landmarks_returns_landmark_dicts():
    landmarks = [
        SimpleNamespace(x=0.1, y=0.2, z=0.3, visibility=0.9),
        SimpleNamespace(x=0.4, y=0.5, z=0.6, visibility=0.8),
    ]
    results = SimpleNamespace(pose_landmarks=[landmarks])

    extracted = extract_landmarks(results)

    assert extracted == [
        {"landmark_id": 0, "x": 0.1, "y": 0.2, "z": 0.3, "visibility": 0.9},
        {"landmark_id": 1, "x": 0.4, "y": 0.5, "z": 0.6, "visibility": 0.8},
    ]


def test_extract_landmarks_returns_none_when_no_pose():
    assert extract_landmarks(SimpleNamespace(pose_landmarks=[])) is None
