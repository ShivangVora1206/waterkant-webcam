import logging
import re
import subprocess
import threading
import time

import cv2
import numpy as np


class Camera:
    def __init__(self, config):
        self._config = config
        self._cap = None
        self._lock = threading.Lock()
        self._latest_frame = None
        self._capture_thread = None
        self._running = False

    # ------------------------------------------------------------------
    # Device detection
    # ------------------------------------------------------------------

    def _detect_device_index(self) -> int:
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
                    if any(kw in line for kw in ("Brio", "BRIO", "046d")):
                        for candidate in lines[i + 1 :]:
                            match = re.search(r"/dev/video(\d+)", candidate.strip())
                            if match:
                                return int(match.group(1))
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        for index in range(5):
            cap = cv2.VideoCapture(index, cv2.CAP_V4L2)
            if cap.isOpened():
                cap.release()
                return index

        raise RuntimeError(
            "No camera found. Connect the Logitech Brio 105 and try again, "
            "or set CAMERA_INDEX in config.py."
        )

    # ------------------------------------------------------------------
    # Device open / close
    # ------------------------------------------------------------------

    def _open_device(self):
        """Open the V4L2 device and apply capture settings."""
        if self._config.CAMERA_INDEX is not None:
            index = self._config.CAMERA_INDEX
        else:
            index = self._detect_device_index()

        cap = cv2.VideoCapture(index, cv2.CAP_V4L2)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._config.CAMERA_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._config.CAMERA_HEIGHT)
        cap.set(cv2.CAP_PROP_FPS, self._config.CAMERA_FPS)
        # Minimal internal buffer to avoid stale frames piling up
        cap.set(cv2.CAP_PROP_BUFFERSIZE, self._config.FRAME_BUFFER_SIZE)

        if not cap.isOpened():
            raise RuntimeError(f"Failed to open camera at index {index}.")

        self._cap = cap
        logging.info("Camera opened at /dev/video%d", index)

    # ------------------------------------------------------------------
    # Background capture thread
    # ------------------------------------------------------------------

    def _capture_loop(self):
        """Continuously grab frames in the background.

        Keeps self._latest_frame up to date so the display loop can call
        read_frame() without blocking on camera I/O.
        """
        consecutive_failures = 0
        while self._running:
            if self._cap is None:
                time.sleep(0.05)
                continue

            ok, frame = self._cap.read()
            if ok:
                consecutive_failures = 0
                with self._lock:
                    self._latest_frame = frame
            else:
                consecutive_failures += 1
                if consecutive_failures >= self._config.CAMERA_RECONNECT_ATTEMPTS:
                    logging.warning("Camera feed lost — attempting reconnect...")
                    with self._lock:
                        self._latest_frame = None
                    if self._cap is not None:
                        self._cap.release()
                        self._cap = None
                    time.sleep(1)
                    try:
                        self._open_device()
                        consecutive_failures = 0
                    except Exception as exc:
                        logging.error("Reconnect failed: %s", exc)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def open(self):
        self._open_device()
        self._running = True
        self._capture_thread = threading.Thread(
            target=self._capture_loop, daemon=True, name="camera-capture"
        )
        self._capture_thread.start()

    def read_frame(self) -> np.ndarray | None:
        """Return a copy of the most recently captured frame (non-blocking)."""
        with self._lock:
            if self._latest_frame is None:
                return None
            return self._latest_frame.copy()

    def close(self):
        self._running = False
        if self._capture_thread is not None:
            self._capture_thread.join(timeout=2)
            self._capture_thread = None
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *_):
        self.close()
