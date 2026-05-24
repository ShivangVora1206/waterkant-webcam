#!/usr/bin/env bash
set -euo pipefail

INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="webcam.service"
SERVICE_SRC="$INSTALL_DIR/$SERVICE_NAME"
SERVICE_DEST="/etc/systemd/system/$SERVICE_NAME"

# Detect the real user: if this script is run with sudo, SUDO_USER is the
# original caller. If run as root directly, fall back to USER.
ACTUAL_USER="${SUDO_USER:-$USER}"

# Prefix commands with sudo when not running as root
if [[ $EUID -ne 0 ]]; then
    SUDO="sudo"
else
    SUDO=""
fi

echo "==> Installing for user: $ACTUAL_USER"
echo "==> Install directory:   $INSTALL_DIR"
echo ""

echo "==> Installing system dependencies..."
$SUDO apt-get update -qq
$SUDO apt-get install -y \
    python3-opencv \
    python3-pygame \
    python3-numpy \
    v4l-utils \
    libdrm2

# Add the exhibit user to the groups needed for direct framebuffer/DRM access
echo ""
echo "==> Configuring user groups for display access..."
$SUDO usermod -a -G video,render,input "$ACTUAL_USER"

# Disable the desktop display manager if present (it holds the DRM device
# exclusively, which would block our direct framebuffer rendering)
if systemctl is-enabled lightdm &>/dev/null 2>&1; then
    echo "==> Disabling lightdm (not needed for exhibit mode)..."
    $SUDO systemctl disable --now lightdm
fi

echo ""
echo "==> Installing systemd service..."
# Substitute __USER__ and __INSTALL_DIR__ placeholders with real values
sed \
    -e "s|__USER__|$ACTUAL_USER|g" \
    -e "s|__INSTALL_DIR__|$INSTALL_DIR|g" \
    "$SERVICE_SRC" | $SUDO tee "$SERVICE_DEST" > /dev/null

$SUDO systemctl daemon-reload
$SUDO systemctl enable "$SERVICE_NAME"

echo ""
echo "Installation complete."
echo ""
echo "Next step: add 'display_rotate=1' to /boot/firmware/config.txt if your"
echo "display is physically mounted in portrait orientation (-90°), then reboot."
echo ""
echo "Useful commands:"
echo "  Start now (without rebooting): sudo systemctl start $SERVICE_NAME"
echo "  Stop the exhibit:              sudo systemctl stop $SERVICE_NAME"
echo "  Restart after config change:   sudo systemctl restart $SERVICE_NAME"
echo "  View live logs:                journalctl -u $SERVICE_NAME -f"
