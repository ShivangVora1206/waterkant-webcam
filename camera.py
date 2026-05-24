import re
import subprocess
import cv2
import numpy as np


class Camera:
    def __init__(self, config):
        self._config = config
        self._cap = None

    def _detect_device_index(self) -> int:
        # Try v4l2-ctl first — most reliable on RPi OS
        try:
            result = subprocess.run(
                ["v4l2-ctl", "--list-devices"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                lines = result.stdout.splitlines()
                for i, line in enumerate(lines):
                    # Match Logitech Brio 105 by name or USB vendor ID
                    if any(kw in line for kw in ("Brio", "BRIO", "046d")):
                        # Next non-empty line(s) are the /dev/videoN paths
                        for candidate in lines[i + 1:]:
                            candidate = candidate.strip()
                            match = re.search(r"/dev/video(\d+)", candidate)
                            if match:
                                return int(match.group(1))
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        # Fall back to probing indices 0–4
        for index in range(5):
            cap = cv2.VideoCapture(index, cv2.CAP_V4L2)
            if cap.isOpened():
                cap.release()
                return index

        raise RuntimeError(
            "No camera found. Connect the Logitech Brio 105 and try again, "
            "or set CAMERA_INDEX in config.py."
        )

    def open(self):
        if self._config.CAMERA_INDEX is not None:
            index = self._config.CAMERA_INDEX
        else:
            index = self._detect_device_index()

        self._cap = cv2.VideoCapture(index, cv2.CAP_V4L2)
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._config.CAMERA_WIDTH)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._config.CAMERA_HEIGHT)
        self._cap.set(cv2.CAP_PROP_FPS, self._config.CAMERA_FPS)
        # Keep the internal buffer at 1 frame to minimise capture latency
        self._cap.set(cv2.CAP_PROP_BUFFERSIZE, self._config.FRAME_BUFFER_SIZE)

        if not self._cap.isOpened():
            raise RuntimeError(f"Failed to open camera at index {index}.")

    def read_frame(self) -> np.ndarray | None:
        if self._cap is None:
            return None
        ok, frame = self._cap.read()
        return frame if ok else None

    def close(self):
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *_):
        self.close()
