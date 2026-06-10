"""Reproduce the 'second analysis hangs forever' report.

Runs the same ASR analysis several times, each on a DIFFERENT thread
(like QThreadPool does in the app). If ctranslate2/OpenMP deadlocks on
cross-thread use, an iteration will time out.

Run:  python tests/manual_repeat_smoke.py
Exit: 0 = all iterations completed, 2 = hang detected
"""

import os
import sys
import threading
import time

sys.stdout.reconfigure(encoding="utf-8")

import soundfile as sf

from pronunciation_coach.core.analysis import PronunciationAnalyzer
from pronunciation_coach.speech.asr import FasterWhisperASR
from pronunciation_coach.speech.tts import SapiTTS, resample_to_16k

TEXT = "Think about three things."
ITERATIONS = 4
TIMEOUT_S = 120

audio, sr = SapiTTS().synthesize(TEXT)
audio16 = resample_to_16k(audio, sr)
print(f"test audio: {len(audio16)} samples")

analyzer = PronunciationAnalyzer(FasterWhisperASR("base.en"))

for i in range(ITERATIONS):
    done = {}

    def work():
        result = analyzer.analyze(audio16, TEXT)
        done["accuracy"] = result.overall_accuracy

    t = threading.Thread(target=work, name=f"analysis-{i}", daemon=True)
    start = time.time()
    t.start()
    t.join(timeout=TIMEOUT_S)
    if t.is_alive():
        print(f"HANG: iteration {i} did not finish within {TIMEOUT_S}s")
        os._exit(2)
    print(f"iteration {i}: accuracy={done['accuracy']} in {time.time()-start:.1f}s")

print("ALL ITERATIONS OK")
