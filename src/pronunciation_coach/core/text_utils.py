"""Text normalization helpers shared across the analysis pipeline."""

from string import punctuation

_PUNCT_TABLE = str.maketrans("", "", punctuation + "’‘“”…")


def remove_punctuation(text: str) -> str:
    return text.translate(_PUNCT_TABLE)


def normalize_word(word: str) -> str:
    """Lowercase and strip punctuation; used before G2P and word comparison."""
    return remove_punctuation(word).lower().strip()


def tokenize_words(text: str) -> list[str]:
    """Split text into words, dropping tokens that are pure punctuation."""
    return [w for w in text.split() if normalize_word(w)]
