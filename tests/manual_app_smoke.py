"""Boot the full app offscreen for 4 seconds and exit. Verifies wiring.

Run:  python tests/manual_app_smoke.py
"""

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

import pronunciation_coach.app as app_module

_orig_exec = QApplication.exec


def _exec_with_quit(*_args, **_kwargs):
    QTimer.singleShot(4000, QApplication.instance().quit)
    return _orig_exec()


QApplication.exec = _exec_with_quit

rc = app_module.main()
print("APP SMOKE OK, exit code:", rc)
sys.exit(rc)
