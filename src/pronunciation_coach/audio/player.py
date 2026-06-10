"""Audio playback via sounddevice."""

from __future__ import annotations

import numpy as np
import sounddevice as sd
from PySide6.QtCore import QObject, Signal


class AudioPlayer(QObject):
    error = Signal(str)

    def play(self, audio: np.ndarray, sample_rate: int = 16000) -> None:
        try:
            sd.stop()
            sd.play(np.asarray(audio, dtype=np.float32), samplerate=sample_rate)
        except Exception as exc:
            self.error.emit(f"Audio playback failed: {exc}")

    def stop(self) -> None:
        sd.stop()
