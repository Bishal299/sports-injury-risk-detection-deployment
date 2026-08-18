import cv2


class VideoReader:

    def __init__(self, video_path: str):

        self.video_path = video_path

        self.cap = cv2.VideoCapture(video_path)

        if not self.cap.isOpened():
            raise ValueError(
                f"Could not open video: {video_path}"
            )

        self.fps = self.cap.get(
            cv2.CAP_PROP_FPS
        )

        self.total_frames = int(
            self.cap.get(
                cv2.CAP_PROP_FRAME_COUNT
            )
        )

        self.width = int(
            self.cap.get(
                cv2.CAP_PROP_FRAME_WIDTH
            )
        )

        self.height = int(
            self.cap.get(
                cv2.CAP_PROP_FRAME_HEIGHT
            )
        )

        self.duration = (
            self.total_frames / self.fps
            if self.fps > 0
            else 0
        )

    def get_metadata(self):

        return {
            "fps": self.fps,
            "total_frames": self.total_frames,
            "width": self.width,
            "height": self.height,
            "duration": self.duration
        }

    def frames(self):

        while True:

            success, frame = self.cap.read()

            if not success:
                break

            yield frame

    def release(self):

        if self.cap:
            self.cap.release()