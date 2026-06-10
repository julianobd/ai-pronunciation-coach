from pronunciation_coach.core.analysis import PronunciationAnalyzer
from pronunciation_coach.core.shadowing_metrics import (
    compute_shadowing,
    find_pauses,
    speech_rate,
    timing_score,
)


def test_speech_rate():
    stamps = [(0.0, 0.4), (0.5, 0.9), (1.0, 1.5), (1.6, 2.0)]
    assert speech_rate(stamps) == 4 / 2.0


def test_speech_rate_ignores_missing_words():
    stamps = [(0.0, 0.4), (-1.0, -1.0), (1.0, 1.5)]
    assert speech_rate(stamps) == 2 / 1.5


def test_find_pauses():
    stamps = [(0.0, 0.4), (0.5, 0.9), (2.0, 2.4)]  # 1.1s gap
    pauses = find_pauses(stamps)
    assert len(pauses) == 1
    assert pauses[0] == (0.9, 1.1)


def test_timing_identical_is_100():
    stamps = [(0.0, 0.3), (0.5, 0.8), (1.0, 1.4)]
    assert timing_score(stamps, stamps) == 100.0


def test_timing_shifted_start_still_100():
    # Same rhythm, user just started 2s later.
    user = [(2.0, 2.3), (2.5, 2.8), (3.0, 3.4)]
    ref = [(0.0, 0.3), (0.5, 0.8), (1.0, 1.4)]
    assert timing_score(user, ref) == 100.0


def test_timing_degrades_with_deviation():
    user = [(0.0, 0.3), (1.5, 1.8), (3.0, 3.4)]  # much slower rhythm
    ref = [(0.0, 0.3), (0.5, 0.8), (1.0, 1.4)]
    assert timing_score(user, ref) < 50.0


def test_compute_shadowing_composite():
    analyzer = PronunciationAnalyzer(asr=None)
    text = "good morning friend"
    user = analyzer.analyze_transcript(
        text, text, word_stamps=[("good", 0.0, 0.3), ("morning", 0.4, 0.9), ("friend", 1.0, 1.4)]
    )
    ref = analyzer.analyze_transcript(
        text, text, word_stamps=[("good", 0.0, 0.3), ("morning", 0.4, 0.9), ("friend", 1.0, 1.4)]
    )
    result = compute_shadowing(user, ref)
    assert result.pronunciation == 100.0
    assert result.timing == 100.0
    assert result.fluency == 100.0
    assert result.score == 100.0
    assert result.pauses == []
