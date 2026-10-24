"""Python objects exposed to QML.

Keep logic here (testable without a screen); keep QML for presentation only.
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from datetime import datetime, time, timedelta
from pathlib import Path

from PySide6.QtCore import Property, QObject, QTimer, Signal, Slot

from .settings import Settings, default_settings_path
from .sound import SoundPlayer, create_player

SOUNDS_DIR = Path(__file__).resolve().parent / "sounds"
SNOOZE = timedelta(minutes=9)
KINDS = ("ambient", "alarm")  # sub-folders of sounds/, also the `kind` QML passes in


def process_memory_mb() -> float:
    """Resident memory of this process in MB (best effort, cross-platform)."""
    status = Path("/proc/self/status")
    if status.exists():
        for line in status.read_text().splitlines():
            if line.startswith("VmRSS:"):
                return int(line.split()[1]) / 1024
    try:
        import psutil  # optional, used on Windows in dev
        return psutil.Process().memory_info().rss / (1024 * 1024)
    except ImportError:
        return 0.0


def parse_hhmm(text: str) -> time | None:
    try:
        return datetime.strptime(text, "%H:%M").time()
    except (TypeError, ValueError):
        return None


def is_night(now: time, start: time, end: time) -> bool:
    """True if `now` is in [start, end); the window may wrap past midnight."""
    if start == end:
        return False
    if start < end:
        return start <= now < end
    return now >= start or now < end


def list_sounds(folder: Path) -> list[dict]:
    """[{"id": "ocean-waves", "name": "Ocean waves"}, ...] for every WAV in `folder`."""
    return [
        {"id": p.stem, "name": p.stem.replace("-", " ").replace("_", " ").capitalize()}
        for p in sorted(folder.glob("*.wav"))
    ]


class Backend(QObject):
    timeChanged = Signal()
    memoryChanged = Signal()
    nightModeChanged = Signal()
    settingsChanged = Signal()
    alarmRingingChanged = Signal()
    playingChanged = Signal()

    def __init__(
        self,
        parent: QObject | None = None,
        *,
        settings_path: Path | None = None,
        sounds_dir: Path = SOUNDS_DIR,
        player: SoundPlayer | None = None,
        clock: Callable[[], datetime] = datetime.now,
    ) -> None:
        super().__init__(parent)
        self._settings_path = settings_path or default_settings_path()
        self._settings = Settings.load(self._settings_path)
        self._sounds_dir = sounds_dir
        self._player = player or create_player(self)
        self._clock = clock

        self._time = ""
        self._date = ""
        self._memory = 0.0
        self._night = False
        self._ringing = False
        self._playing = ""            # "", "relax", "alarm" or "preview"
        self._preview = ""            # "<kind>/<id>" while previewing
        self._last_alarm: datetime | None = None  # minute it last rang, so it rings once
        self._snooze_until: datetime | None = None

        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)
        self._timer.start()
        self._tick()

    # --- clock / stats ---------------------------------------------------
    def _get_time(self) -> str:
        return self._time

    time = Property(str, _get_time, notify=timeChanged)

    def _get_date(self) -> str:
        return self._date

    date = Property(str, _get_date, notify=timeChanged)

    def _get_memory(self) -> float:
        return self._memory

    memoryMb = Property(float, _get_memory, notify=memoryChanged)

    def _get_night(self) -> bool:
        return self._night

    nightMode = Property(bool, _get_night, notify=nightModeChanged)

    def _tick(self) -> None:
        now = self._clock()
        hhmm, date = now.strftime("%H:%M"), f"{now:%A} {now.day} {now:%B}"
        if (hhmm, date) != (self._time, self._date):
            self._time, self._date = hhmm, date
            self.timeChanged.emit()
        mem = round(process_memory_mb(), 1)
        if mem != self._memory:
            self._memory = mem
            self.memoryChanged.emit()
        self._update_night(now)
        self._check_alarm(now)

    def _update_night(self, now: datetime) -> None:
        s = self._settings
        night = is_night(now.time(), parse_hhmm(s.night_start), parse_hhmm(s.night_end))
        if night != self._night:
            self._night = night
            self.nightModeChanged.emit()

    # --- settings (each change is saved straight away) --------------------
    def _set(self, key: str, value) -> None:
        if getattr(self._settings, key) == value:
            return
        setattr(self._settings, key, value)
        try:
            self._settings.save(self._settings_path)
        except OSError as e:
            print(f"[settings] could not save {self._settings_path}: {e}")
        self.settingsChanged.emit()
        self._update_night(self._clock())

    def _time_setting(key: str, notify: Signal) -> Property:  # noqa: N805 (class-body helper)
        def setter(self, value: str) -> None:
            if parse_hhmm(value):
                self._set(key, value)
        return Property(str, lambda self: getattr(self._settings, key), setter, notify=notify)

    nightStart = _time_setting("night_start", settingsChanged)
    nightEnd = _time_setting("night_end", settingsChanged)
    alarmTime = _time_setting("alarm_time", settingsChanged)
    del _time_setting

    def _get_alarm_enabled(self) -> bool:
        return self._settings.alarm_enabled

    def _set_alarm_enabled(self, on: bool) -> None:
        self._snooze_until = None
        if not on:
            self.stopAlarm()
        self._set("alarm_enabled", bool(on))

    alarmEnabled = Property(bool, _get_alarm_enabled, _set_alarm_enabled, notify=settingsChanged)

    def _get_ambient(self) -> str:
        return self._settings.ambient_sound

    def _set_ambient(self, sound_id: str) -> None:
        self._set("ambient_sound", sound_id)
        if self._playing == "relax":  # swap the sound that's playing
            self._play("relax", self._sound_path("ambient", sound_id), loop=True)

    ambientSound = Property(str, _get_ambient, _set_ambient, notify=settingsChanged)

    def _get_alarm_sound(self) -> str:
        return self._settings.alarm_sound

    def _set_alarm_sound(self, sound_id: str) -> None:
        self._set("alarm_sound", sound_id)

    alarmSound = Property(str, _get_alarm_sound, _set_alarm_sound, notify=settingsChanged)

    def _get_ambient_sounds(self) -> list:
        return list_sounds(self._sounds_dir / "ambient")

    ambientSounds = Property(list, _get_ambient_sounds, constant=True)

    def _get_alarm_sounds(self) -> list:
        return list_sounds(self._sounds_dir / "alarm")

    alarmSounds = Property(list, _get_alarm_sounds, constant=True)

    # --- playback ----------------------------------------------------------
    def _sound_path(self, kind: str, sound_id: str) -> Path | None:
        """The chosen WAV, or the first one in the folder if it has gone missing."""
        folder = self._sounds_dir / kind
        path = folder / f"{sound_id}.wav"
        if path.exists():
            return path
        return next(iter(sorted(folder.glob("*.wav"))), None)

    def _play(self, what: str, path: Path | None, loop: bool) -> None:
        self._player.stop()
        if path:
            self._player.play(path, loop)
        self._set_playing(what if path else "")

    def _stop(self) -> None:
        self._player.stop()
        self._set_playing("")

    def _set_playing(self, what: str) -> None:
        if what != "preview":
            self._preview = ""
        if what != self._playing or what == "preview":
            self._playing = what
            self.playingChanged.emit()

    def _get_relaxing(self) -> bool:
        return self._playing == "relax"

    relaxing = Property(bool, _get_relaxing, notify=playingChanged)

    def _get_previewing(self) -> str:
        return self._preview

    previewing = Property(str, _get_previewing, notify=playingChanged)

    @Slot()
    def toggleRelax(self) -> None:
        if self._playing == "relax":
            self._stop()
        else:
            self._play("relax", self._sound_path("ambient", self._settings.ambient_sound), True)

    @Slot(str, str)
    def previewSound(self, kind: str, sound_id: str) -> None:
        if kind not in KINDS:
            return
        path = self._sound_path(kind, sound_id)
        self._player.stop()
        if path:
            self._player.play(path, loop=True)
            self._preview = f"{kind}/{sound_id}"
            self._set_playing("preview")
        else:
            self._set_playing("")

    @Slot()
    def stopPreview(self) -> None:
        if self._playing == "preview":
            self._stop()

    # --- alarm -------------------------------------------------------------
    def _get_ringing(self) -> bool:
        return self._ringing

    alarmRinging = Property(bool, _get_ringing, notify=alarmRingingChanged)

    def _check_alarm(self, now: datetime) -> None:
        if self._ringing or not self._settings.alarm_enabled:
            return
        minute = now.replace(second=0, microsecond=0)
        if self._snooze_until and now >= self._snooze_until:
            self._snooze_until = None
        elif now.strftime("%H:%M") != self._settings.alarm_time or minute == self._last_alarm:
            return
        self._last_alarm = minute
        self._ringing = True
        self._play("alarm", self._sound_path("alarm", self._settings.alarm_sound), loop=True)
        self.alarmRingingChanged.emit()

    def _silence(self) -> None:
        if self._playing == "alarm":
            self._stop()
        if self._ringing:
            self._ringing = False
            self.alarmRingingChanged.emit()

    @Slot()
    def stopAlarm(self) -> None:
        self._snooze_until = None
        self._silence()

    @Slot()
    def snoozeAlarm(self) -> None:
        if self._ringing:
            self._snooze_until = self._clock() + SNOOZE
            self._silence()

    @Slot(result=str)
    def platform(self) -> str:
        return sys.platform
