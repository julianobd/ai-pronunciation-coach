"""Levenshtein edit distance (ported from Legacy/WordMetrics.py, numpy-free)."""

from __future__ import annotations

from typing import Sequence


def edit_distance(seq1: Sequence, seq2: Sequence) -> int:
    """Minimum insertions + deletions + substitutions to turn seq1 into seq2.

    Works on strings (per character) or lists of tokens.
    """
    if len(seq1) < len(seq2):
        return edit_distance(seq2, seq1)
    if not seq2:
        return len(seq1)

    previous = list(range(len(seq2) + 1))
    for i, a in enumerate(seq1, start=1):
        current = [i] + [0] * len(seq2)
        for j, b in enumerate(seq2, start=1):
            current[j] = min(
                current[j - 1] + 1,          # insertion
                previous[j] + 1,             # deletion
                previous[j - 1] + (a != b),  # substitution / match
            )
        previous = current
    return previous[-1]
