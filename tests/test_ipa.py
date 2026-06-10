from pronunciation_coach.core import ipa


def test_tokenize_keeps_affricates_whole():
    assert ipa.tokenize_ipa("tʃɪn") == ["tʃ", "ɪ", "n"]
    assert ipa.tokenize_ipa("dʒʌmp") == ["dʒ", "ʌ", "m", "p"]


def test_tokenize_keeps_diphthongs_whole():
    assert ipa.tokenize_ipa("taɪm") == ["t", "aɪ", "m"]
    assert ipa.tokenize_ipa("goʊ") == ["g", "oʊ"]
    assert ipa.tokenize_ipa("bɔɪ") == ["b", "ɔɪ"]


def test_tokenize_strips_stress_and_length():
    assert ipa.tokenize_ipa("hɛˈloʊ") == ["h", "ɛ", "l", "oʊ"]
    assert ipa.tokenize_ipa("ˈθɪŋkˌ") == ["θ", "ɪ", "ŋ", "k"]


def test_word_to_ipa_known_words():
    assert "θ" in ipa.word_to_ipa("think")
    assert "ð" in ipa.word_to_ipa("this")


def test_word_to_ipa_handles_punctuation_and_case():
    assert ipa.word_to_ipa("Think!") == ipa.word_to_ipa("think")


def test_word_to_ipa_oov_returns_something():
    result = ipa.word_to_ipa("xyzzyqq")
    assert isinstance(result, str) and len(result) > 0
    assert not result.endswith("*")


def test_text_to_ipa_multiword():
    result = ipa.text_to_ipa("think about")
    assert " " in result
