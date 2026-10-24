"""Generate the bundled placeholder sounds (stdlib only, deterministic).

    python scripts/make_sounds.py

Writes 16 kHz mono WAVs into src/pi_kiosk/sounds/{ambient,alarm}/. Swap in your own
recordings any time: any WAV dropped into those folders shows up in Settings.
Ambient files are built so their end flows into their start, for gapless looping.
"""

from __future__ import annotations

import math
import random
import wave
from array import array
from pathlib import Path

RATE = 16_000
OUT = Path(__file__).resolve().parents[1] / "src" / "pi_kiosk" / "sounds"


def write(path: Path, samples: list[float], peak: float) -> None:
    scale = peak * 32767 / max(abs(s) for s in samples)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(array("h", (int(s * scale) for s in samples)).tobytes())
    print(f"wrote {path.relative_to(OUT.parent)}  ({path.stat().st_size // 1024} KB)")


def seamless(make, seconds: float, fade: float = 1.0) -> list[float]:
    """Render seconds+fade of audio, then crossfade the tail over the head so it loops."""
    n, f = int(seconds * RATE), int(fade * RATE)
    x = make(n + f)
    return [x[i] * i / f + x[n + i] * (1 - i / f) for i in range(f)] + x[f:n]


def lowpass(x: list[float], a: float) -> list[float]:
    out, y = [], 0.0
    for s in x:
        y += a * (s - y)
        out.append(y)
    return out


def brown(n: int, rng: random.Random) -> list[float]:
    out, y = [], 0.0
    for _ in range(n):
        y = 0.997 * y + rng.uniform(-1, 1) * 0.06
        out.append(y)
    return out


def rain(n: int) -> list[float]:
    rng = random.Random(1)
    hiss = lowpass([rng.uniform(-1, 1) for _ in range(n)], 0.35)
    for _ in range(n // 400):  # scattered drops: short decaying blips
        start, freq = rng.randrange(n), rng.uniform(1500, 4000)
        amp = rng.uniform(0.1, 0.5)
        for i in range(min(240, n - start)):
            hiss[start + i] += amp * math.exp(-i / 40) * math.sin(2 * math.pi * freq * i / RATE)
    return hiss


def ocean(n: int, period: float = 8.0) -> list[float]:
    rng = random.Random(2)
    surf = lowpass(brown(n, rng), 0.5)
    hiss = lowpass([rng.uniform(-1, 1) for _ in range(n)], 0.2)
    out = []
    for i in range(n):
        swell = (0.5 - 0.5 * math.cos(2 * math.pi * i / (period * RATE))) ** 2
        out.append(surf[i] * (0.3 + swell) + hiss[i] * 0.25 * swell)
    return out


def tone(seconds: float, notes: list[tuple[float, float]], decay: float,
         partials=((1, 1.0), (2.76, 0.4), (5.4, 0.15))) -> list[float]:
    """Bell-ish notes: (start_seconds, frequency) pairs over a silent bed."""
    n = int(seconds * RATE)
    out = [0.0] * n
    for start, freq in notes:
        s0 = int(start * RATE)
        for i in range(n - s0):
            t = i / RATE
            env = min(1.0, t * 200) * math.exp(-t / decay)
            out[s0 + i] += env * sum(a * math.sin(2 * math.pi * freq * m * t) for m, a in partials)
    return out


def beep(seconds: float = 2.0) -> list[float]:
    n = int(seconds * RATE)
    out = [0.0] * n
    for k in range(4):  # beep-beep-beep-beep, then a pause
        s0 = int(k * 0.2 * RATE)
        for i in range(int(0.1 * RATE)):
            env = min(1.0, i / 80, (int(0.1 * RATE) - i) / 80)
            out[s0 + i] = env * math.sin(2 * math.pi * 880 * i / RATE)
    return out


def main() -> None:
    write(OUT / "ambient" / "rain.wav", seamless(rain, 16), 0.5)
    write(OUT / "ambient" / "ocean-waves.wav", seamless(ocean, 16), 0.5)
    noise = seamless(lambda n: brown(n, random.Random(3)), 16)
    write(OUT / "ambient" / "brown-noise.wav", noise, 0.4)
    write(OUT / "alarm" / "chime.wav", tone(3.0, [(0, 659.3), (0.6, 523.3)], 0.6), 0.8)
    rising = tone(3.0, [(0, 523.3), (0.3, 659.3), (0.6, 784.0)], 0.4)
    write(OUT / "alarm" / "rising.wav", rising, 0.8)
    write(OUT / "alarm" / "beep.wav", beep(), 0.7)


if __name__ == "__main__":
    main()
