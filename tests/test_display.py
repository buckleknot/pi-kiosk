from PySide6.QtCore import QSize
from PySide6.QtGui import QColor, QImage

from pi_kiosk.display import (
    BACKGROUNDS_DIR,
    BackgroundProvider,
    Backlight,
    button_tint,
    night_tint,
    pick_background,
)


def make_image(path, w=400, h=200, colour="#4080c0"):
    path.parent.mkdir(parents=True, exist_ok=True)
    image = QImage(w, h, QImage.Format.Format_RGB32)
    image.fill(QColor(colour))
    assert image.save(str(path))
    return path


def test_pick_background_only_from_that_sounds_folder(tmp_path):
    make_image(tmp_path / "rain" / "a.png")
    (tmp_path / "rain" / "notes.txt").write_text("not an image")
    make_image(tmp_path / "ocean" / "b.png")
    assert pick_background("rain", tmp_path) == "rain/a.png"
    assert pick_background("missing", tmp_path) == ""


def test_every_bundled_sound_has_a_background():
    sounds = BACKGROUNDS_DIR.parent / "sounds"
    for wav in sounds.glob("*/*.wav"):
        assert pick_background(wav.stem), f"no background for {wav.stem}"
    assert pick_background("default"), "no idle scene"


def test_night_tint_is_dark_red_monochrome():
    image = QImage(4, 4, QImage.Format.Format_RGB32)
    image.fill(QColor("white"))
    c = QColor(night_tint(image).pixel(0, 0))
    assert c.red() <= 80 and c.green() < c.red() / 5 and c.blue() < c.red() / 5


def test_provider_scales_to_cover_and_tints_at_night(tmp_path):
    make_image(tmp_path / "rain" / "big.png", 1600, 800)
    provider = BackgroundProvider(tmp_path)
    day = provider.requestImage("day/rain/big.png", QSize(), QSize(800, 480))
    assert (day.width(), day.height()) == (960, 480)  # covers 800x480, aspect kept
    night = provider.requestImage("night/rain/big.png", QSize(), QSize(800, 480))
    c = QColor(night.pixel(10, 10))
    assert c.red() > c.green() and c.red() > c.blue()


def test_provider_refuses_paths_outside_its_folder(tmp_path):
    make_image(tmp_path / "secret.png")
    provider = BackgroundProvider(tmp_path / "backgrounds")
    assert provider.requestImage("day/../secret.png", QSize(), QSize()).isNull()


def test_backlight_writes_scaled_value(tmp_path):
    dev = tmp_path / "10-0045"
    dev.mkdir()
    (dev / "max_brightness").write_text("255\n")
    (dev / "brightness").write_text("255\n")
    light = Backlight(tmp_path)
    assert light.available
    assert light.set_percent(50)
    assert (dev / "brightness").read_text() == "128"


def test_missing_backlight_means_software_dimming(tmp_path):
    assert not Backlight(tmp_path / "none").available


def test_button_tint_is_a_light_version_of_the_picture(tmp_path):
    tint = QColor(button_tint(make_image(tmp_path / "blue.png", colour="#2050c0")))
    assert tint.blue() > tint.green() > tint.red()  # still blue
    assert min(tint.red(), tint.green(), tint.blue()) > 140  # but light, for dark text
    assert 180 < tint.alpha() < 255  # and a little see-through
    assert button_tint(tmp_path / "missing.png") == "#e0e0e0"
