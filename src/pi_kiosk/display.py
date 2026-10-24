"""Screen-side helpers: the panel backlight."""

from __future__ import annotations

from pathlib import Path


class Backlight:
    """The display's backlight via /sys/class/backlight (the official Pi panels).

    Not available on Windows; the UI then dims in software instead. Writing needs
    the udev rule from deploy/pi/install.sh.
    """

    def __init__(self, root: Path = Path("/sys/class/backlight")) -> None:
        devices = sorted(d for d in root.glob("*") if (d / "max_brightness").exists())
        self._device = devices[0] if devices else None

    @property
    def available(self) -> bool:
        return self._device is not None

    def set_percent(self, percent: int) -> bool:
        """Returns False (and stops trying) if the backlight can't be written."""
        if not self._device:
            return False
        try:
            top = int((self._device / "max_brightness").read_text())
            (self._device / "brightness").write_text(str(max(1, round(top * percent / 100))))
            return True
        except (OSError, ValueError) as e:
            print(f"[backlight] {e}; falling back to software dimming")
            self._device = None
            return False
