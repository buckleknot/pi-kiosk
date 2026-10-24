from datetime import datetime, time, timedelta

import pytest

from pi_kiosk.backend import SOUNDS_DIR, Backend, is_night, list_sounds, process_memory_mb
from pi_kiosk.settings import Settings
from pi_kiosk.sound import SoundPlayer


class FakePlayer(SoundPlayer):
    def __init__(self):
        super().__init__()
        self.playing = None  # (file name, loop) or None
        self.volume = None

    def play(self, path, loop=False):
        self.playing = (path.name, loop)

    def stop(self):
        self.playing = None

    def set_volume(self, level):
        self.volume = level


class Clock:
    def __init__(self, hhmm="12:00"):
        h, m = map(int, hhmm.split(":"))
        self.now = datetime(2026, 10, 23, h, m)

    def __call__(self):
        return self.now

    def advance(self, **kw):
        self.now += timedelta(**kw)


@pytest.fixture
def make(tmp_path):
    def make(hhmm="12:00", **settings):
        path = tmp_path / "settings.json"
        if settings:
            Settings(**settings).save(path)
        clock, player = Clock(hhmm), FakePlayer()
        b = Backend(settings_path=path, player=player, clock=clock)
        return b, clock, player
    return make


@pytest.mark.parametrize("now,start,end,expected", [
    ("22:00", "21:00", "07:00", True),    # window wraps past midnight
    ("03:00", "21:00", "07:00", True),
    ("07:00", "21:00", "07:00", False),   # end is exclusive
    ("12:00", "21:00", "07:00", False),
    ("14:00", "13:00", "15:00", True),    # same-day window
    ("16:00", "13:00", "15:00", False),
    ("12:00", "09:00", "09:00", False),   # empty window = never night
])
def test_is_night(now, start, end, expected):
    def t(s):
        return time.fromisoformat(s)
    assert is_night(t(now), t(start), t(end)) is expected


def test_clock_is_populated(make):
    b, _, _ = make("09:05")
    assert b.time == "09:05"
    assert b.date == "Friday 23 October"


def test_night_mode_follows_clock_and_settings(make, qtbot):
    b, clock, _ = make("20:59")
    assert not b.nightMode
    clock.advance(minutes=1)
    with qtbot.waitSignal(b.nightModeChanged, timeout=1500):
        pass  # next timer tick
    assert b.nightMode
    b.nightStart = "23:00"
    assert not b.nightMode


def test_night_toggle_overrides_until_the_next_scheduled_switch(make):
    b, clock, _ = make("20:00")  # day; night starts 21:00
    b.toggleNight()
    assert b.nightMode and b.nightOverridden
    clock.advance(minutes=30)
    b._tick()
    assert b.nightMode and b.nightOverridden  # override holds
    clock.advance(minutes=30)
    b._tick()
    assert b.nightMode and not b.nightOverridden  # 21:00: schedule agrees, back to auto
    b.toggleNight()
    assert not b.nightMode and b.nightOverridden
    b.toggleNight()
    assert b.nightMode and not b.nightOverridden  # toggling back = auto again


def test_volume_is_applied_saved_and_clamped(make, tmp_path, qtbot):
    b, _, player = make()
    assert player.volume == 0.7
    b.volume = 30
    assert player.volume == 0.3
    b.volume = 250
    assert b.volume == 100
    qtbot.waitUntil(lambda: Settings.load(tmp_path / "settings.json").volume == 100, timeout=2000)


def test_alarm_never_plays_below_minimum_volume(make):
    b, clock, player = make("06:59", alarm_enabled=True, alarm_time="07:00", volume=10)
    assert player.volume == 0.1
    clock.advance(minutes=1)
    b._tick()
    assert player.volume == 0.5
    b.stopAlarm()
    assert player.volume == 0.1


class FakeBacklight:
    available = True

    def __init__(self):
        self.percent = None

    def set_percent(self, percent):
        self.percent = percent
        return True


def test_brightness_is_remembered_separately_for_day_and_night(tmp_path, qtbot):
    light = FakeBacklight()
    clock = Clock("20:00")
    b = Backend(settings_path=tmp_path / "s.json", player=FakePlayer(), clock=clock,
                backlight=light)
    assert b.hardwareBrightness and b.brightness == 100 and light.percent == 100
    b.brightness = 60
    b.toggleNight()
    assert b.brightness == 30 and light.percent == 30  # night default
    b.brightness = 2
    assert b.brightness == 5  # never fully dark
    b.toggleNight()
    assert b.brightness == 60 and light.percent == 60
    qtbot.waitUntil(lambda: Settings.load(tmp_path / "s.json").night_brightness == 5, timeout=2000)


def test_background_follows_what_is_playing_and_night_mode(make):
    b, clock, _ = make("06:59", alarm_enabled=True, alarm_time="07:00")
    idle = b.backgroundSource
    assert idle.startswith("image://backgrounds/night/default/")  # idle scene, 06:59 = night
    b.toggleRelax()
    assert b.backgroundSource == "image://backgrounds/night/rain/rain.jpg"
    b.toggleNight()
    assert b.backgroundSource == "image://backgrounds/day/rain/rain.jpg"
    clock.advance(minutes=1)
    b._tick()  # alarm takes over, with its own picture
    assert b.backgroundSource.endswith("/chime/chime.jpg")
    b.stopAlarm()
    assert "/default/" in b.backgroundSource
    idle = b.backgroundSource
    b.previewSound("ambient", "rain")
    b.stopPreview()
    assert b.backgroundSource == idle  # stays put while idle: no reshuffling


def test_sound_without_pictures_falls_back_to_the_idle_scene(make, tmp_path):
    (tmp_path / "bg" / "default").mkdir(parents=True)
    (tmp_path / "bg" / "default" / "calm.png").write_bytes(b"")  # name is all that's checked
    clock = Clock("12:00")
    b = Backend(settings_path=tmp_path / "s.json", player=FakePlayer(), clock=clock,
                backgrounds_dir=tmp_path / "bg")
    b.toggleRelax()
    assert b.backgroundSource == "image://backgrounds/day/default/calm.png"


def test_settings_persist_and_bad_times_are_ignored(make, tmp_path):
    b, _, _ = make()
    b.alarmTime = "06:30"
    b.nightStart = "25:99"
    b2 = Backend(settings_path=tmp_path / "settings.json", player=FakePlayer())
    assert b2.alarmTime == "06:30"
    assert b2.nightStart == "21:00"


def test_corrupt_settings_fall_back_to_defaults(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text('{"alarm_time": 7, "night_end": "05:00"')  # truncated JSON
    assert Settings.load(path) == Settings()
    path.write_text('{"alarm_time": 7, "night_end": "05:00"}')  # wrong type is dropped
    assert Settings.load(path) == Settings(night_end="05:00")


def test_alarm_rings_once_and_stops(make):
    b, clock, player = make("06:59", alarm_enabled=True, alarm_time="07:00")
    assert not b.alarmRinging
    clock.advance(minutes=1)
    b._tick()
    assert b.alarmRinging
    assert player.playing == ("chime.wav", True)
    b.stopAlarm()
    assert not b.alarmRinging and player.playing is None
    clock.advance(seconds=30)
    b._tick()
    assert not b.alarmRinging  # same minute: doesn't ring again


def test_alarm_disabled_never_rings(make):
    b, _, player = make("07:00", alarm_enabled=False, alarm_time="07:00")
    b._tick()
    assert not b.alarmRinging and player.playing is None


def test_snooze_rings_again_after_nine_minutes(make):
    b, clock, _ = make("07:00", alarm_enabled=True, alarm_time="07:00")
    assert b.alarmRinging
    b.snoozeAlarm()
    assert not b.alarmRinging
    clock.advance(minutes=8, seconds=59)
    b._tick()
    assert not b.alarmRinging
    clock.advance(seconds=1)
    b._tick()
    assert b.alarmRinging


def test_turning_alarm_off_silences_it(make):
    b, _, player = make("07:00", alarm_enabled=True, alarm_time="07:00")
    b.alarmEnabled = False
    assert not b.alarmRinging and player.playing is None


def test_relax_toggles_ambient_loop_and_alarm_takes_over(make):
    b, clock, player = make("06:59", alarm_enabled=True, alarm_time="07:00")
    b.toggleRelax()
    assert b.relaxing and player.playing == ("rain.wav", True)
    b.ambientSound = "ocean-waves"
    assert player.playing == ("ocean-waves.wav", True)
    clock.advance(minutes=1)
    b._tick()
    assert not b.relaxing and player.playing == ("chime.wav", True)
    b.stopAlarm()
    b.toggleRelax()
    b.toggleRelax()
    assert not b.relaxing and player.playing is None


def test_preview(make):
    b, _, player = make()
    b.previewSound("alarm", "beep")
    assert b.previewing == "alarm/beep" and player.playing == ("beep.wav", True)
    b.stopPreview()
    assert b.previewing == "" and player.playing is None


def test_missing_sound_falls_back_to_first_in_folder(make):
    b, _, player = make(ambient_sound="deleted-file")
    b.toggleRelax()
    assert player.playing == ("brown-noise.wav", True)


def test_bundled_sounds_cover_the_defaults():
    ambient = [s["id"] for s in list_sounds(SOUNDS_DIR / "ambient")]
    alarm = [s["id"] for s in list_sounds(SOUNDS_DIR / "alarm")]
    assert Settings().ambient_sound in ambient
    assert Settings().alarm_sound in alarm
    assert {"id": "ocean-waves", "name": "Ocean waves"} in list_sounds(SOUNDS_DIR / "ambient")


def test_memory_reading_is_non_negative():
    assert process_memory_mb() >= 0
