"""Development-only QML hot reload: save a .qml file and the UI rebuilds."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QFileSystemWatcher, QObject, QTimer
from PySide6.QtQml import QQmlApplicationEngine


class QmlReloader(QObject):
    def __init__(self, engine: QQmlApplicationEngine, main_qml: Path, qml_dir: Path,
                 initial_props: dict) -> None:
        super().__init__(engine)
        # Reuse the originals rather than reading them back from the old window: a QML
        # edit that drops a property would otherwise pass None on to every later reload.
        self._props = initial_props
        self._engine = engine
        self._main = main_qml
        self._dir = qml_dir
        self._watcher = QFileSystemWatcher(self)
        self._debounce = QTimer(self, singleShot=True, interval=200)
        self._debounce.timeout.connect(self._reload)
        self._watcher.fileChanged.connect(lambda _: self._debounce.start())
        self._watcher.directoryChanged.connect(lambda _: self._debounce.start())
        self._watch()
        print(f"[hot-reload] watching {qml_dir}")

    def _watch(self) -> None:
        files = [str(p) for p in self._dir.rglob("*.qml")]
        dirs = [str(p) for p in self._dir.rglob("*") if p.is_dir()] + [str(self._dir)]
        old = self._watcher.files() + self._watcher.directories()
        if old:
            self._watcher.removePaths(old)
        self._watcher.addPaths(files + dirs)  # editors often replace files, so re-add

    def _reload(self) -> None:
        for obj in self._engine.rootObjects():
            obj.close()
            obj.deleteLater()
        self._engine.clearComponentCache()
        self._engine.setInitialProperties(self._props)
        self._engine.load(self._main.as_uri())
        self._watch()
        ok = bool(self._engine.rootObjects())
        print("[hot-reload] reloaded" if ok else "[hot-reload] QML error - fix and save again")
