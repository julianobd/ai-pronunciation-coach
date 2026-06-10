"""Static phoneme knowledge base: articulation tips, confusions, minimal pairs.

Loaded once from data/phoneme_kb.json. Maps raw IPA tokens to "teachable
keys" (θ -> "th") so stats and exercises speak the learner's language.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from functools import lru_cache
from importlib import resources


@dataclass(frozen=True)
class PhonemeInfo:
    key: str
    ipa: tuple[str, ...]
    display: str
    articulation_tip: str
    common_confusions: tuple[str, ...] = ()
    example_words: tuple[str, ...] = ()
    minimal_pairs: tuple[tuple[str, str], ...] = field(default_factory=tuple)


@lru_cache(maxsize=1)
def _load() -> tuple[dict[str, PhonemeInfo], dict[str, str]]:
    raw = json.loads(
        resources.files("pronunciation_coach.data").joinpath("phoneme_kb.json").read_text(
            encoding="utf-8"
        )
    )
    infos: dict[str, PhonemeInfo] = {}
    ipa_to_key: dict[str, str] = {}
    for entry in raw["phonemes"]:
        info = PhonemeInfo(
            key=entry["key"],
            ipa=tuple(entry["ipa"]),
            display=entry["display"],
            articulation_tip=entry["articulation_tip"],
            common_confusions=tuple(entry.get("common_confusions", [])),
            example_words=tuple(entry.get("example_words", [])),
            minimal_pairs=tuple(tuple(p) for p in entry.get("minimal_pairs", [])),
        )
        infos[info.key] = info
        for symbol in info.ipa:
            ipa_to_key.setdefault(symbol, info.key)
    return infos, ipa_to_key


def all_phonemes() -> dict[str, PhonemeInfo]:
    return dict(_load()[0])


def get_info(key: str) -> PhonemeInfo | None:
    return _load()[0].get(key)


def key_for_ipa(ipa_token: str) -> str | None:
    return _load()[1].get(ipa_token)


def display_for_key(key: str) -> str:
    info = get_info(key)
    return info.display if info else key


def are_confusable(key_a: str, key_b: str) -> bool:
    if key_a == key_b:
        return True
    infos = _load()[0]
    a, b = infos.get(key_a), infos.get(key_b)
    return bool(
        (a and key_b in a.common_confusions) or (b and key_a in b.common_confusions)
    )
