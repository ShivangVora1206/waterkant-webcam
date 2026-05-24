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
        # Pre-allocated objects — created once on first frame, reused every frame
        self._display_surface = None   # pygame.Surface at dest size
        self._pixel_buffer = None      # numpy (W, H, 3) buffer for blit_array
        self._dest_rect = None         # (x, y, w, h) letterbox/pillarbox placement
        self._last_frame_size = None   # (w, h) of the last rotated frame

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

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

    def close(self):
        pygame.quit()

    # ------------------------------------------------------------------
    # Frame transforms
    # ------------------------------------------------------------------

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

    def _compute_dest(self, frame_w: int, frame_h: int):
        """Fit frame inside screen while preserving aspect ratio (letterbox / pillarbox).

        Returns (dest_x, dest_y, dest_w, dest_h).  Any unused area is black.
        """
        screen_w, screen_h = self._screen_size
        scale = min(screen_w / frame_w, screen_h / frame_h)
        dest_w = int(frame_w * scale)
        dest_h = int(frame_h * scale)
        dest_x = (screen_w - dest_w) // 2
        dest_y = (screen_h - dest_h) // 2
        return dest_x, dest_y, dest_w, dest_h

    # ------------------------------------------------------------------
    # Render
    # ------------------------------------------------------------------

    def render(self, frame: np.ndarray):
        frame = self._apply_rotation(frame)
        frame_h, frame_w = frame.shape[:2]

        # On first frame (or if frame size changes), set up the layout and
        # pre-allocate the surface + pixel buffer used every subsequent frame.
        if (frame_w, frame_h) != self._last_frame_size:
            dest_x, dest_y, dest_w, dest_h = self._compute_dest(frame_w, frame_h)
            self._dest_rect = (dest_x, dest_y, dest_w, dest_h)
            self._last_frame_size = (frame_w, frame_h)
            # Surface lives at dest size; allocate once and reuse
            self._display_surface = pygame.Surface((dest_w, dest_h))
            # pygame.surfarray expects (W, H, 3) — allocate contiguous buffer
            self._pixel_buffer = np.empty((dest_w, dest_h, 3), dtype=np.uint8)
            # Paint black bars once — they never need to be redrawn
            self._screen.fill((0, 0, 0))

        dest_x, dest_y, dest_w, dest_h = self._dest_rect

        # cv2.resize is significantly faster than pygame.transform.scale for
        # large frames because it runs in optimised C with SIMD support.
        frame = cv2.resize(frame, (dest_w, dest_h), interpolation=cv2.INTER_LINEAR)

        # BGR → RGB conversion (in C, no Python overhead)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Transpose from OpenCV's (H, W, 3) to pygame's (W, H, 3) layout and
        # write into the pre-allocated contiguous buffer (avoids heap allocation).
        np.copyto(self._pixel_buffer, frame.transpose(1, 0, 2))

        # Blit directly into the pre-allocated surface (no new Surface created)
        pygame.surfarray.blit_array(self._display_surface, self._pixel_buffer)
        self._screen.blit(self._display_surface, (dest_x, dest_y))
        pygame.display.flip()

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def handle_events(self) -> bool:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return False
        return True

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *_):
        self.close()
