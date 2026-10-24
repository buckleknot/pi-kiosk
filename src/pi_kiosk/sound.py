"""Plays one sound at a time: ambient loops, alarms and previews share the channel.

The app streams the WAV itself, a few milliseconds at a time, so it can fade the
volume in and out and loop without a gap. The audio goes to a "sink": `aplay` on
the Pi (no media framework needed; QtMultimedia pulls in FFmpeg/GStreamer) and
PortAudio via the `sounddevice` package on Windows.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import threading
import wave
from array import array
from pathlib import Path

from PySide6.QtCore import QObject

FADE_SECONDS = 2.0
CHUNK_SECONDS = 0.05


class SoundPlayer(QObject):
    """Silent fallback when no audio backend is available (e.g. CI)."""

    def play(self, path: Path, loop: bool = False) -> None:
        print(f"[sound] no audio backend; would play {path.name}")

    def stop(self) -> None:
        pass

    def set_volume(self, level: float) -> None:
        """0.0 (silent) to 1.0 (as recorded)."""


class AplaySink:
    """Raw PCM into `aplay` on stdin, with small buffers so fades react quickly."""

    def __init__(self, rate: int, channels: int) -> None:
        self._proc = subprocess.Popen(
            ["aplay", "-q", "-t", "raw", "-f", "S16_LE", "-r", str(rate), "-c", str(channels),
             "--buffer-time=200000", "-"],
            stdin=subprocess.PIPE, bufsize=0,
        )
        try:  # default 64 KB pipe would add ~2 s of lag before a fade-out is heard
            import fcntl
            fcntl.fcntl(self._proc.stdin, fcntl.F_SETPIPE_SZ, 4096)
        except (ImportError, AttributeError, OSError):
            pass

    def write(self, data: bytes) -> None:
        self._proc.stdin.write(data)

    def close(self) -> None:
        self._proc.stdin.close()
        try:
            self._proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            self._proc.kill()


class SounddeviceSink:
    def __init__(self, rate: int, channels: int) -> None:
        import sounddevice
        self._stream = sounddevice.RawOutputStream(rate, channels=channels, dtype="int16")
        self._stream.start()

    def write(self, data: bytes) -> None:
        self._stream.write(data)  # blocks until there's room, which paces the stream

    def close(self) -> None:
        self._stream.stop()  # lets the buffered audio finish
        self._stream.close()


class FadingPlayer(SoundPlayer):
    """Fades in on play, fades out on stop, and fades across when the sound changes.

    A worker thread does the streaming; play()/stop() just leave it a request.
    Only 16-bit WAVs are supported (any rate, mono or stereo).
    """

    def __init__(self, open_sink, parent: QObject | None = None,
                 fade_seconds: float = FADE_SECONDS) -> None:
        super().__init__(parent)
        self._open_sink = open_sink  # (rate, channels) -> object with write()/close()
        self._fade = fade_seconds
        self._cond = threading.Condition()
        self._request: tuple[Path, bool] | None = None
        self._pending = False
        # Everything below belongs to the worker thread.
        self._sink, self._fmt = None, None
        self._reader: wave.Wave_read | None = None
        self._loop, self._gain = False, 0.0
        self._volume = self._level = 1.0  # requested / last applied output level
        threading.Thread(target=self._run, name="sound", daemon=True).start()

    def play(self, path: Path, loop: bool = False) -> None:
        self._post((path, loop))

    def stop(self) -> None:
        self._post(None)

    def set_volume(self, level: float) -> None:
        self._volume = max(0.0, min(1.0, level)) ** 2  # squared: even steps to the ear

    def _post(self, request: tuple[Path, bool] | None) -> None:
        with self._cond:
            self._request, self._pending = request, True
            self._cond.notify()

    def _run(self) -> None:
        while True:
            try:
                self._step()
            except Exception as e:  # a bad file or device mustn't kill the thread
                print(f"[sound] {type(e).__name__}: {e}")
                self._close_reader()
                self._close_sink()

    def _step(self) -> None:
        with self._cond:
            if self._reader is None and not self._pending:
                self._close_sink()  # idle: release the audio device
                self._cond.wait()
            pending = self._pending

        if pending and (self._reader is None or self._gain <= 0):
            with self._cond:  # take the newest request now the old sound is silent
                request, self._pending = self._request, False
            self._close_reader()
            if request:
                self._reader, self._loop, self._gain = _open_wav(request[0]), request[1], 0.0
                self._level = self._volume
                fmt = (self._reader.getframerate(), self._reader.getnchannels())
                if self._fmt != fmt:
                    self._close_sink()
                if self._sink is None:
                    self._sink, self._fmt = self._open_sink(*fmt), fmt
            return

        rate, channels = self._fmt
        want = int(rate * CHUNK_SECONDS)
        frames = self._reader.readframes(want)
        if len(frames) < 2 * channels * want and self._loop:
            self._reader.rewind()  # top up from the start so the loop has no gap
            frames += self._reader.readframes(want - len(frames) // (2 * channels))
        if not frames:
            self._close_reader()
            return

        step = CHUNK_SECONDS / self._fade
        target = max(0.0, self._gain - step) if pending else min(1.0, self._gain + step)
        level = self._volume
        # Fade and volume both glide across the chunk, so neither causes a click.
        self._sink.write(_scale(frames, self._gain ** 2 * self._level, target ** 2 * level))
        self._gain, self._level = target, level

    def _close_reader(self) -> None:
        if self._reader:
            self._reader.close()
            self._reader = None

    def _close_sink(self) -> None:
        if self._sink:
            sink, self._sink, self._fmt = self._sink, None, None
            sink.close()


def _open_wav(path: Path) -> wave.Wave_read:
    reader = wave.open(str(path), "rb")
    if reader.getsampwidth() != 2:
        reader.close()
        raise ValueError("only 16-bit WAV files are supported")
    return reader


def _scale(frames: bytes, start: float, end: float) -> bytes:
    """Scale 16-bit samples by a gain sliding from `start` to `end`.
    WAV and both sinks are little-endian, as is the Pi."""
    if start == end == 1.0:
        return frames
    samples = array("h", frames)
    if start == end:
        return array("h", [int(s * start) for s in samples]).tobytes()
    n = len(samples) or 1
    for i, s in enumerate(samples):
        samples[i] = int(s * (start + (end - start) * i / n))
    return samples.tobytes()


def create_player(parent: QObject | None = None) -> SoundPlayer:
    if sys.platform == "win32":
        try:
            import sounddevice  # noqa: F401
            return FadingPlayer(SounddeviceSink, parent)
        except (ImportError, OSError):
            return SoundPlayer(parent)
    if shutil.which("aplay"):
        return FadingPlayer(AplaySink, parent)
    return SoundPlayer(parent)
