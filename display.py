import cv2
import numpy as np
import pygame


_ROTATION_MAP = {
    90:  cv2.ROTATE_90_CLOCKWISE,
    -90: cv2.ROTATE_90_COUNTERCLOCKWISE,
    180: cv2.ROTATE_180,
}


class Display:
    def __init__(self, config):
        self._config = config
        self._screen = None
        self._screen_size = None

    def open(self):
        pygame.init()
        pygame.display.set_caption(self._config.WINDOW_TITLE)
        pygame.mouse.set_visible(False)

        if self._config.DISPLAY_FULLSCREEN:
            self._screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self._screen = pygame.display.set_mode(
                (self._config.CAMERA_WIDTH, self._config.CAMERA_HEIGHT)
            )

        self._screen_size = self._screen.get_size()

    def _apply_rotation(self, frame: np.ndarray) -> np.ndarray:
        rotation = self._config.DISPLAY_ROTATION
        if rotation in _ROTATION_MAP:
            frame = cv2.rotate(frame, _ROTATION_MAP[rotation])

        if self._config.FLIP_HORIZONTAL and self._config.FLIP_VERTICAL:
            frame = cv2.flip(frame, -1)
        elif self._config.FLIP_HORIZONTAL:
            frame = cv2.flip(frame, 1)
        elif self._config.FLIP_VERTICAL:
            frame = cv2.flip(frame, 0)

        return frame

    def render(self, frame: np.ndarray):
        frame = self._apply_rotation(frame)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # surfarray expects (width, height, channels); cv2 gives (height, width, channels)
        surface = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
        scaled = pygame.transform.scale(surface, self._screen_size)
        self._screen.blit(scaled, (0, 0))
        pygame.display.flip()

    def handle_events(self) -> bool:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return False
        return True

    def close(self):
        pygame.quit()

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *_):
        self.close()
