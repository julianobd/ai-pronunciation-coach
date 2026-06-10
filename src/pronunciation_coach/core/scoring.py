"""Utterance scoring (port of Legacy/pronunciationTrainer.py:157-191).

Accuracy is phoneme-weighted: each expected phoneme contributes equally to
the overall score, so long words matter more than short ones.
"""

from __future__ import annotations

from .phoneme_alignment import WordPhonemeResult

# Word display categories: >=80 good (green), >=60 fair (orange), else poor (red)
CATEGORY_GOOD, CATEGORY_FAIR, CATEGORY_POOR = 0, 1, 2


def category_for_accuracy(accuracy: float) -> int:
    if accuracy >= 80:
        return CATEGORY_GOOD
    if accuracy >= 60:
        return CATEGORY_FAIR
    return CATEGORY_POOR


def overall_accuracy(word_results: list[WordPhonemeResult]) -> float:
    """Phoneme-weighted accuracy across the utterance, 0-100."""
    total_phonemes = 0
    total_matches = 0
    for result in word_results:
        expected_count = sum(1 for op in result.ops if op.op != "insertion")
        matches = sum(1 for op in result.ops if op.op == "match")
        total_phonemes += expected_count
        total_matches += matches
    if total_phonemes == 0:
        return 0.0
    return round(100.0 * total_matches / total_phonemes, 1)
