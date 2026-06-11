"""Guardrail tests for the phoneme and cluster knowledge bases.

These keep the curated JSON content honest: minimum counts per entry,
IPA-mapping integrity, and (where G2P allows) that example words really
contain the phoneme they claim to teach.
"""

from pronunciation_coach.core import cluster_kb, ipa, phoneme_kb

DETECTABLE_KEYS = {
    "th", "th_voiced", "sh", "zh", "ch", "j", "r", "l", "v", "w", "y", "h",
    "ng", "s", "z", "f", "p", "b", "t", "d", "k", "g", "m", "n",
    "ih", "ee", "ae", "eh", "uh", "schwa", "ah", "aw", "oo_short", "oo",
    "oh", "ay", "eye", "ow", "oy", "er",
}
PRACTICE_ONLY_KEYS = {"flap_t", "glottal_t", "hw", "ar", "or", "air", "ear", "oor"}

# Entries where solid minimal pairs are scarce in English.
MIN_PAIRS_EXCEPTIONS = {"schwa": 0, "zh": 6, "glottal_t": 0, "oor": 5}

CLUSTER_KEYS = {
    "st", "sp", "sk", "str", "spr", "spl", "scr", "shr", "thr", "dr", "tr",
    "gr", "kr", "pl", "bl", "fl", "cl", "gl", "sl", "sm", "sn", "sw",
}


def test_inventory_complete():
    phonemes = phoneme_kb.all_phonemes()
    assert set(phonemes) == DETECTABLE_KEYS | PRACTICE_ONLY_KEYS
    for key in DETECTABLE_KEYS:
        assert phonemes[key].detectable, key
    for key in PRACTICE_ONLY_KEYS:
        assert not phonemes[key].detectable, key


def test_entry_minimum_content():
    for key, info in phoneme_kb.all_phonemes().items():
        assert info.spellings, f"{key}: no spellings"
        total_examples = (
            len(info.examples_initial)
            + len(info.examples_medial)
            + len(info.examples_final)
        )
        assert total_examples >= 10, f"{key}: only {total_examples} examples"
        min_pairs = MIN_PAIRS_EXCEPTIONS.get(key, 10 if info.detectable else 8)
        assert len(info.minimal_pairs) >= min_pairs, (
            f"{key}: only {len(info.minimal_pairs)} minimal pairs"
        )
        assert len(info.practice_sentences) >= 5, f"{key}: too few sentences"
        assert len(info.tongue_twisters) >= 2, f"{key}: too few tongue twisters"
        assert info.articulation_tip


def test_minimal_pair_words_differ():
    for key, info in phoneme_kb.all_phonemes().items():
        for a, b in info.minimal_pairs:
            assert a and b and a.lower() != b.lower(), f"{key}: bad pair {a}/{b}"


def test_ipa_mapping_integrity():
    # Every detectable symbol resolves back to its own entry (no
    # first-match-wins collisions); practice-only IPA is unmapped.
    for key, info in phoneme_kb.all_phonemes().items():
        for symbol in info.ipa:
            if info.detectable:
                assert phoneme_kb.key_for_ipa(symbol) == key, (
                    f"{symbol} claimed by {phoneme_kb.key_for_ipa(symbol)}, "
                    f"expected {key}"
                )
            else:
                assert phoneme_kb.key_for_ipa(symbol) is None, symbol


def test_affricate_ligatures_mapped():
    # eng_to_ipa emits single-codepoint ligatures; both forms must resolve.
    assert phoneme_kb.key_for_ipa("ʧ") == "ch"
    assert phoneme_kb.key_for_ipa("ʤ") == "j"
    assert phoneme_kb.key_for_ipa("tʃ") == "ch"
    assert phoneme_kb.key_for_ipa("dʒ") == "j"


def test_example_words_property():
    for key, info in phoneme_kb.all_phonemes().items():
        words = info.example_words
        assert words, f"{key}: empty example_words"
        assert len(words) == len(set(words)), f"{key}: duplicates in example_words"
        for pos in (info.examples_initial, info.examples_medial, info.examples_final):
            if pos:
                assert any(w in words for w in pos)


def test_example_words_contain_phoneme():
    # >=80% of a detectable phoneme's example words must contain one of its
    # IPA tokens per the G2P pipeline (threshold absorbs CMUdict quirks).
    # Substring fallback covers symbols split by the tokenizer (e.g. ər).
    for key, info in phoneme_kb.all_phonemes().items():
        if not info.detectable:
            continue
        words = info.example_words
        hits = 0
        for word in words:
            ipa_str = ipa.word_to_ipa(word)
            tokens = ipa.tokenize_ipa(ipa_str)
            if any(sym in tokens for sym in info.ipa) or any(
                sym in ipa_str for sym in info.ipa
            ):
                hits += 1
        ratio = hits / len(words)
        assert ratio >= 0.8, f"{key}: only {ratio:.0%} of examples contain {info.ipa}"


def test_clusters_inventory_and_content():
    clusters = cluster_kb.all_clusters()
    assert set(clusters) == CLUSTER_KEYS
    for key, cluster in clusters.items():
        assert cluster.articulation_tip, key
        assert cluster.common_errors, key
        assert len(cluster.example_words) >= 6, key
        assert len(cluster.practice_sentences) >= 2, key
        for phoneme_key in cluster.phoneme_keys:
            assert phoneme_kb.get_info(phoneme_key), (
                f"{key}: unknown phoneme {phoneme_key}"
            )
        for word in cluster.example_words:
            assert word.lower().startswith(tuple(cluster.spellings)), (
                f"{key}: {word} does not start with {cluster.spellings}"
            )


def test_clusters_for_phonemes():
    keys = [c.key for c in cluster_kb.clusters_for_phonemes(["th"])]
    assert "thr" in keys
    assert cluster_kb.clusters_for_phonemes(["schwa"]) == []
