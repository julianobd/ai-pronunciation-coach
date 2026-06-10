"""Reproduce lost worker results through the real Qt path.

Submits N analyses through PracticeService (QThreadPool + queued signals),
waiting for each analysis_ready before submitting the next. If a result is
dropped (signals object deleted before queued delivery), the run times out.

Run:  python tests/manual_qt_repeat_smoke.py
Exit: 0 = all delivered, 2 = a result was lost (UI would hang forever)
"""

import os
import sys
import tempfile
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.stdout.reconfigure(encoding="utf-8")

from PySide6.QtCore import QCoreApplication, QTimer

from pronunciation_coach.core.analysis import PronunciationAnalyzer
from pronunciation_coach.persistence.db import Database
from pronunciation_coach.persistence.repository import AttemptRepo, PhonemeStatsRepo
from pronunciation_coach.services.practice_service import PracticeService
from pronunciation_coach.speech.asr import FasterWhisperASR
from pronunciation_coach.speech.tts import SapiTTS, resample_to_16k

TEXT = "Think about three things."
ITERATIONS = 10
PER_ITERATION_TIMEOUT_MS = 60000

audio, sr = SapiTTS().synthesize(TEXT)
audio16 = resample_to_16k(audio, sr)

app = QCoreApplication(sys.argv)

db = Database(os.path.join(tempfile.mkdtemp(), "repeat.db"))
service = PracticeService(
    PronunciationAnalyzer(FasterWhisperASR("base.en")),
    AttemptRepo(db),
    PhonemeStatsRepo(db),
)

state = {"done": 0, "started_at": time.time()}

watchdog = QTimer()
watchdog.setSingleShot(True)


def submit_next():
    watchdog.start(PER_ITERATION_TIMEOUT_MS)
    service.submit_recording(audio16, TEXT)


def on_ready(analysis):
    watchdog.stop()
    state["done"] += 1
    print(f"iteration {state['done']}: accuracy={analysis.overall_accuracy} "
          f"({time.time() - state['started_at']:.1f}s elapsed)")
    if state["done"] >= ITERATIONS:
        print("ALL ITERATIONS DELIVERED")
        app.exit(0)
    else:
        submit_next()


def on_failed(message):
    print("WORKER ERROR:", message)
    app.exit(3)


def on_timeout():
    print(f"HANG: iteration {state['done'] + 1} result never delivered "
          f"(UI would show 'Analyzing…' forever)")
    app.exit(2)


service.analysis_ready.connect(on_ready)
service.analysis_failed.connect(on_failed)
watchdog.timeout.connect(on_timeout)

QTimer.singleShot(0, submit_next)
sys.exit(app.exec())
