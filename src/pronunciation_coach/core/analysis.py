"""PronunciationAnalyzer: the full audio -> phoneme errors pipeline.

Port of Legacy/pronunciationTrainer.py (English-only), extended with
phoneme-level error extraction via core.phoneme_alignment.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from . import ipa, phoneme_kb, scoring
from .phoneme_alignment import WordPhonemeResult, analyze_word
from .text_utils import normalize_word, tokenize_words
from .word_alignment import WORD_NOT_FOUND_TOKEN, align_word_sequences

SAMPLE_RATE = 16000
MIN_DURATION_S = 0.5
MIN_RMS = 0.003  # below this the recording is effectively silence


@dataclass
class UtteranceAnalysis:
    expected_text: str
    transcript: str
    word_results: list[WordPhonemeResult] = field(default_factory=list)
    word_timestamps: list[tuple[float, float]] = field(default_factory=list)
    overall_accuracy: float = 0.0
    phoneme_errors: list[dict] = field(default_factory=list)
    duration_s: float = 0.0
    too_quiet: bool = False        # recording was too short/silent to analyze
    low_confidence: bool = False   # transcript barely matches expected text

    @property
    def word_categories(self) -> list[int]:
        return [scoring.category_for_accuracy(r.accuracy) for r in self.word_results]


def _error_type(op_kind: str) -> str:
    return {
        "substitution": "phoneme_substitution",
        "omission": "phoneme_omission",
        "insertion": "phoneme_insertion",
    }[op_kind]


def extract_phoneme_errors(word_results: list[WordPhonemeResult]) -> list[dict]:
    """Flatten per-word ops into the persistable error list."""
    errors: list[dict] = []
    for result in word_results:
        for op in result.ops:
            if op.op == "match":
                continue
            token = op.expected if op.expected else op.detected
            key = phoneme_kb.key_for_ipa(token) if token else None
            errors.append(
                {
                    "word": result.word,
                    "expected": op.expected,
                    "detected": op.detected,
                    "error_type": _error_type(op.op),
                    "phoneme_key": key,
                    "word_missing": result.word_missing,
                }
            )
    return errors


def preprocess_audio(audio: np.ndarray) -> np.ndarray:
    audio = np.asarray(audio, dtype=np.float32).flatten()
    audio = audio - np.mean(audio)
    peak = np.max(np.abs(audio)) if audio.size else 0.0
    if peak > 0:
        audio = audio / peak
    return audio


class PronunciationAnalyzer:
    def __init__(self, asr) -> None:
        self.asr = asr  # speech.asr.ASRModel

    def analyze(self, audio: np.ndarray, expected_text: str) -> UtteranceAnalysis:
        raw = np.asarray(audio, dtype=np.float32).flatten()
        duration_s = raw.size / SAMPLE_RATE
        rms = float(np.sqrt(np.mean(raw**2))) if raw.size else 0.0
        if duration_s < MIN_DURATION_S or rms < MIN_RMS:
            return UtteranceAnalysis(
                expected_text=expected_text, transcript="",
                duration_s=duration_s, too_quiet=True,
            )

        asr_result = self.asr.transcribe(preprocess_audio(raw))
        return self.analyze_transcript(
            expected_text,
            asr_result.text,
            [(w.word, w.start_s, w.end_s) for w in asr_result.words],
            duration_s=duration_s,
        )

    def analyze_transcript(
        self,
        expected_text: str,
        transcript: str,
        word_stamps: list[tuple[str, float, float]] | None = None,
        duration_s: float = 0.0,
    ) -> UtteranceAnalysis:
        """Text-only entry point (also used by tests and shadowing)."""
        words_real = tokenize_words(expected_text)

        # Prefer ASR word stamps as the estimated-word source so indices
        # line up with timestamps; fall back to splitting the transcript.
        if word_stamps:
            words_estimated = [w for (w, _s, _e) in word_stamps if normalize_word(w)]
            stamps = [(s, e) for (w, s, e) in word_stamps if normalize_word(w)]
        else:
            words_estimated = tokenize_words(transcript)
            stamps = []

        mapped_words, mapped_indices = align_word_sequences(words_estimated, words_real)

        word_results: list[WordPhonemeResult] = []
        word_timestamps: list[tuple[float, float]] = []
        for real_word, mapped_word, est_idx in zip(words_real, mapped_words, mapped_indices):
            clean_real = normalize_word(real_word)
            expected_ipa = ipa.word_to_ipa(clean_real)
            missing = mapped_word == WORD_NOT_FOUND_TOKEN
            detected_ipa = "" if missing else ipa.word_to_ipa(normalize_word(mapped_word))
            word_results.append(
                analyze_word(
                    word=clean_real,
                    expected_tokens=ipa.tokenize_ipa(expected_ipa),
                    detected_tokens=ipa.tokenize_ipa(detected_ipa),
                    expected_ipa=expected_ipa,
                    detected_ipa=detected_ipa,
                    word_missing=missing,
                )
            )
            if stamps and est_idx >= 0:
                word_timestamps.append(stamps[est_idx])
            else:
                word_timestamps.append((-1.0, -1.0))

        accuracy = scoring.overall_accuracy(word_results)
        matched = sum(1 for idx in mapped_indices if idx >= 0)
        low_confidence = bool(words_real) and (
            matched / len(words_real) < 0.25 and len(words_estimated) > 0
        )

        return UtteranceAnalysis(
            expected_text=expected_text,
            transcript=transcript,
            word_results=word_results,
            word_timestamps=word_timestamps,
            overall_accuracy=accuracy,
            phoneme_errors=extract_phoneme_errors(word_results),
            duration_s=duration_s,
            low_confidence=low_confidence,
        )
