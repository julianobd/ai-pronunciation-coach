"""Align ASR-estimated words against the expected (real) words.

Replaces Legacy/WordMatching.py's dtwalign dependency with an in-house
Needleman-Wunsch global alignment over an edit-distance cost matrix.
For each expected word we return the best-matching estimated word (or the
WORD_NOT_FOUND_TOKEN when ASR produced nothing for it) plus the index of
that estimated word so callers can look up word timestamps.
"""

from __future__ import annotations

from .word_metrics import edit_distance

WORD_NOT_FOUND_TOKEN = "-"


def align_word_sequences(
    words_estimated: list[str], words_real: list[str]
) -> tuple[list[str], list[int]]:
    """Globally align estimated words to real words.

    Returns (mapped_words, mapped_indices), both of len(words_real):
      mapped_words[i]   -> estimated word matched to real word i, or '-'
      mapped_indices[i] -> index into words_estimated, or -1
    """
    n, m = len(words_estimated), len(words_real)
    if m == 0:
        return [], []
    if n == 0:
        return [WORD_NOT_FOUND_TOKEN] * m, [-1] * m

    # Gap penalties: skipping a real word costs its length (all phonemes
    # missed); skipping an estimated word costs its length (spurious word).
    INF = float("inf")
    dp = [[INF] * (m + 1) for _ in range(n + 1)]
    dp[0][0] = 0.0
    for i in range(1, n + 1):
        dp[i][0] = dp[i - 1][0] + len(words_estimated[i - 1])
    for j in range(1, m + 1):
        dp[0][j] = dp[0][j - 1] + len(words_real[j - 1])

    for i in range(1, n + 1):
        est = words_estimated[i - 1]
        for j in range(1, m + 1):
            real = words_real[j - 1]
            dp[i][j] = min(
                dp[i - 1][j - 1] + edit_distance(est.lower(), real.lower()),
                dp[i - 1][j] + len(est),
                dp[i][j - 1] + len(real),
            )

    mapped_words = [WORD_NOT_FOUND_TOKEN] * m
    mapped_indices = [-1] * m
    i, j = n, m
    while i > 0 and j > 0:
        est, real = words_estimated[i - 1], words_real[j - 1]
        sub_cost = dp[i - 1][j - 1] + edit_distance(est.lower(), real.lower())
        if dp[i][j] == sub_cost:
            mapped_words[j - 1] = est
            mapped_indices[j - 1] = i - 1
            i, j = i - 1, j - 1
        elif dp[i][j] == dp[i - 1][j] + len(est):
            i -= 1
        else:
            j -= 1

    return mapped_words, mapped_indices
