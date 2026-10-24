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
  settings.py     user settings, saved as JSON
  sound.py        WAV streaming with fade in/out (sounddevice on Windows, aplay on the Pi)
  display.py      backlight control + background image provider (night tint)
  hotreload.py    dev-only QML reload
  qml/Main.qml    root window: day/night colours, page stack, alarm overlay
  qml/pages/      ClockPage (home), ConfigPage (settings)
  qml/components/ reusable QML (BigButton, TimePicker, SoundPicker, AlarmPopup, Theme)
  sounds/         ambient/ and alarm/ WAVs, listed automatically in Settings
  backgrounds/    one folder per sound id (e.g. rain/), plus default/ for when nothing plays
tests/            pytest + pytest-qt (offscreen)
scripts/          setup-dev.ps1, deploy.ps1, make_sounds.py, make_backgrounds.py
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
- `QT_QUICK_CONTROLS_STYLE=Material` — same look on both platforms. `Basic` is lighter if RAM/GPU gets tight.
- The header shows the process's resident memory, so you can watch it as you build.
- `MemoryMax=300M` in the service restarts the app rather than letting it starve the OS.
- Prefer `Loader`/`StackView` to create screens on demand instead of keeping them all alive;
  keep images at screen resolution (800×480), not camera-size.
- Free more RAM on the Pi: `sudo systemctl disable --now getty@tty1 bluetooth ModemManager`
  (only those you don't need).

## Clock, alarm and sounds

- Night mode (dim red on black) runs between the times set in Settings; otherwise stock
  Material colours. Alarm and night times, and the chosen sounds, are saved to
  `%APPDATA%\pi-kiosk\settings.json` on Windows and `~/.config/pi-kiosk/settings.json` on the Pi.
- The moon/sun button (top left) flips day/night now; the schedule takes over again at
  its next switch. The slider below it sets brightness; day and night each remember
  their own level. On the Pi it drives the panel backlight (`/sys/class/backlight`, permission via a udev rule from
  `install.sh`); without one, e.g. on Windows, the picture is dimmed in software instead.
  The right-hand slider sets the volume (the alarm never plays below 50%).
- While a sound plays (Relax or the alarm), a picture from `backgrounds/<sound id>/` fills
  the screen, chosen at random if there are several; otherwise one from `backgrounds/default/`.
  Pictures crossfade when they change, including on the day/night switch. Drop in
  JPEG/PNG photos of any size: they're decoded at screen size, and at night turned into dim red monochrome.
  The bundled ones are placeholders: `python scripts/make_backgrounds.py`.
- Sounds are plain WAV files in `src/pi_kiosk/sounds/ambient` (Relax) and `.../alarm`.
  Drop more in and they appear in Settings (`ocean-waves.wav` shows as "Ocean waves").
  The bundled ones are generated placeholders: `python scripts/make_sounds.py`.
  16 kHz mono keeps them small; ambient files should loop cleanly end-to-start.
  They must be 16-bit PCM. Sounds fade in over 2 s and out over 2 s (`FADE_SECONDS`).
- The Pi Zero 2 W has no headphone jack: audio needs a USB sound card or an I2S
  amp/DAC board (or HDMI). Check with `aplay -l` and `aplay some.wav` on the Pi.

## Notes

- Windows can't emulate the Pi's speed or GPU (VideoCore IV, OpenGL ES 2.0). Deploy early
  and often; avoid heavy shader effects and big blurs.
- Rotate the panel 180°: uncomment `QT_QPA_EGLFS_ROTATION` in `deploy/pi/pi-kiosk@.service`.
- CI: `.github/workflows/tests.yml` runs tests on Windows and Linux ARM64 if you push to GitHub.
