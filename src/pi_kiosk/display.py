"""Screen-side helpers: the panel backlight and the background images."""

from __future__ import annotations

import random
from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QImage, QImageReader, qRgb
from PySide6.QtQuick import QQuickImageProvider

BACKGROUNDS_DIR = Path(__file__).resolve().parent / "backgrounds"
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}


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


def pick_background(sound_id: str, root: Path = BACKGROUNDS_DIR) -> str:
    """A random image from backgrounds/<sound_id>/, as a path relative to `root` ("" if none)."""
    folder = root / sound_id
    images = [p for p in folder.glob("*") if p.suffix.lower() in IMAGE_SUFFIXES]
    return random.choice(images).relative_to(root).as_posix() if images else ""


def night_tint(image: QImage) -> QImage:
    """Dim red monochrome, matching the night palette. Done once per image on the CPU,
    with Qt's C++ conversions, so the Pi's GPU needs no shader."""
    gray = image.convertToFormat(QImage.Format.Format_Grayscale8)
    data = bytes(gray.constBits())
    tinted = QImage(data, gray.width(), gray.height(), gray.bytesPerLine(),
                    QImage.Format.Format_Indexed8)
    # Dark enough that the red clock text stays readable on top.
    table = []
    for g in range(256):
        r = round(80 * (g / 255) ** 1.2)
        table.append(qRgb(r, r // 12, r // 12))
    tinted.setColorTable(table)
    return tinted.convertToFormat(QImage.Format.Format_RGB32)  # also copies out of `data`


class BackgroundProvider(QQuickImageProvider):
    """Serves image://backgrounds/<day|night>/<sound>/<file>, decoded at screen size
    (a full-size camera JPEG would otherwise take ~50 MB of RAM)."""

    def __init__(self, root: Path = BACKGROUNDS_DIR) -> None:
        super().__init__(QQuickImageProvider.ImageType.Image)
        self._root = root.resolve()

    def requestImage(self, id: str, size: QSize, requested: QSize) -> QImage:  # noqa: N802
        mode, _, rel = id.partition("/")
        path = (self._root / rel).resolve()
        if self._root not in path.parents or not path.is_file():
            return QImage()
        reader = QImageReader(str(path))
        reader.setAutoTransform(True)  # honour camera rotation
        if requested.isValid() and not requested.isEmpty() and reader.size().isValid():
            reader.setScaledSize(reader.size().scaled(
                requested, Qt.AspectRatioMode.KeepAspectRatioByExpanding))
        image = reader.read()
        if image.isNull():
            print(f"[backgrounds] can't read {path}: {reader.errorString()}")
            return image
        return night_tint(image) if mode == "night" else image
