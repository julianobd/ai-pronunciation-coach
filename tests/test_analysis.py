"""End-to-end (transcript-level) test of the spec's canonical example:
expected "Think about three things." detected as "Tink about tree tings."
"""

from pronunciation_coach.core.analysis import PronunciationAnalyzer


def make_analyzer():
    return PronunciationAnalyzer(asr=None)


def test_think_tink_extracts_th_errors():
    analysis = make_analyzer().analyze_transcript(
        "Think about three things.", "Tink about tree tings."
    )
    th_errors = [
        e for e in analysis.phoneme_errors
        if e["expected"] == "θ" and e["error_type"] == "phoneme_substitution"
    ]
    assert len(th_errors) == 3  # think, three, things
    assert {e["word"] for e in th_errors} == {"think", "three", "things"}
    assert all(e["phoneme_key"] == "th" for e in th_errors)
    assert all(e["detected"] == "t" for e in th_errors)


def test_think_tink_accuracy_below_perfect():
    analysis = make_analyzer().analyze_transcript(
        "Think about three things.", "Tink about tree tings."
    )
    assert 0 < analysis.overall_accuracy < 100
    assert not analysis.low_confidence


def test_perfect_reading_scores_100():
    analysis = make_analyzer().analyze_transcript(
        "Think about three things.", "Think about three things."
    )
    assert analysis.overall_accuracy == 100.0
    assert analysis.phoneme_errors == []


def test_garbage_transcript_flags_low_confidence():
    analysis = make_analyzer().analyze_transcript(
        "Think about three things.", "purple elephant calculator window banana"
    )
    assert analysis.low_confidence or analysis.overall_accuracy < 50


def test_word_results_align_to_expected_words():
    analysis = make_analyzer().analyze_transcript(
        "Think about three things.", "Tink about tree tings."
    )
    assert [r.word for r in analysis.word_results] == ["think", "about", "three", "things"]
    assert analysis.word_results[1].accuracy == 100.0  # "about" was fine
