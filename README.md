# Webcam Exhibit

A minimal, production-ready fullscreen webcam stream for a Raspberry Pi 4B exhibit. On boot the Pi opens a bare X session and immediately fills the connected display with the live feed from a Logitech Brio 105 USB webcam. All display parameters — including rotation to compensate for portrait-mounted screens — are controlled from a single configuration file.

---

## Hardware Requirements

| Component | Spec |
|---|---|
| Single-board computer | Raspberry Pi 4B (2 GB RAM or more) |
| Webcam | Logitech Brio 105 (USB-A) |
| Display | 1920×1080 HDMI monitor |
| Power supply | Official Raspberry Pi 15 W USB-C PSU |
| Storage | 16 GB+ microSD (class 10 / A1) |
| OS | Raspberry Pi OS 64-bit Bookworm (Desktop or Lite) |

The display in this exhibit is mounted at **−90° from landscape** (portrait, cable at top). `config.py` and `/boot/firmware/config.txt` are configured for this orientation out of the box.

---

## Quick Start

1. **Flash the OS** — use Raspberry Pi Imager to write *Raspberry Pi OS (64-bit)* to the SD card. In the imager's advanced settings, set the hostname, enable SSH, and configure Wi-Fi if needed.

2. **Boot and connect** — insert the SD card, connect the Brio 105 via USB and the display via HDMI, then power on.

3. **Clone the project**
   ```bash
   git clone <repo-url> /home/pi/webcam
   cd /home/pi/webcam
   ```

4. **Run the installer**
   ```bash
   bash install.sh
   ```
   This installs all dependencies, copies the systemd service, and enables it on boot.

5. **Set display rotation in firmware** (for portrait-mounted displays)

   Open `/boot/firmware/config.txt` and add or edit:
   ```
   display_rotate=1
   ```
   This tells the GPU to report the screen as 1080×1920 (portrait). Combined with `DISPLAY_ROTATION = -90` in `config.py`, the webcam feed fills the portrait screen correctly.

6. **Reboot**
   ```bash
   sudo reboot
   ```
   The exhibit starts automatically. No login prompt will appear.

---

## Configuration Reference

All settings are in [`config.py`](config.py). Edit the file and restart the service to apply changes:

```bash
sudo systemctl restart webcam.service
```

| Variable | Type | Default | Description |
|---|---|---|---|
| `CAMERA_INDEX` | `int \| None` | `None` | Camera device index. `None` = auto-detect Brio 105 via `v4l2-ctl`; set to `0` to force `/dev/video0`. |
| `CAMERA_WIDTH` | `int` | `1920` | Requested capture width in pixels. |
| `CAMERA_HEIGHT` | `int` | `1080` | Requested capture height in pixels. |
| `CAMERA_FPS` | `int` | `30` | Requested capture frame rate. |
| `CAMERA_RECONNECT_ATTEMPTS` | `int` | `30` | Number of consecutive read failures before the camera connection is recycled. |
| `DISPLAY_ROTATION` | `int` | `-90` | Degrees to rotate each captured frame before rendering. Valid values: `0`, `90`, `-90`, `180`. |
| `DISPLAY_FULLSCREEN` | `bool` | `True` | `False` opens a windowed display — useful during development. |
| `FLIP_HORIZONTAL` | `bool` | `False` | Mirror the image left-to-right (selfie/mirror mode). |
| `FLIP_VERTICAL` | `bool` | `False` | Mirror the image top-to-bottom. |
| `FRAME_BUFFER_SIZE` | `int` | `1` | OpenCV internal capture buffer size. Keep at `1` to minimise display latency. |
| `WINDOW_TITLE` | `str` | `"Webcam Exhibit"` | X11 window title (not visible in fullscreen mode). |

---

## Display Rotation

The project corrects for a physically rotated monitor entirely in software — no X11 or xrandr rotation is used.

**How it works:**

1. The Brio 105 captures a 1920×1080 landscape frame.
2. `display.py` applies a −90° rotation (`cv2.ROTATE_90_COUNTERCLOCKWISE`), producing a 1080×1920 portrait frame.
3. Pygame scales this to fill the screen's reported resolution and blits it fullscreen.

**To change the rotation:**

Open `config.py` and set `DISPLAY_ROTATION` to the angle that compensates for your physical mount:

| Physical mount | `DISPLAY_ROTATION` value |
|---|---|
| Landscape (no rotation) | `0` |
| Portrait, cable at top (−90°) | `-90` |
| Portrait, cable at bottom (+90°) | `90` |
| Upside-down landscape | `180` |

Also update `/boot/firmware/config.txt` to match so the OS reports the correct resolution:

| `DISPLAY_ROTATION` | `display_rotate` in config.txt |
|---|---|
| `0` | `0` (or omit the line) |
| `-90` | `1` |
| `90` | `3` |
| `180` | `2` |

---

## Camera Troubleshooting

**List connected video devices:**
```bash
v4l2-ctl --list-devices
```
Look for a line containing `Brio`. The `/dev/videoN` path below it is the device node.

**Check available devices:**
```bash
ls /dev/video*
```

**Force a specific device index:**

If the Brio 105 is not at `/dev/video0`, set `CAMERA_INDEX` in `config.py`:
```python
CAMERA_INDEX = 2   # replace with the correct index
```
Then restart the service.

**Camera not detected at all:**

- Ensure the USB cable is plugged directly into a Pi USB-A port (not through a hub).
- Run `lsusb | grep -i logitech` — the Brio 105 should appear.
- Check `dmesg | tail -20` for USB enumeration errors.

---

## Viewing Logs

Stream live logs from the service:
```bash
journalctl -u webcam.service -f
```

Show the last 100 lines:
```bash
journalctl -u webcam.service -n 100
```

---

## Service Management

```bash
# Start the exhibit immediately (without rebooting)
sudo systemctl start webcam.service

# Stop the exhibit
sudo systemctl stop webcam.service

# Restart after a config change
sudo systemctl restart webcam.service

# Check current status
systemctl status webcam.service

# Disable autostart on boot
sudo systemctl disable webcam.service

# Re-enable autostart
sudo systemctl enable webcam.service
```

---

## Manual Run (Development)

To run the application outside of the systemd service — useful for testing on the Pi or on a desktop Linux machine with a webcam:

```bash
# On the Pi, if a display is connected
DISPLAY=:0 python3 main.py

# In a windowed mode (set DISPLAY_FULLSCREEN = False in config.py first)
python3 main.py
```

Press **ESC** to exit cleanly.

---

## Raspberry Pi OS Configuration Checklist

| Setting | Location | Recommended value |
|---|---|---|
| OS image | Raspberry Pi Imager | Raspberry Pi OS (64-bit) Bookworm |
| Display rotation | `/boot/firmware/config.txt` | `display_rotate=1` (for −90° portrait mount) |
| Auto-login | Not required | The service starts X directly — no desktop session needed |
| SSH | Raspberry Pi Imager (advanced) | Enable for remote management |
| Overscan | `/boot/firmware/config.txt` | `disable_overscan=1` (prevents black border on some displays) |

The systemd service starts a bare X session on VT1 directly, so a desktop environment (LXDE, etc.) is not required. Raspberry Pi OS Lite works fine and reduces boot time.
# waterkant-webcam
