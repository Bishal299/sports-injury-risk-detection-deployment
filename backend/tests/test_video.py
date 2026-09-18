import pytest

from app.utils import video as video_utils


class FakeCapture:
    def __init__(self, opened=True):
        self.opened = opened
        self.released = False

    def isOpened(self):
        return self.opened

    def get(self, prop):
        values = {
            video_utils.cv2.CAP_PROP_FPS: 29.97,
            video_utils.cv2.CAP_PROP_FRAME_COUNT: 300,
            video_utils.cv2.CAP_PROP_FRAME_WIDTH: 1280,
            video_utils.cv2.CAP_PROP_FRAME_HEIGHT: 720,
        }
        return values[prop]

    def release(self):
        self.released = True


def test_extract_video_metadata_reads_capture_properties(monkeypatch):
    capture = FakeCapture(opened=True)
    monkeypatch.setattr(video_utils.cv2, "VideoCapture", lambda _path: capture)

    metadata = video_utils.extract_video_metadata("synthetic.mp4")

    assert metadata == {
        "duration": 300 / 29.97,
        "fps": 30,
        "resolution": "1280x720",
    }
    assert capture.released is True


def test_extract_video_metadata_rejects_unreadable_video(monkeypatch):
    monkeypatch.setattr(video_utils.cv2, "VideoCapture", lambda _path: FakeCapture(opened=False))

    with pytest.raises(ValueError, match="Unable to open video"):
        video_utils.extract_video_metadata("missing.mp4")
