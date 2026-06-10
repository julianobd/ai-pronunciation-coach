"""Bundled English sentence bank (from Legacy/databases/data_en.csv).

Difficulty is derived from word count at load time, like the legacy app:
easy <= 8 words, medium 9-20, hard 21+.
"""

from __future__ import annotations

import random
from functools import lru_cache
from importlib import resources

from . import ipa
from .text_utils import tokenize_words

EASY, MEDIUM, HARD = "easy", "medium", "hard"


def _difficulty(word_count: int) -> str:
    if word_count <= 8:
        return EASY
    if word_count <= 20:
        return MEDIUM
    return HARD


@lru_cache(maxsize=1)
def _sentences() -> dict[str, list[str]]:
    text = resources.files("pronunciation_coach.data").joinpath("sentences_en.csv").read_text(
        encoding="utf-8"
    )
    buckets: dict[str, list[str]] = {EASY: [], MEDIUM: [], HARD: []}
    for line in text.splitlines()[1:]:  # skip "sentence" header
        sentence = line.strip().strip('"')
        if not sentence:
            continue
        buckets[_difficulty(len(sentence.split()))].append(sentence)
    return buckets


def random_sentence(difficulty: str = EASY) -> str:
    bucket = _sentences().get(difficulty) or _sentences()[EASY]
    return random.choice(bucket)


def sentences_with_phoneme(phoneme_ipa_tokens: tuple[str, ...], difficulty: str = EASY,
                           limit: int = 20) -> list[str]:
    """Find bank sentences containing a target phoneme (for offline exercises)."""
    targets = set(phoneme_ipa_tokens)
    found: list[str] = []
    bucket = _sentences().get(difficulty) or _sentences()[EASY]
    sample = random.sample(bucket, min(len(bucket), 600))
    for sentence in sample:
        for word in tokenize_words(sentence):
            if targets & set(ipa.word_to_phonemes(word)):
                found.append(sentence)
                break
        if len(found) >= limit:
            break
    return found
