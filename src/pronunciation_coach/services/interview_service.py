"""Interview simulator: AI interviewer asks, the user answers out loud.

Answers are open-ended (no expected text), so each answer gets a fluency
assessment (speech rate + pauses) rather than a pronunciation accuracy.
"""

from __future__ import annotations

import numpy as np
from PySide6.QtCore import QObject, Signal

from ..core.shadowing_metrics import find_pauses, fluency_score, speech_rate
from ..persistence.repository import AttemptRepo
from ..providers.base import ExerciseProvider
from ..providers.offline import OfflineProvider
from ..speech.asr import ASRModel
from .workers import run_in_background

# Comfortable conversational pace used as the fluency reference.
TARGET_RATE_WPS = 2.3


class InterviewService(QObject):
    interviewer_says = Signal(str, bool)      # text, interview_done
    answer_processed = Signal(str, float)     # transcript, fluency 0-100
    failed = Signal(str)

    def __init__(self, asr: ASRModel, provider: ExerciseProvider,
                 attempts: AttemptRepo, parent=None) -> None:
        super().__init__(parent)
        self.asr = asr
        self.provider = provider
        self.offline = OfflineProvider()
        self.attempts = attempts
        self.history: list[dict] = []
        self.job_role = "general position"
        self.difficulty = "medium"

    def set_provider(self, provider: ExerciseProvider) -> None:
        self.provider = provider

    def start(self, job_role: str, difficulty: str) -> None:
        self.job_role = job_role or "general position"
        self.difficulty = difficulty
        self.history = []
        self._next_question()

    def _next_question(self) -> None:
        run_in_background(
            self._generate_turn,
            on_result=self._on_turn,
            on_error=self.failed.emit,
        )

    def _generate_turn(self) -> dict:
        try:
            return self.provider.generate_interview_turn(
                self.job_role, self.difficulty, self.history
            )
        except Exception:
            return self.offline.generate_interview_turn(
                self.job_role, self.difficulty, self.history
            )

    def _on_turn(self, turn: dict) -> None:
        self.history.append({"role": "interviewer", "text": turn["reply"]})
        self.interviewer_says.emit(turn["reply"], turn.get("done", False))

    def submit_answer(self, audio: np.ndarray) -> None:
        run_in_background(
            self._transcribe_answer, audio,
            on_result=self._on_answer,
            on_error=self.failed.emit,
        )

    def _transcribe_answer(self, audio: np.ndarray):
        result = self.asr.transcribe(np.asarray(audio, dtype=np.float32).flatten())
        stamps = [(w.start_s, w.end_s) for w in result.words]
        rate = speech_rate(stamps)
        pauses = find_pauses(stamps)
        fluency = fluency_score(pauses, rate, TARGET_RATE_WPS)
        duration_s = len(audio) / 16000.0
        return result.text, fluency, duration_s

    def _on_answer(self, payload) -> None:
        transcript, fluency, duration_s = payload
        self.history.append({"role": "candidate", "text": transcript})
        self.attempts.add(
            mode="interview",
            expected_text="",
            transcript=transcript,
            overall_accuracy=None,
            duration_s=duration_s,
            detail={"fluency": fluency, "job_role": self.job_role},
        )
        self.answer_processed.emit(transcript, fluency)
        self._next_question()
