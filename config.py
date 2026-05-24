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
# DISPLAY_ROTATION: degrees to rotate each captured frame in software before rendering.
#
# How to pick the right value:
#   0   — No rotation. The camera's native landscape frame (16:9) fills the KMS
#          screen (also 16:9) perfectly — no cropping, no bars. The physical −90°
#          display mount rotates the image for you. Use this when the camera is
#          mounted on the same frame as the display (both rotated together).
#  -90  — Rotate frame 90° CCW before display. Use when the camera is in a fixed
#          landscape position but the display is portrait AND you have configured
#          the OS to report portrait resolution (see README — Display Rotation).
#   90  — Rotate frame 90° CW.
#  180  — Flip upside-down.
#
# Start with 0. If the image appears sideways, try -90 or 90.
DISPLAY_ROTATION = 0

DISPLAY_FULLSCREEN = True   # False opens a windowed display (useful for development)
FLIP_HORIZONTAL = False     # Mirror the image left-right
FLIP_VERTICAL = False       # Mirror the image top-bottom

# Performance
FRAME_BUFFER_SIZE = 1       # OpenCV internal capture buffer; keep at 1 to minimise latency

# Window
WINDOW_TITLE = "Webcam Exhibit"
