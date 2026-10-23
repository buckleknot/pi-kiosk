"""Python objects exposed to QML.

Keep logic here (testable without a screen); keep QML for presentation only.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Property, QObject, QTimer, Signal, Slot


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


class Backend(QObject):
    counterChanged = Signal()
    timeChanged = Signal()
    memoryChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._counter = 0
        self._time = ""
        self._memory = 0.0

        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)
        self._timer.start()
        self._tick()

    # --- counter ---------------------------------------------------------
    def _get_counter(self) -> int:
        return self._counter

    counter = Property(int, _get_counter, notify=counterChanged)

    @Slot()
    def increment(self) -> None:
        self._counter += 1
        self.counterChanged.emit()

    @Slot()
    def reset(self) -> None:
        if self._counter:
            self._counter = 0
            self.counterChanged.emit()

    # --- clock / stats ---------------------------------------------------
    def _get_time(self) -> str:
        return self._time

    time = Property(str, _get_time, notify=timeChanged)

    def _get_memory(self) -> float:
        return self._memory

    memoryMb = Property(float, _get_memory, notify=memoryChanged)

    def _tick(self) -> None:
        now = datetime.now().strftime("%H:%M:%S")
        if now != self._time:
            self._time = now
            self.timeChanged.emit()
        mem = round(process_memory_mb(), 1)
        if mem != self._memory:
            self._memory = mem
            self.memoryChanged.emit()

    @Slot(result=str)
    def platform(self) -> str:
        return sys.platform
