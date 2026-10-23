import os
import sys
from pathlib import Path

# Headless Qt for tests (works on Windows, Linux CI and the Pi over SSH).
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")

# Allow running tests without `pip install -e .` (e.g. on the Pi).
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
