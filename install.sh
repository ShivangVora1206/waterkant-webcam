#!/usr/bin/env bash
set -euo pipefail

INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="webcam.service"
SERVICE_SRC="$INSTALL_DIR/$SERVICE_NAME"
SERVICE_DEST="/etc/systemd/system/$SERVICE_NAME"

# Prefix commands with sudo when not running as root
if [[ $EUID -ne 0 ]]; then
    SUDO="sudo"
else
    SUDO=""
fi

echo "==> Installing system dependencies..."
$SUDO apt-get update -qq
$SUDO apt-get install -y \
    python3-opencv \
    python3-pygame \
    python3-numpy \
    v4l-utils \
    xinit \
    xserver-xorg \
    x11-xserver-utils

echo ""
echo "==> Installing systemd service..."
$SUDO cp "$SERVICE_SRC" "$SERVICE_DEST"
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
