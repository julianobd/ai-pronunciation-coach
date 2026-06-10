"""Shadowing similarity metrics: pronunciation, timing, speech rate, pauses.

Both the user's recording and the reference (TTS) audio are analyzed with
the same analyzer against the same expected text, so word timestamps on
both sides are aligned to the same expected-word indices.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from .analysis import UtteranceAnalysis

PAUSE_GAP_S = 0.35        # gap between words reported as a pause
LONG_PAUSE_S = 0.5        # pauses longer than this hurt fluency
TIMING_DECAY = 1.8        # how hard onset deviation hits the timing score


@dataclass
class ShadowingResult:
    score: float
    pronunciation: float
    timing: float
    fluency: float
    speech_rate_wps: float = 0.0
    reference_rate_wps: float = 0.0
    pauses: list[tuple[float, float]] = field(default_factory=list)  # (start_s, duration_s)


def _valid_stamps(stamps: list[tuple[float, float]]) -> list[tuple[float, float]]:
    return [(s, e) for (s, e) in stamps if s >= 0 and e > s]


def speech_rate(stamps: list[tuple[float, float]]) -> float:
    valid = _valid_stamps(stamps)
    if len(valid) < 2:
        return 0.0
    span = valid[-1][1] - valid[0][0]
    return len(valid) / span if span > 0 else 0.0


def find_pauses(stamps: list[tuple[float, float]]) -> list[tuple[float, float]]:
    valid = _valid_stamps(stamps)
    pauses = []
    for (_, prev_end), (next_start, _) in zip(valid, valid[1:]):
        gap = next_start - prev_end
        if gap > PAUSE_GAP_S:
            pauses.append((round(prev_end, 2), round(gap, 2)))
    return pauses


def timing_score(user: list[tuple[float, float]], ref: list[tuple[float, float]]) -> float:
    """Compare relative word onsets between user and reference."""
    pairs = [
        (u, r)
        for u, r in zip(user, ref)
        if u[0] >= 0 and r[0] >= 0
    ]
    if len(pairs) < 2:
        return 0.0
    user_zero = pairs[0][0][0]
    ref_zero = pairs[0][1][0]
    deviations = [
        abs((u[0] - user_zero) - (r[0] - ref_zero)) for u, r in pairs[1:]
    ]
    mean_dev = sum(deviations) / len(deviations)
    return round(100.0 * math.exp(-TIMING_DECAY * mean_dev), 1)


def fluency_score(
    pauses: list[tuple[float, float]],
    rate_wps: float,
    reference_rate_wps: float,
) -> float:
    pause_penalty = sum(
        min(20.0, 10.0 * duration) for _, duration in pauses if duration >= LONG_PAUSE_S
    )
    rate_penalty = 0.0
    if reference_rate_wps > 0 and rate_wps > 0:
        rate_penalty = min(30.0, 60.0 * abs(rate_wps - reference_rate_wps) / reference_rate_wps)
    elif rate_wps == 0:
        rate_penalty = 30.0
    return round(max(0.0, 100.0 - pause_penalty - rate_penalty), 1)


def compute_shadowing(user: UtteranceAnalysis, reference: UtteranceAnalysis) -> ShadowingResult:
    pronunciation = user.overall_accuracy
    timing = timing_score(user.word_timestamps, reference.word_timestamps)
    user_rate = speech_rate(user.word_timestamps)
    ref_rate = speech_rate(reference.word_timestamps)
    pauses = find_pauses(user.word_timestamps)
    fluency = fluency_score(pauses, user_rate, ref_rate)
    score = round(0.5 * pronunciation + 0.25 * timing + 0.25 * fluency, 1)
    return ShadowingResult(
        score=score,
        pronunciation=round(pronunciation, 1),
        timing=timing,
        fluency=fluency,
        speech_rate_wps=round(user_rate, 2),
        reference_rate_wps=round(ref_rate, 2),
        pauses=pauses,
    )
