"""Shadowing flow: sentence -> TTS audio -> user repeats -> similarity metrics."""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass

import numpy as np
from PySide6.QtCore import QObject, Signal

from ..core import sentence_bank
from ..core.analysis import PronunciationAnalyzer, UtteranceAnalysis
from ..core.shadowing_metrics import ShadowingResult, compute_shadowing
from ..persistence.repository import AttemptRepo
from ..speech.tts import TTSModel, resample_to_16k
from .workers import run_in_background


@dataclass
class ShadowingExercise:
    text: str
    audio: np.ndarray          # reference audio for playback
    sample_rate: int
    reference: UtteranceAnalysis  # analyzer run on the TTS audio (word timestamps)


class ShadowingService(QObject):
    exercise_ready = Signal(object)            # ShadowingExercise
    result_ready = Signal(object, object)      # UtteranceAnalysis, ShadowingResult
    failed = Signal(str)

    def __init__(self, analyzer: PronunciationAnalyzer, tts: TTSModel,
                 attempts: AttemptRepo, parent=None) -> None:
        super().__init__(parent)
        self.analyzer = analyzer
        self.tts = tts
        self.attempts = attempts
        self.current: ShadowingExercise | None = None

    def new_exercise(self, difficulty: str = "easy", text: str | None = None) -> None:
        run_in_background(
            self._build_exercise, difficulty, text,
            on_result=self._on_exercise,
            on_error=self.failed.emit,
        )

    def _build_exercise(self, difficulty: str, text: str | None) -> ShadowingExercise:
        sentence = text or sentence_bank.random_sentence(difficulty)
        audio, sample_rate = self.tts.synthesize(sentence)
        # Reference word timestamps come from running our own ASR on the TTS
        # audio - model-agnostic and aligned to the same expected words.
        reference = self.analyzer.analyze(resample_to_16k(audio, sample_rate), sentence)
        return ShadowingExercise(sentence, audio, sample_rate, reference)

    def _on_exercise(self, exercise: ShadowingExercise) -> None:
        self.current = exercise
        self.exercise_ready.emit(exercise)

    def submit_recording(self, audio: np.ndarray) -> None:
        if self.current is None:
            self.failed.emit("No shadowing sentence loaded yet.")
            return
        exercise = self.current
        run_in_background(
            self._score, audio, exercise,
            on_result=lambda pair: self._on_result(*pair),
            on_error=self.failed.emit,
        )

    def _score(self, audio: np.ndarray, exercise: ShadowingExercise):
        analysis = self.analyzer.analyze(audio, exercise.text)
        result = compute_shadowing(analysis, exercise.reference)
        return analysis, result

    def _on_result(self, analysis: UtteranceAnalysis, result: ShadowingResult) -> None:
        if not analysis.too_quiet:
            detail = dataclasses.asdict(analysis)
            detail["shadowing"] = dataclasses.asdict(result)
            self.attempts.add(
                mode="shadowing",
                expected_text=analysis.expected_text,
                transcript=analysis.transcript,
                overall_accuracy=analysis.overall_accuracy,
                duration_s=analysis.duration_s,
                detail=detail,
            )
        self.result_ready.emit(analysis, result)
