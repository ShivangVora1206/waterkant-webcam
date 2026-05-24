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
        self._display_surface = None   # pygame.Surface at screen size
        self._pixel_buffer = None      # numpy (W, H, 3) buffer for blit_array
        self._crop = None              # (src_x, src_y, src_w, src_h) center-crop region
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
        screen_w, screen_h = self._screen_size

        # Allocate once — output always fills the full screen
        self._display_surface = pygame.Surface((screen_w, screen_h))
        self._pixel_buffer = np.empty((screen_w, screen_h, 3), dtype=np.uint8)

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

    def _compute_crop(self, frame_w: int, frame_h: int):
        """Compute a center-crop region so the frame fills the screen with no bars.

        Uses the "cover" / object-fit:cover strategy:
          - Scale the frame up until BOTH dimensions meet or exceed the screen.
          - Crop the excess from the center.

        Returns (src_x, src_y, src_w, src_h) — a rect in the rotated frame that,
        when resized to screen dimensions, fills the display exactly.
        """
        screen_w, screen_h = self._screen_size
        # max() ensures the frame is large enough to cover the screen in both axes
        scale = max(screen_w / frame_w, screen_h / frame_h)
        # How much of the original frame maps to the screen after scaling
        src_w = round(screen_w / scale)
        src_h = round(screen_h / scale)
        # Centre the crop window
        src_x = (frame_w - src_w) // 2
        src_y = (frame_h - src_h) // 2
        return src_x, src_y, src_w, src_h

    # ------------------------------------------------------------------
    # Render
    # ------------------------------------------------------------------

    def render(self, frame: np.ndarray):
        frame = self._apply_rotation(frame)
        frame_h, frame_w = frame.shape[:2]

        # Recompute crop geometry only when frame dimensions change
        if (frame_w, frame_h) != self._last_frame_size:
            self._crop = self._compute_crop(frame_w, frame_h)
            self._last_frame_size = (frame_w, frame_h)

        src_x, src_y, src_w, src_h = self._crop
        screen_w, screen_h = self._screen_size

        # 1. Crop first (O(1) numpy slice — no data copy)
        frame = frame[src_y:src_y + src_h, src_x:src_x + src_w]

        # 2. Resize the small cropped region to screen size (faster than
        #    resizing the full frame then cropping)
        frame = cv2.resize(frame, (screen_w, screen_h), interpolation=cv2.INTER_LINEAR)

        # 3. BGR → RGB
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # 4. Transpose (H,W,3) → (W,H,3) into pre-allocated contiguous buffer
        np.copyto(self._pixel_buffer, frame.transpose(1, 0, 2))

        # 5. Blit into pre-allocated surface and flip — no heap allocation per frame
        pygame.surfarray.blit_array(self._display_surface, self._pixel_buffer)
        self._screen.blit(self._display_surface, (0, 0))
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
