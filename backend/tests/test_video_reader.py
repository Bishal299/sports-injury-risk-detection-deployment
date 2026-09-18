import numpy as np
import pytest

from app.services import video_reader as video_reader_module
from app.services.video_reader import VideoReader


class FakeVideoCapture:
    def __init__(self, opened=True):
        self.opened = opened
        self.released = False
        self.frames = [
            np.zeros((24, 32, 3), dtype=np.uint8),
            np.ones((24, 32, 3), dtype=np.uint8),
            np.full((24, 32, 3), 2, dtype=np.uint8),
        ]

    def isOpened(self):
        return self.opened

    def get(self, prop):
        values = {
            video_reader_module.cv2.CAP_PROP_FPS: 30.0,
            video_reader_module.cv2.CAP_PROP_FRAME_COUNT: len(self.frames),
            video_reader_module.cv2.CAP_PROP_FRAME_WIDTH: 32,
            video_reader_module.cv2.CAP_PROP_FRAME_HEIGHT: 24,
        }
        return values[prop]

    def read(self):
        if not self.frames:
            return False, None
        return True, self.frames.pop(0)

    def release(self):
        self.released = True


def test_video_reader_metadata_and_frame_iteration(monkeypatch):
    capture = FakeVideoCapture(opened=True)
    monkeypatch.setattr(video_reader_module.cv2, "VideoCapture", lambda _path: capture)

    reader = VideoReader("synthetic.mp4")

    assert reader.get_metadata() == {
        "fps": 30.0,
        "total_frames": 3,
        "width": 32,
        "height": 24,
        "duration": 0.1,
    }

    frames = list(reader.frames())
    assert len(frames) == 3
    assert frames[0].shape == (24, 32, 3)

    reader.release()
    assert capture.released is True


def test_video_reader_rejects_unreadable_video(monkeypatch):
    monkeypatch.setattr(video_reader_module.cv2, "VideoCapture", lambda _path: FakeVideoCapture(opened=False))

    with pytest.raises(ValueError, match="Could not open video"):
        VideoReader("missing.mp4")
