import logging
import signal
import sys

import config
from camera import Camera
from display import Display

logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="%(levelname)s: %(message)s")

_running = True


def _sigterm_handler(sig, frame):
    global _running
    _running = False


signal.signal(signal.SIGTERM, _sigterm_handler)


def main():
    with Camera(config) as cam, Display(config) as disp:
        consecutive_failures = 0
        while _running:
            frame = cam.read_frame()

            if frame is None:
                consecutive_failures += 1
                if consecutive_failures >= config.CAMERA_RECONNECT_ATTEMPTS:
                    logging.warning("Camera feed lost — attempting reconnect...")
                    cam.close()
                    cam.open()
                    consecutive_failures = 0
                continue

            consecutive_failures = 0

            if not disp.handle_events():
                break

            disp.render(frame)


if __name__ == "__main__":
    main()
