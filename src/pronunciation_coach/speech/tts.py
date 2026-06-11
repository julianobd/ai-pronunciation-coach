"""Text-to-speech for shadowing mode.

Engine order (auto): OmniVoice (k2-fsa, best quality) -> Silero -> Windows
SAPI via pyttsx3, which needs no downloads at all. SAPI explicitly picks an
English voice so a Portuguese (or any non-English) Windows still sounds right.
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


class OmniVoiceTTS:
    """k2-fsa OmniVoice — zero-shot voice design TTS (`pip install omnivoice`).

    Highest quality engine; GPU recommended (CPU works but is slower).
    """

    SAMPLE_RATE = 24000

    def __init__(self, instruct: str = "female, medium pitch, american accent") -> None:
        self.instruct = instruct
        self._model = None

    def load(self) -> None:
        if self._model is None:
            # Keep the HF download inside the app's model cache like the
            # other engines, unless the user already configured HF_HOME.
            os.environ.setdefault("HF_HOME", str(model_cache_dir() / "hf"))
            import torch
            from omnivoice import OmniVoice

            if torch.cuda.is_available():
                device_map, dtype = "cuda:0", torch.float16
            else:
                device_map, dtype = "cpu", torch.float32
            self._model = OmniVoice.from_pretrained(
                "k2-fsa/OmniVoice", device_map=device_map, dtype=dtype
            )

    def synthesize(self, text: str) -> tuple[np.ndarray, int]:
        self.load()
        # generate() returns a list of float waveforms, one per input text.
        waves = self._model.generate(text=text, instruct=self.instruct)
        audio = np.asarray(waves[0], dtype=np.float32).flatten()
        peak = float(np.max(np.abs(audio))) if audio.size else 0.0
        if peak > 1.0:
            audio = audio / peak
        return audio * 0.8, self.SAMPLE_RATE


class SapiTTS:
    """Windows built-in voices via pyttsx3. Zero downloads."""

    @staticmethod
    def _pick_english_voice(engine) -> None:
        # On non-English Windows the default SAPI voice matches the OS
        # language and reads English text with that accent — prefer an
        # installed English voice instead.
        try:
            for voice in engine.getProperty("voices"):
                haystack = f"{voice.id} {voice.name}".lower()
                if "en-us" in haystack or "en_us" in haystack or "english" in haystack:
                    engine.setProperty("voice", voice.id)
                    return
            for voice in engine.getProperty("voices"):
                if "en-" in f"{voice.id} {voice.name}".lower():
                    engine.setProperty("voice", voice.id)
                    return
        except Exception:
            pass  # keep the default voice

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
            self._pick_english_voice(engine)
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


def _has_module(name: str) -> bool:
    import importlib.util

    return importlib.util.find_spec(name) is not None


class FallbackTTS:
    """Tries the preferred engines in order, silently falling back to SAPI."""

    def __init__(self, prefer: str = "auto") -> None:
        self.prefer = prefer
        self._chain: list[TTSModel] | None = None
        self._sapi = SapiTTS()

    def _build_chain(self) -> list[TTSModel]:
        has_torch = _has_module("torch")
        has_omnivoice = has_torch and _has_module("omnivoice")
        if self.prefer == "omnivoice":
            return [OmniVoiceTTS()] if has_omnivoice else []
        if self.prefer == "silero":
            return [SileroTTS()] if has_torch else []
        if self.prefer == "sapi":
            return []
        chain: list[TTSModel] = []  # auto
        if has_omnivoice:
            chain.append(OmniVoiceTTS())
        if has_torch:
            chain.append(SileroTTS())
        return chain

    def synthesize(self, text: str) -> tuple[np.ndarray, int]:
        if self._chain is None:
            self._chain = self._build_chain()
        while self._chain:
            try:
                return self._chain[0].synthesize(text)
            except Exception:
                self._chain.pop(0)  # e.g. first-run download failed
        return self._sapi.synthesize(text)


def create_tts(prefer: str = "auto") -> TTSModel:
    return FallbackTTS(prefer)
