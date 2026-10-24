from pi_kiosk.display import Backlight


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
