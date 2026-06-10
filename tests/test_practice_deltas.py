from pronunciation_coach.core.analysis import PronunciationAnalyzer
from pronunciation_coach.services.practice_service import compute_phoneme_deltas


def analyze(expected, transcript):
    return PronunciationAnalyzer(asr=None).analyze_transcript(expected, transcript)


def test_th_errors_counted():
    analysis = analyze("Think about three things.", "Tink about tree tings.")
    deltas = compute_phoneme_deltas(analysis)
    attempts, errors = deltas["th"]
    assert attempts == 3.0   # think, three, things
    assert errors == 3.0     # all substituted with t


def test_perfect_reading_has_no_errors():
    analysis = analyze("Think about three things.", "Think about three things.")
    deltas = compute_phoneme_deltas(analysis)
    assert all(errors == 0 for _attempts, errors in deltas.values())
    assert deltas["th"][0] == 3.0


def test_missing_word_excluded_from_stats():
    analysis = analyze("think big", "big")
    deltas = compute_phoneme_deltas(analysis)
    # "think" was dropped entirely by ASR -> its phonemes don't count
    assert "th" not in deltas
