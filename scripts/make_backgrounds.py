"""Generate placeholder backgrounds, one folder per sound (deterministic).

    python scripts/make_backgrounds.py

Writes 800x480 JPEGs into src/pi_kiosk/backgrounds/<sound id>/. Replace them with
real photos any time: every JPEG/PNG in a sound's folder is a candidate, and one is
picked at random each time that sound starts. Night versions are made on the fly.
"""

from __future__ import annotations

import math
import os
import random
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QPointF, QRectF, Qt  # noqa: E402
from PySide6.QtGui import (  # noqa: E402
    QBrush,
    QColor,
    QGuiApplication,
    QImage,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QRadialGradient,
)

W, H = 800, 480
OUT = Path(__file__).resolve().parents[1] / "src" / "pi_kiosk" / "backgrounds"


def canvas(*stops: tuple[float, str]) -> tuple[QImage, QPainter]:
    image = QImage(W, H, QImage.Format.Format_RGB32)
    p = QPainter(image)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    sky = QLinearGradient(0, 0, 0, H)
    for at, colour in stops:
        sky.setColorAt(at, QColor(colour))
    p.fillRect(0, 0, W, H, sky)
    return image, p


def glow(p: QPainter, x: float, y: float, r: float, colour: str, alpha: int) -> None:
    g = QRadialGradient(QPointF(x, y), r)
    c = QColor(colour)
    c.setAlpha(alpha)
    g.setColorAt(0, c)
    c.setAlpha(0)
    g.setColorAt(1, c)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(g))
    p.drawEllipse(QPointF(x, y), r, r)


def waves(p: QPainter, base: float, colours: list[str], amp: float, rng: random.Random) -> None:
    for i, colour in enumerate(colours):
        y0, phase, k = base + i * 38, rng.uniform(0, 6), rng.uniform(0.008, 0.014)
        path = QPainterPath(QPointF(0, H))
        for x in range(0, W + 10, 10):
            path.lineTo(x, y0 + amp * math.sin(k * x + phase) + amp / 2 * math.sin(2.3 * k * x))
        path.lineTo(W, H)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(colour))
        p.drawPath(path)


def save(image: QImage, p: QPainter, sound: str, name: str = "") -> None:
    p.end()
    path = OUT / sound / f"{name or sound}.jpg"
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(str(path), "JPG", 85)
    print(f"wrote {path.relative_to(OUT.parent)}  ({path.stat().st_size // 1024} KB)")


def main() -> None:
    rng = random.Random(7)

    image, p = canvas((0, "#3b4a5a"), (1, "#1c2630"))  # rain: slate sky, streaks
    glow(p, 600, 80, 380, "#8fa3b5", 70)
    p.setPen(QPen(QColor(200, 215, 230, 60), 1.4))
    for _ in range(420):
        x, y, n = rng.uniform(-100, W), rng.uniform(-50, H), rng.uniform(18, 46)
        p.drawLine(QPointF(x, y), QPointF(x + n * 0.25, y + n))
    save(image, p, "rain")

    image, p = canvas((0, "#f6d6a8"), (0.45, "#9cc3d6"), (1, "#1f5f7a"))  # ocean
    glow(p, 400, 215, 160, "#fff1d0", 200)
    waves(p, 250, ["#5f9fb8", "#3f86a3", "#2b6f8d", "#1b5873", "#11445c"], 10, rng)
    save(image, p, "ocean-waves")

    image, p = canvas((0, "#6b4a35"), (1, "#2a1c14"))  # brown noise: warm, soft
    for _ in range(14):
        glow(p, rng.uniform(0, W), rng.uniform(0, H), rng.uniform(80, 220), "#c08a5a",
             rng.randint(25, 60))
    save(image, p, "brown-noise")

    image, p = canvas((0, "#2d2a5a"), (0.55, "#c76b6b"), (1, "#f2b56b"))  # chime: dawn
    glow(p, 400, 470, 260, "#ffd28a", 220)
    waves(p, 400, ["#4a3550", "#2f2238"], 14, rng)
    save(image, p, "chime")

    image, p = canvas((0, "#1d3557"), (0.6, "#e07a5f"), (1, "#f4d35e"))  # rising: sunrise
    glow(p, 400, 420, 120, "#fff4c2", 255)
    glow(p, 400, 420, 320, "#ffd27a", 120)
    p.setBrush(QColor("#22223b"))
    p.drawRect(QRectF(0, 420, W, 60))
    save(image, p, "rising")

    image, p = canvas((0, "#4fa3e0"), (1, "#cfe8f7"))  # beep: bright morning
    glow(p, 640, 110, 70, "#fffbe0", 255)
    glow(p, 640, 110, 200, "#fff3b0", 110)
    for cx, cy, s in [(180, 140, 1.0), (420, 90, 0.7), (300, 300, 1.2)]:
        for dx, dy, r in [(0, 0, 40), (35, 8, 32), (-35, 10, 30), (15, -20, 30)]:
            glow(p, cx + dx * s, cy + dy * s, r * s * 1.4, "#ffffff", 200)
    save(image, p, "beep")

    # Idle scenes ("default" folder): shown whenever nothing is playing.
    image, p = canvas((0, "#7aa7d9"), (0.55, "#f3c9a8"), (1, "#f7e3c3"))  # hills at dusk
    glow(p, 560, 250, 70, "#fff6dc", 255)
    glow(p, 560, 250, 260, "#ffd9a8", 120)
    for i, colour in enumerate(["#a7b9d6", "#8aa1c4", "#6a86ad", "#4d6b93", "#35517a"]):
        path, y0 = QPainterPath(QPointF(0, H)), 250 + i * 45
        phase, k = rng.uniform(0, 6), rng.uniform(0.004, 0.008)
        for x in range(0, W + 10, 10):
            path.lineTo(x, y0 - 40 * math.sin(k * x + phase) - 15 * math.sin(3.1 * k * x))
        path.lineTo(W, H)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(colour))
        p.drawPath(path)
    save(image, p, "default", "hills")

    image, p = canvas((0, "#0f2a44"), (0.5, "#3f6e8c"), (0.62, "#9fc2c9"), (1, "#204a5c"))  # lake
    glow(p, 250, 120, 120, "#e8f3ff", 60)
    peaks = [(0, 300), (120, 190), (230, 260), (360, 150), (500, 250), (620, 180), (800, 290)]
    for flip in (1, -1):  # the range and its reflection in the water
        path = QPainterPath(QPointF(0, 300))
        for x, y in peaks:
            path.lineTo(x, 300 + flip * (y - 300))
        path.lineTo(W, 300)
        path.closeSubpath()
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#1d3b52" if flip == 1 else "#2c5468"))
        p.drawPath(path)
    p.setPen(QPen(QColor(255, 255, 255, 40), 2))
    for _ in range(40):  # ripples
        x, y = rng.uniform(0, W), rng.uniform(320, H)
        p.drawLine(QPointF(x, y), QPointF(x + rng.uniform(20, 70), y))
    save(image, p, "default", "lake")


if __name__ == "__main__":
    app = QGuiApplication([])
    main()
