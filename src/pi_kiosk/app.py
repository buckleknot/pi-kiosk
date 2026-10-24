"""Application entry point.

The same code runs on Windows (windowed 800x480 "simulator") and on the
Raspberry Pi (full screen via EGLFS, no desktop). Platform differences are
handled by command-line flags and environment variables, not code branches.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

QML_DIR = Path(__file__).resolve().parent / "qml"
MAIN_QML = QML_DIR / "Main.qml"
DEFAULT_SIZE = (800, 480)  # Official 7" DSI touchscreen


def is_raspberry_pi() -> bool:
    try:
        return "Raspberry Pi" in Path("/proc/device-tree/model").read_text(errors="ignore")
    except OSError:
        return False


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="pi-kiosk")
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--fullscreen", dest="fullscreen", action="store_true", default=None,
                      help="Run full screen (default on a Pi)")
    mode.add_argument("--windowed", dest="fullscreen", action="store_false",
                      help="Run in an 800x480 window (default elsewhere)")
    p.add_argument("--size", default=f"{DEFAULT_SIZE[0]}x{DEFAULT_SIZE[1]}",
                   help="Window size WxH when windowed (default %(default)s)")
    p.add_argument("--reload", action="store_true",
                   help="Hot-reload QML when files change (development)")
    args = p.parse_args(argv)
    if args.fullscreen is None:
        args.fullscreen = is_raspberry_pi()
    w, _, h = args.size.lower().partition("x")
    args.width, args.height = int(w), int(h)
    return args


def configure_environment() -> None:
    """Set Qt defaults *before* QGuiApplication is created."""
    # Material looks identical on Windows and Pi; theme/accent are set in Main.qml.
    os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Material")
    if is_raspberry_pi():
        os.environ.setdefault("QT_QPA_PLATFORM", "eglfs")
        os.environ.setdefault("QT_QPA_EGLFS_HIDECURSOR", "1")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    configure_environment()

    # Import Qt after the environment is configured.
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlApplicationEngine

    from .backend import Backend
    from .hotreload import QmlReloader

    app = QGuiApplication(sys.argv)
    app.setApplicationName("pi-kiosk")

    backend = Backend()
    engine = QQmlApplicationEngine()
    engine.addImportPath(str(QML_DIR))
    props = {
        "backend": backend,
        "kioskFullscreen": args.fullscreen,
        "width": args.width,
        "height": args.height,
    }
    engine.setInitialProperties(props)
    engine.load(MAIN_QML.as_uri())
    if not engine.rootObjects():
        return 1

    reloader = QmlReloader(engine, MAIN_QML, QML_DIR, props) if args.reload else None  # noqa: F841
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
