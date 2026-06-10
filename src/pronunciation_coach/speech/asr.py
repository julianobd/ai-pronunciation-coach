"""Speech-to-text. faster-whisper (CTranslate2) with word timestamps.

The ASRModel protocol keeps the analyzer model-agnostic so a phoneme-level
recognizer (e.g. wav2vec2) can be swapped in later.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

import numpy as np

from ..paths import model_cache_dir

SAMPLE_RATE = 16000


@dataclass
class WordStamp:
    word: str
    start_s: float
    end_s: float


@dataclass
class ASRResult:
    text: str
    words: list[WordStamp] = field(default_factory=list)


class ASRModel(Protocol):
    def transcribe(self, audio: np.ndarray) -> ASRResult:
        """audio: float32 mono at 16 kHz."""
        ...


class FasterWhisperASR:
    def __init__(self, model_size: str = "base.en", device: str = "cpu",
                 compute_type: str = "int8") -> None:
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self._model = None

    def load(self) -> None:
        """Download (first run) and load the model. Safe to call twice."""
        if self._model is None:
            from faster_whisper import WhisperModel

            self._model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
                download_root=str(model_cache_dir()),
            )

    def transcribe(self, audio: np.ndarray) -> ASRResult:
        self.load()
        audio = np.asarray(audio, dtype=np.float32).flatten()
        segments, _info = self._model.transcribe(
            audio,
            language="en",
            word_timestamps=True,
            vad_filter=True,
            temperature=0.0,
            condition_on_previous_text=False,
            beam_size=5,
        )
        words: list[WordStamp] = []
        texts: list[str] = []
        for segment in segments:
            texts.append(segment.text.strip())
            for w in segment.words or []:
                words.append(WordStamp(w.word.strip(), float(w.start), float(w.end)))
        return ASRResult(text=" ".join(t for t in texts if t), words=words)
