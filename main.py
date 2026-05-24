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
        while _running:
            if not disp.handle_events():
                break
            frame = cam.read_frame()
            if frame is None:
                continue  # waiting for first frame or reconnect
            disp.render(frame)


if __name__ == "__main__":
    main()
