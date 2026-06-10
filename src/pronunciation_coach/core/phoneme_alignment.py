"""Phoneme-level alignment between expected and detected IPA token sequences.

Needleman-Wunsch / Levenshtein DP with backtrace producing explicit
match / substitution / omission / insertion operations per phoneme.
This is what turns "think -> tink" into
{"word": "think", "expected": "θ", "detected": "t",
 "error_type": "phoneme_substitution"}.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional

from . import phoneme_kb

OpType = Literal["match", "substitution", "omission", "insertion"]

# Substitution between confusable phonemes (same KB key or listed confusion)
# is cheaper so the alignment pairs them up instead of emitting gap pairs.
_CONFUSABLE_SUB_COST = 0.6
_SUB_COST = 1.0
_GAP_COST = 1.0


@dataclass
class PhonemeOp:
    op: OpType
    expected: Optional[str]  # IPA token, None for insertion
    detected: Optional[str]  # IPA token, None for omission
    index: int               # position in the expected sequence


@dataclass
class WordPhonemeResult:
    word: str
    expected_ipa: str
    detected_ipa: str
    ops: list[PhonemeOp] = field(default_factory=list)
    accuracy: float = 0.0          # 0-100, matches / expected length
    word_missing: bool = False     # ASR produced no word at all


def _sub_cost(a: str, b: str) -> float:
    if a == b:
        return 0.0
    key_a, key_b = phoneme_kb.key_for_ipa(a), phoneme_kb.key_for_ipa(b)
    if key_a and key_a == key_b:
        return _CONFUSABLE_SUB_COST
    if key_a and key_b and phoneme_kb.are_confusable(key_a, key_b):
        return _CONFUSABLE_SUB_COST
    return _SUB_COST


def align_phonemes(expected: list[str], detected: list[str]) -> list[PhonemeOp]:
    n, m = len(expected), len(detected)
    dp = [[0.0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        dp[i][0] = i * _GAP_COST
    for j in range(1, m + 1):
        dp[0][j] = j * _GAP_COST
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            dp[i][j] = min(
                dp[i - 1][j - 1] + _sub_cost(expected[i - 1], detected[j - 1]),
                dp[i - 1][j] + _GAP_COST,
                dp[i][j - 1] + _GAP_COST,
            )

    ops: list[PhonemeOp] = []
    i, j = n, m
    while i > 0 or j > 0:
        if i > 0 and j > 0 and dp[i][j] == dp[i - 1][j - 1] + _sub_cost(
            expected[i - 1], detected[j - 1]
        ):
            kind: OpType = "match" if expected[i - 1] == detected[j - 1] else "substitution"
            ops.append(PhonemeOp(kind, expected[i - 1], detected[j - 1], i - 1))
            i, j = i - 1, j - 1
        elif i > 0 and dp[i][j] == dp[i - 1][j] + _GAP_COST:
            ops.append(PhonemeOp("omission", expected[i - 1], None, i - 1))
            i -= 1
        else:
            ops.append(PhonemeOp("insertion", None, detected[j - 1], max(i - 1, 0)))
            j -= 1
    ops.reverse()
    return ops


def analyze_word(
    word: str,
    expected_tokens: list[str],
    detected_tokens: list[str],
    expected_ipa: str = "",
    detected_ipa: str = "",
    word_missing: bool = False,
) -> WordPhonemeResult:
    ops = align_phonemes(expected_tokens, detected_tokens)
    matches = sum(1 for op in ops if op.op == "match")
    accuracy = 100.0 * matches / len(expected_tokens) if expected_tokens else 100.0
    return WordPhonemeResult(
        word=word,
        expected_ipa=expected_ipa or "".join(expected_tokens),
        detected_ipa=detected_ipa or "".join(detected_tokens),
        ops=ops,
        accuracy=accuracy,
        word_missing=word_missing,
    )
