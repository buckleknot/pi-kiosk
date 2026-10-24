import time
import wave
from array import array

import pytest

from pi_kiosk.sound import CHUNK_SECONDS, FadingPlayer

RATE = 8000
LEVEL = 10_000


class FakeSink:
    """Records the peak level of every chunk instead of playing it."""

    opened: list["FakeSink"] = []

    def __init__(self, rate, channels):
        self.format = (rate, channels)
        self.peaks: list[int] = []
        self.closed = False
        FakeSink.opened.append(self)

    def write(self, data):
        self.peaks.append(max(abs(s) for s in array("h", data)))
        time.sleep(0.001)  # stand-in for the real device's pacing

    def close(self):
        self.closed = True


def make_wav(path, seconds, width=2):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(width)
        w.setframerate(RATE)
        n = int(RATE * seconds)
        w.writeframes(array("h", [LEVEL] * n).tobytes() if width == 2 else bytes([200]) * n)
    return path


def wait_for(cond, timeout=3.0):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if cond():
            return
        time.sleep(0.005)
    raise AssertionError("timed out")


@pytest.fixture
def player():
    FakeSink.opened = []
    return FadingPlayer(FakeSink, fade_seconds=4 * CHUNK_SECONDS)  # 4-chunk fades


def test_fades_in_then_plays_at_full_level(player, tmp_path):
    player.play(make_wav(tmp_path / "a.wav", 1.0), loop=True)
    wait_for(lambda: FakeSink.opened and len(FakeSink.opened[0].peaks) >= 6)
    peaks = FakeSink.opened[0].peaks
    assert peaks[0] < LEVEL * 0.1          # starts near silence
    assert peaks[:4] == sorted(peaks[:4])  # rising
    assert peaks[5] == LEVEL               # then untouched
    player.stop()


def test_stop_fades_out_then_releases_the_device(player, tmp_path):
    player.play(make_wav(tmp_path / "a.wav", 1.0), loop=True)
    wait_for(lambda: FakeSink.opened and len(FakeSink.opened[0].peaks) >= 6)
    player.stop()
    sink = FakeSink.opened[0]
    wait_for(lambda: sink.closed)
    tail = sink.peaks[-4:]
    assert tail == sorted(tail, reverse=True) and tail[-1] < LEVEL * 0.1


def test_short_file_loops_without_stopping(player, tmp_path):
    player.play(make_wav(tmp_path / "a.wav", 0.12), loop=True)  # ~2.4 chunks long
    wait_for(lambda: FakeSink.opened and len(FakeSink.opened[0].peaks) >= 12)
    assert not FakeSink.opened[0].closed
    player.stop()


def test_one_shot_ends_and_releases_the_device(player, tmp_path):
    player.play(make_wav(tmp_path / "a.wav", 0.12), loop=False)
    wait_for(lambda: FakeSink.opened and FakeSink.opened[0].closed)


def test_bad_file_doesnt_kill_the_player(player, tmp_path):
    player.play(make_wav(tmp_path / "8bit.wav", 0.5, width=1))
    player.play(tmp_path / "missing.wav")
    time.sleep(0.05)
    player.play(make_wav(tmp_path / "ok.wav", 1.0), loop=True)
    wait_for(lambda: FakeSink.opened and len(FakeSink.opened[-1].peaks) >= 2)
    player.stop()
