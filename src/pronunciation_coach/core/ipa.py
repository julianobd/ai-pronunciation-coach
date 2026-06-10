"""Grapheme-to-phoneme conversion and IPA tokenization.

Primary G2P is eng_to_ipa (CMUdict-based). Words it does not know are
returned with a trailing '*'; for those we fall back to g2p_en (ARPAbet,
mapped to IPA) when installed, else to the bare lowercase word so the
edit-distance comparison still has something letter-like to chew on
(legacy behavior).
"""

from __future__ import annotations

from functools import lru_cache

import eng_to_ipa

from .text_utils import normalize_word

# Multi-character IPA symbols that must be treated as a single phoneme.
# Order matters: longest match first.
IPA_MULTICHAR = [
    "tʃ", "dʒ",                  # affricates
    "aɪ", "eɪ", "ɔɪ", "aʊ", "oʊ",  # diphthongs
    "ɪə", "eə", "ʊə",            # (rare in eng_to_ipa output, kept for safety)
]

# Marks that carry no segmental information for our comparison.
_IGNORED_CHARS = set("ˈˌːˑ̩̃ʼ'  ​")

# ARPAbet (g2p_en output, stress digits stripped) -> IPA
ARPABET_TO_IPA = {
    "AA": "ɑ", "AE": "æ", "AH": "ʌ", "AO": "ɔ", "AW": "aʊ", "AY": "aɪ",
    "B": "b", "CH": "tʃ", "D": "d", "DH": "ð", "EH": "ɛ", "ER": "ɝ",
    "EY": "eɪ", "F": "f", "G": "g", "HH": "h", "IH": "ɪ", "IY": "i",
    "JH": "dʒ", "K": "k", "L": "l", "M": "m", "N": "n", "NG": "ŋ",
    "OW": "oʊ", "OY": "ɔɪ", "P": "p", "R": "r", "S": "s", "SH": "ʃ",
    "T": "t", "TH": "θ", "UH": "ʊ", "UW": "u", "V": "v", "W": "w",
    "Y": "j", "Z": "z", "ZH": "ʒ",
}

_g2p_fallback = None


def _arpabet_word_to_ipa(word: str) -> str | None:
    """OOV fallback via g2p_en, if available."""
    global _g2p_fallback
    if _g2p_fallback is None:
        try:
            from g2p_en import G2p  # heavy import, optional dependency

            _g2p_fallback = G2p()
        except Exception:
            _g2p_fallback = False
    if not _g2p_fallback:
        return None
    phones = _g2p_fallback(word)
    ipa = [ARPABET_TO_IPA.get(p.rstrip("012"), "") for p in phones]
    result = "".join(ipa)
    return result or None


@lru_cache(maxsize=8192)
def word_to_ipa(word: str) -> str:
    """IPA for a single word (stress marks kept; tokenizer strips them)."""
    clean = normalize_word(word)
    if not clean:
        return ""
    ipa = eng_to_ipa.convert(clean)
    if ipa.endswith("*"):  # OOV marker from eng_to_ipa
        fallback = _arpabet_word_to_ipa(clean)
        return fallback if fallback else clean
    return ipa


def text_to_ipa(text: str) -> str:
    return " ".join(word_to_ipa(w) for w in text.split() if normalize_word(w))


def tokenize_ipa(ipa: str) -> list[str]:
    """Split an IPA word string into phoneme tokens.

    Greedy longest-match so affricates and diphthongs stay single tokens;
    stress/length marks and spaces are dropped.
    """
    tokens: list[str] = []
    i = 0
    while i < len(ipa):
        ch = ipa[i]
        if ch in _IGNORED_CHARS:
            i += 1
            continue
        matched = False
        for sym in IPA_MULTICHAR:
            if ipa.startswith(sym, i):
                tokens.append(sym)
                i += len(sym)
                matched = True
                break
        if not matched:
            tokens.append(ch)
            i += 1
    return tokens


def word_to_phonemes(word: str) -> list[str]:
    return tokenize_ipa(word_to_ipa(word))
