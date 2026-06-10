"""Manual end-to-end smoke: TTS -> wav -> ASR -> phoneme analysis.

Run:  python tests/manual_smoke.py
"""

import os
import sys
import tempfile

import soundfile as sf

sys.stdout.reconfigure(encoding="utf-8")

from pronunciation_coach.speech.tts import SapiTTS, resample_to_16k

TEXT = "Think about three things."

audio, sr = SapiTTS().synthesize(TEXT)
print(f"TTS ok: {len(audio)} samples at {sr} Hz")

wav_path = os.path.join(tempfile.gettempdir(), "coach_smoke.wav")
sf.write(wav_path, resample_to_16k(audio, sr), 16000)
print("wav written:", wav_path)

from pronunciation_coach.core.analysis import PronunciationAnalyzer
from pronunciation_coach.speech.asr import FasterWhisperASR

audio16, _ = sf.read(wav_path, dtype="float32")
analyzer = PronunciationAnalyzer(FasterWhisperASR("base.en"))
analysis = analyzer.analyze(audio16, TEXT)
print("transcript:", analysis.transcript)
print("accuracy:", analysis.overall_accuracy)
print("word timestamps:", analysis.word_timestamps)
print("errors:", analysis.phoneme_errors[:5])
assert analysis.overall_accuracy > 60, "TTS speech should score reasonably"
print("SMOKE OK")
