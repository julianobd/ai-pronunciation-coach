from pronunciation_coach.core.phoneme_alignment import align_phonemes, analyze_word


def ops_summary(ops):
    return [(o.op, o.expected, o.detected) for o in ops]


def test_perfect_match():
    ops = align_phonemes(["θ", "ɪ", "ŋ", "k"], ["θ", "ɪ", "ŋ", "k"])
    assert all(o.op == "match" for o in ops)


def test_th_substitution_think_tink():
    # think /θɪŋk/ vs tink /tɪŋk/
    ops = align_phonemes(["θ", "ɪ", "ŋ", "k"], ["t", "ɪ", "ŋ", "k"])
    assert ops_summary(ops)[0] == ("substitution", "θ", "t")
    assert [o.op for o in ops[1:]] == ["match", "match", "match"]


def test_omission():
    # "and" /ænd/ said as /æn/
    ops = align_phonemes(["æ", "n", "d"], ["æ", "n"])
    assert ops_summary(ops)[-1] == ("omission", "d", None)


def test_insertion():
    # epenthetic vowel: "school" said as "eschool"
    ops = align_phonemes(["s", "k", "u", "l"], ["ɛ", "s", "k", "u", "l"])
    assert ("insertion", None, "ɛ") in ops_summary(ops)
    assert sum(1 for o in ops if o.op == "match") == 4


def test_empty_detected_is_all_omissions():
    ops = align_phonemes(["θ", "r", "i"], [])
    assert [o.op for o in ops] == ["omission"] * 3


def test_analyze_word_accuracy():
    result = analyze_word("think", ["θ", "ɪ", "ŋ", "k"], ["t", "ɪ", "ŋ", "k"])
    assert result.accuracy == 75.0
    assert result.word == "think"


def test_confusable_substitution_preferred_over_gaps():
    # θ->t is a listed confusion, so alignment should pair them as a
    # substitution rather than omission+insertion.
    ops = align_phonemes(["θ"], ["t"])
    assert ops_summary(ops) == [("substitution", "θ", "t")]
