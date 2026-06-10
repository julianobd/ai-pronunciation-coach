from pronunciation_coach.core import scoring
from pronunciation_coach.core.phoneme_alignment import analyze_word


def test_categories():
    assert scoring.category_for_accuracy(95) == scoring.CATEGORY_GOOD
    assert scoring.category_for_accuracy(80) == scoring.CATEGORY_GOOD
    assert scoring.category_for_accuracy(70) == scoring.CATEGORY_FAIR
    assert scoring.category_for_accuracy(30) == scoring.CATEGORY_POOR


def test_overall_accuracy_weighted_by_phonemes():
    perfect = analyze_word("see", ["s", "i"], ["s", "i"])
    half = analyze_word("think", ["θ", "ɪ", "ŋ", "k"], ["t", "ɪ", "ŋ", "k"])
    # 2 + 3 matches out of 2 + 4 expected phonemes
    assert scoring.overall_accuracy([perfect, half]) == round(100 * 5 / 6, 1)


def test_overall_accuracy_empty():
    assert scoring.overall_accuracy([]) == 0.0
