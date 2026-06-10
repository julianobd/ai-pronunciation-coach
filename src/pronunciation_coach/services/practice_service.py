"""Record -> analyze -> persist -> notify pipeline."""

from __future__ import annotations

import dataclasses

import numpy as np
from PySide6.QtCore import QObject, Signal

from ..core import phoneme_kb
from ..core.analysis import PronunciationAnalyzer, UtteranceAnalysis
from ..persistence.repository import AttemptRepo, PhonemeStatsRepo
from .workers import run_in_background

# Spurious extra phonemes are weighted less than substitutions/omissions:
# ASR word splits often produce false insertions.
INSERTION_WEIGHT = 0.5


def compute_phoneme_deltas(analysis: UtteranceAnalysis) -> dict[str, tuple[float, float]]:
    """Per teachable key: (attempts_delta, errors_delta) for this utterance."""
    deltas: dict[str, list[float]] = {}
    for result in analysis.word_results:
        if result.word_missing:
            continue  # likely ASR dropout, not pronunciation
        for op in result.ops:
            if op.op == "insertion":
                key = phoneme_kb.key_for_ipa(op.detected) if op.detected else None
                if key:
                    deltas.setdefault(key, [0.0, 0.0])
                    deltas[key][0] += INSERTION_WEIGHT
                    deltas[key][1] += INSERTION_WEIGHT
                continue
            key = phoneme_kb.key_for_ipa(op.expected) if op.expected else None
            if not key:
                continue
            deltas.setdefault(key, [0.0, 0.0])
            deltas[key][0] += 1.0
            if op.op in ("substitution", "omission"):
                deltas[key][1] += 1.0
    return {k: (v[0], v[1]) for k, v in deltas.items()}


class PracticeService(QObject):
    analysis_ready = Signal(object)   # UtteranceAnalysis
    analysis_failed = Signal(str)

    def __init__(self, analyzer: PronunciationAnalyzer, attempts: AttemptRepo,
                 stats: PhonemeStatsRepo, parent=None) -> None:
        super().__init__(parent)
        self.analyzer = analyzer
        self.attempts = attempts
        self.stats = stats

    def submit_recording(self, audio: np.ndarray, expected_text: str,
                         mode: str = "practice") -> None:
        run_in_background(
            self.analyzer.analyze, audio, expected_text,
            on_result=lambda analysis: self._on_analysis(analysis, mode),
            on_error=self.analysis_failed.emit,
        )

    def _on_analysis(self, analysis: UtteranceAnalysis, mode: str) -> None:
        if not analysis.too_quiet and not analysis.low_confidence:
            self.persist(analysis, mode)
        self.analysis_ready.emit(analysis)

    def persist(self, analysis: UtteranceAnalysis, mode: str) -> None:
        self.attempts.add(
            mode=mode,
            expected_text=analysis.expected_text,
            transcript=analysis.transcript,
            overall_accuracy=analysis.overall_accuracy,
            duration_s=analysis.duration_s,
            detail=dataclasses.asdict(analysis),
        )
        for key, (attempt_count, error_count) in compute_phoneme_deltas(analysis).items():
            self.stats.record(key, attempt_count, error_count)
