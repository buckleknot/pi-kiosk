import os
import sys
import tempfile
from pathlib import Path

# Headless Qt for tests (works on Windows, Linux CI and the Pi over SSH).
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Material")
# Never read or overwrite the real settings file.
os.environ["PI_KIOSK_SETTINGS"] = str(Path(tempfile.mkdtemp()) / "settings.json")

# Allow running tests without `pip install -e .` (e.g. on the Pi).
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
