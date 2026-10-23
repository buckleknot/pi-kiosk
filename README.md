# pi-kiosk

Full-screen PySide6 + QML app for a **Raspberry Pi Zero 2 W (512 MB)** with the official
**800×480 DSI touchscreen**, developed on Windows.

## How it fits together

| | Windows (dev) | Raspberry Pi (target) |
|---|---|---|
| OS | Windows 10/11 | Raspberry Pi OS **Lite 64-bit** (Debian 13 trixie) |
| PySide6 | pip `PySide6-Essentials==6.8.2.1` in `.venv` | apt `python3-pyside6.*` (6.8.2) |
| Display | 800×480 window (`--windowed`) | Full screen via **EGLFS/KMS**, no desktop |
| Run | `python -m pi_kiosk --reload` | systemd service `pi-kiosk@<user>` |

PySide6 comes from apt on the Pi because Debian's build uses the system Qt with the
EGLFS/KMS backend and shared libraries — lighter and better integrated than a pip wheel.
Windows is pinned to the same version so behaviour matches. If `apt-cache policy
python3-pyside6.qtquick` on the Pi shows a different version, update `requirements-dev.txt`.

## Windows setup (once)

Needs Python 3.13 (python.org installer, with the `py` launcher) and Git.

```powershell
cd C:\dev\pi-kiosk
powershell -ExecutionPolicy Bypass -File scripts\setup-dev.ps1
.\.venv\Scripts\Activate.ps1
```

## Daily loop

```powershell
python -m pi_kiosk --reload   # 800x480 window; save any .qml file and it reloads
pytest                        # backend unit tests + loads Main.qml headless, fails on QML warnings
ruff check .
```

VS Code: open the folder, F5 runs "pi-kiosk (800x480, hot reload)".
Esc quits the app.

## Project layout

```
src/pi_kiosk/
  app.py          entry point, CLI flags, platform defaults
  backend.py      Python objects exposed to QML (put logic here — it's unit-testable)
  hotreload.py    dev-only QML reload
  qml/Main.qml    root window
  qml/components/ reusable QML (BigButton, Theme singleton)
tests/            pytest + pytest-qt (offscreen)
scripts/          setup-dev.ps1, deploy.ps1
deploy/pi/        install.sh + systemd unit for the Pi
```

## Pi setup (once)

1. Flash **Raspberry Pi OS Lite (64-bit)** with Raspberry Pi Imager. In its settings set
   hostname `kiosk`, your username, Wi-Fi and **enable SSH**.
2. From Windows: `.\scripts\deploy.ps1 -PiHost <user>@kiosk.local`
3. On the Pi: `bash ~/pi-kiosk/deploy/pi/install.sh` — installs packages, adds the
   systemd service, starts the app full screen. Reboot once so group changes apply.

After that, every change is just `.\scripts\deploy.ps1 -PiHost <user>@kiosk.local`
(copies files, restarts the service). Logs: `journalctl -u pi-kiosk@<user> -f`.
Run tests on the device: `cd ~/pi-kiosk && python3 -m pytest`.

## Keeping it inside 512 MB

- No desktop: EGLFS renders straight to DRM/KMS (saves ~100 MB vs X/Wayland).
- `QT_QUICK_CONTROLS_STYLE=Basic` — lightest Controls style, same look on both platforms.
- The header shows the process's resident memory, so you can watch it as you build.
- `MemoryMax=300M` in the service restarts the app rather than letting it starve the OS.
- Prefer `Loader`/`StackView` to create screens on demand instead of keeping them all alive;
  keep images at screen resolution (800×480), not camera-size.
- Free more RAM on the Pi: `sudo systemctl disable --now getty@tty1 bluetooth ModemManager`
  (only those you don't need).

## Notes

- Windows can't emulate the Pi's speed or GPU (VideoCore IV, OpenGL ES 2.0). Deploy early
  and often; avoid heavy shader effects and big blurs.
- Rotate the panel 180°: uncomment `QT_QPA_EGLFS_ROTATION` in `deploy/pi/pi-kiosk@.service`.
- CI: `.github/workflows/tests.yml` runs tests on Windows and Linux ARM64 if you push to GitHub.
