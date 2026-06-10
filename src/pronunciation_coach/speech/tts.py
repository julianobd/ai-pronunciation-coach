"""Text-to-speech for shadowing mode.

Default is Silero (torch.hub, offline after first download); fallback is
Windows SAPI via pyttsx3, which needs no downloads at all.
"""

from __future__ import annotations

import os
import tempfile
from typing import Protocol

import numpy as np

from ..paths import model_cache_dir


class TTSModel(Protocol):
    def synthesize(self, text: str) -> tuple[np.ndarray, int]:
        """Returns (float32 mono audio, sample_rate)."""
        ...


def resample_to_16k(audio: np.ndarray, sample_rate: int) -> np.ndarray:
    if sample_rate == 16000:
        return audio.astype(np.float32)
    target_len = int(len(audio) * 16000 / sample_rate)
    return np.interp(
        np.linspace(0, len(audio) - 1, target_len),
        np.arange(len(audio)),
        audio,
    ).astype(np.float32)


class SileroTTS:
    SAMPLE_RATE = 24000

    def __init__(self, speaker: str = "en_0") -> None:
        self.speaker = speaker
        self._model = None

    def load(self) -> None:
        if self._model is None:
            import torch

            torch.hub.set_dir(str(model_cache_dir() / "torch_hub"))
            self._model, _ = torch.hub.load(
                repo_or_dir="snakers4/silero-models",
                model="silero_tts",
                language="en",
                speaker="v3_en",
                trust_repo=True,
            )

    def synthesize(self, text: str) -> tuple[np.ndarray, int]:
        self.load()
        audio = self._model.apply_tts(
            text=text, speaker=self.speaker, sample_rate=self.SAMPLE_RATE
        )
        return np.asarray(audio, dtype=np.float32) * 0.8, self.SAMPLE_RATE


class SapiTTS:
    """Windows built-in voices via pyttsx3. Zero downloads."""

    def synthesize(self, text: str) -> tuple[np.ndarray, int]:
        import pyttsx3
        import soundfile as sf

        # Windows-safe tempfile pattern (see Legacy/lambdaSpeechToScore.py):
        # delete=False + explicit close before another process/library opens it.
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp_name = tmp.name
        tmp.close()
        try:
            engine = pyttsx3.init()
            engine.setProperty("rate", 165)
            engine.save_to_file(text, tmp_name)
            engine.runAndWait()
            audio, sample_rate = sf.read(tmp_name, dtype="float32")
            if audio.ndim > 1:
                audio = audio.mean(axis=1)
            return audio, sample_rate
        finally:
            try:
                os.remove(tmp_name)
            except OSError:
                pass


class FallbackTTS:
    """Tries the preferred engine, silently falls back to SAPI on failure."""

    def __init__(self, prefer: str = "auto") -> None:
        self.prefer = prefer
        self._primary: TTSModel | None = None
        self._sapi = SapiTTS()

    def _resolve_primary(self) -> TTSModel | None:
        if self.prefer == "sapi":
            return None
        try:
            import torch  # noqa: F401  - silero needs torch

            return SileroTTS()
        except ImportError:
            return None

    def synthesize(self, text: str) -> tuple[np.ndarray, int]:
        if self._primary is None and self.prefer != "sapi":
            self._primary = self._resolve_primary()
        if self._primary is not None:
            try:
                return self._primary.synthesize(text)
            except Exception:
                self._primary = None  # e.g. first-run download failed
        return self._sapi.synthesize(text)


def create_tts(prefer: str = "auto") -> TTSModel:
    return FallbackTTS(prefer)
