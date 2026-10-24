"""Loads the real QML offscreen and fails on any QML warning/error."""

from datetime import datetime

from PySide6.QtCore import QObject, QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from pi_kiosk.app import MAIN_QML, QML_DIR
from pi_kiosk.backend import Backend
from pi_kiosk.display import BackgroundProvider
from pi_kiosk.settings import Settings
from pi_kiosk.sound import SoundPlayer


def make_backend(tmp_path, hhmm="12:00", **settings):
    path = tmp_path / "settings.json"
    Settings(**settings).save(path)
    h, m = map(int, hhmm.split(":"))
    return Backend(settings_path=path, player=SoundPlayer(),
                   clock=lambda: datetime(2026, 10, 23, h, m))


def load_main(backend, fullscreen=False):
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(lambda ws: warnings.extend(w.toString() for w in ws))
    engine.addImportPath(str(QML_DIR))
    engine.addImageProvider("backgrounds", BackgroundProvider())
    engine.setInitialProperties({
        "backend": backend, "kioskFullscreen": fullscreen, "width": 800, "height": 480,
    })
    engine.load(MAIN_QML.as_uri())
    return engine, warnings


def texts(root):
    return {o.property("text") for o in root.findChildren(QObject)} - {None}


def test_main_qml_loads_without_warnings(qtbot, tmp_path):
    backend = make_backend(tmp_path, "12:34")  # keep a reference: QML doesn't own it
    engine, warnings = load_main(backend)
    assert engine.rootObjects(), "Main.qml failed to load"
    assert warnings == []
    root = engine.rootObjects()[0]
    assert (root.width(), root.height()) == (800, 480)
    assert {"12:34", "Relax", "Alarm off", "Settings", "auto", "70%"} <= texts(root)


def test_night_mode_and_ringing_alarm_load_without_warnings(qtbot, tmp_path):
    backend = make_backend(tmp_path, "23:00", alarm_enabled=True, alarm_time="23:00")
    assert backend.nightMode and backend.alarmRinging
    engine, warnings = load_main(backend)
    assert engine.rootObjects() and warnings == []
    assert {"Snooze 9 min", "Stop"} <= texts(engine.rootObjects()[0])


def test_relax_button_binding_updates(qtbot, tmp_path):
    backend = make_backend(tmp_path)
    engine, _ = load_main(backend)
    backend.toggleRelax()
    assert "Stop" in texts(engine.rootObjects()[0])


def test_backgrounds_load_without_warnings_day_and_night(qtbot, tmp_path):
    backend = make_backend(tmp_path)
    engine, warnings = load_main(backend)
    backend.toggleRelax()
    qtbot.wait(100)
    backend.toggleNight()
    qtbot.wait(100)
    assert warnings == []


def test_config_page_loads_without_warnings(qtbot, tmp_path):
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(lambda ws: warnings.extend(w.toString() for w in ws))
    backend = make_backend(tmp_path, alarm_time="06:45")
    comp = QQmlComponent(engine, QUrl.fromLocalFile(str(QML_DIR / "pages" / "ConfigPage.qml")))
    page = comp.createWithInitialProperties({"backend": backend})
    assert page is not None, comp.errorString()
    assert warnings == []
    assert {"Night starts", "Alarm", "Relax sound", "Preview"} <= texts(page)
