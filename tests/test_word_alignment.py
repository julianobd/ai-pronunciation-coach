from pronunciation_coach.core.word_alignment import (
    WORD_NOT_FOUND_TOKEN,
    align_word_sequences,
)


def test_perfect_alignment():
    real = ["think", "about", "three", "things"]
    mapped, indices = align_word_sequences(real, real)
    assert mapped == real
    assert indices == [0, 1, 2, 3]


def test_misheard_words_still_align_positionally():
    estimated = ["tink", "about", "tree", "tings"]
    real = ["think", "about", "three", "things"]
    mapped, indices = align_word_sequences(estimated, real)
    assert mapped == estimated
    assert indices == [0, 1, 2, 3]


def test_missing_word():
    estimated = ["think", "three", "things"]
    real = ["think", "about", "three", "things"]
    mapped, _ = align_word_sequences(estimated, real)
    assert mapped[0] == "think"
    assert WORD_NOT_FOUND_TOKEN in mapped
    assert mapped[2] == "three" and mapped[3] == "things"


def test_extra_word_skipped():
    estimated = ["think", "um", "about", "three", "things"]
    real = ["think", "about", "three", "things"]
    mapped, _ = align_word_sequences(estimated, real)
    assert mapped == ["think", "about", "three", "things"]


def test_empty_estimated():
    mapped, indices = align_word_sequences([], ["hello", "world"])
    assert mapped == [WORD_NOT_FOUND_TOKEN] * 2
    assert indices == [-1, -1]
