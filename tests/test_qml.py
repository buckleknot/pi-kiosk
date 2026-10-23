"""Loads the real QML offscreen and fails on any QML warning/error."""

from PySide6.QtQml import QQmlApplicationEngine

from pi_kiosk.app import MAIN_QML, QML_DIR
from pi_kiosk.backend import Backend


def load_main(fullscreen=False):
    backend = Backend()
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(lambda ws: warnings.extend(w.toString() for w in ws))
    engine.addImportPath(str(QML_DIR))
    engine.setInitialProperties({
        "backend": backend, "kioskFullscreen": fullscreen, "width": 800, "height": 480,
    })
    engine.load(MAIN_QML.as_uri())
    return engine, backend, warnings


def test_main_qml_loads_without_warnings(qtbot):
    engine, _, warnings = load_main()
    assert engine.rootObjects(), "Main.qml failed to load"
    assert warnings == []
    root = engine.rootObjects()[0]
    assert (root.width(), root.height()) == (800, 480)


def test_counter_binding_updates(qtbot):
    engine, backend, _ = load_main()
    root = engine.rootObjects()[0]
    backend.increment()
    labels = [o for o in root.findChildren(object) if o.property("text") == "1"]
    assert labels, "counter label did not update"
