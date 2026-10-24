"""User settings, persisted as JSON so they survive restarts."""

from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass, fields
from pathlib import Path


def default_settings_path() -> Path:
    """%APPDATA%/pi-kiosk on Windows, ~/.config/pi-kiosk on the Pi.

    PI_KIOSK_SETTINGS overrides it (the tests use this to stay out of your real settings).
    """
    override = os.environ.get("PI_KIOSK_SETTINGS")
    if override:
        return Path(override)
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home()))
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "pi-kiosk" / "settings.json"


@dataclass
class Settings:
    night_start: str = "21:00"
    night_end: str = "07:00"
    alarm_time: str = "07:00"
    alarm_enabled: bool = False
    ambient_sound: str = "rain"
    alarm_sound: str = "chime"

    @classmethod
    def load(cls, path: Path) -> Settings:
        """Read settings, falling back to defaults for anything missing or malformed."""
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return cls()
        if not isinstance(data, dict):
            return cls()
        defaults = cls()
        return cls(**{
            f.name: data[f.name] for f in fields(cls)
            if isinstance(data.get(f.name), type(getattr(defaults, f.name)))
        })

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")
        tmp.replace(path)  # atomic, so a power cut never leaves a half-written file
