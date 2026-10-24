#!/usr/bin/env bash
# Run ON THE PI (Raspberry Pi OS Lite 64-bit, trixie) after the first deploy:
#   bash ~/pi-kiosk/deploy/pi/install.sh
set -euo pipefail
APP_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
USER_NAME="$(whoami)"

echo "== Installing PySide6 + Qt Quick from apt (system Qt with EGLFS/KMS) =="
sudo apt-get update
sudo apt-get install -y --no-install-recommends \
    python3 \
    python3-pyside6.qtcore python3-pyside6.qtgui python3-pyside6.qtnetwork \
    python3-pyside6.qtqml python3-pyside6.qtquick python3-pyside6.qtquickcontrols2 \
    qml6-module-qtquick qml6-module-qtquick-controls qml6-module-qtquick-layouts \
    qml6-module-qtquick-templates qml6-module-qtquick-window qml6-module-qtqml-workerscript \
    qt6-qpa-plugins libgles2 fonts-dejavu-core \
    alsa-utils  # aplay: plays the WAV sounds without a media framework

# Optional: tests on the Pi (uses apt so nothing is pip-installed system-wide)
sudo apt-get install -y --no-install-recommends python3-pytest python3-pytestqt || true

echo "== Groups for GPU (/dev/dri) and touch (/dev/input) =="
sudo usermod -aG video,render,input "$USER_NAME"

echo "== systemd service =="
sudo install -m 644 "$APP_DIR/deploy/pi/pi-kiosk@.service" /etc/systemd/system/
sudo sed -i "s|__APP_DIR__|$APP_DIR|g" /etc/systemd/system/pi-kiosk@.service
sudo systemctl daemon-reload
sudo systemctl enable --now "pi-kiosk@$USER_NAME"

echo
echo "Installed. Logs:  journalctl -u pi-kiosk@$USER_NAME -f"
echo "Tip: free RAM with 'sudo systemctl disable --now getty@tty1' (console login on the screen)."
