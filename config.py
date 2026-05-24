# -------------------------------------------------------------------
# Webcam Exhibit — Configuration
# All tunable parameters live here. Edit this file to adjust behavior.
# Restart the service after changes: systemctl restart webcam.service
# -------------------------------------------------------------------

# Camera
CAMERA_INDEX = None     # None = auto-detect Logitech Brio 105; set to 0 to force /dev/video0
CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720
CAMERA_FPS = 30
CAMERA_RECONNECT_ATTEMPTS = 30  # consecutive read failures before attempting a reconnect

# Display
# DISPLAY_ROTATION: degrees to rotate each frame before rendering.
# The physical display is mounted at -90° from landscape, so the default
# corrects for that by rotating frames 90° counter-clockwise.
# Valid values: 0, 90, -90, 180
DISPLAY_ROTATION = -90

DISPLAY_FULLSCREEN = True   # False opens a windowed display (useful for development)
FLIP_HORIZONTAL = False     # Mirror the image left-right
FLIP_VERTICAL = False       # Mirror the image top-bottom

# Performance
FRAME_BUFFER_SIZE = 1       # OpenCV internal capture buffer; keep at 1 to minimise latency

# Window
WINDOW_TITLE = "Webcam Exhibit"
