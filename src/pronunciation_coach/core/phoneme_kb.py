"""Static phoneme knowledge base: articulation tips, confusions, minimal pairs.

Loaded once from data/phoneme_kb.json. Maps raw IPA tokens to "teachable
keys" (θ -> "th") so stats and exercises speak the learner's language.

Entries with detectable=False are practice-only targets (flap t, glottal
stop, r-colored vowels...): the ASR/G2P pipeline never emits their IPA, so
they are excluded from the ipa->key mapping and never appear in stats.
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
    spellings: tuple[str, ...] = ()
    examples_initial: tuple[str, ...] = ()
    examples_medial: tuple[str, ...] = ()
    examples_final: tuple[str, ...] = ()
    minimal_pairs: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    practice_sentences: tuple[str, ...] = ()
    tongue_twisters: tuple[str, ...] = ()
    detectable: bool = True

    @property
    def example_words(self) -> tuple[str, ...]:
        """Flat view for legacy consumers: round-robin over positions."""
        positions = [self.examples_initial, self.examples_medial, self.examples_final]
        words: list[str] = []
        seen: set[str] = set()
        longest = max((len(p) for p in positions), default=0)
        for i in range(longest):
            for pos in positions:
                if i < len(pos) and pos[i] not in seen:
                    seen.add(pos[i])
                    words.append(pos[i])
        return tuple(words)


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
        examples = entry.get("examples", {})
        info = PhonemeInfo(
            key=entry["key"],
            ipa=tuple(entry["ipa"]),
            display=entry["display"],
            articulation_tip=entry["articulation_tip"],
            common_confusions=tuple(entry.get("common_confusions", [])),
            spellings=tuple(entry.get("spellings", [])),
            examples_initial=tuple(examples.get("initial", [])),
            examples_medial=tuple(examples.get("medial", [])),
            examples_final=tuple(examples.get("final", [])),
            minimal_pairs=tuple(tuple(p) for p in entry.get("minimal_pairs", [])),
            practice_sentences=tuple(entry.get("practice_sentences", [])),
            tongue_twisters=tuple(entry.get("tongue_twisters", [])),
            detectable=entry.get("detectable", True),
        )
        infos[info.key] = info
        if info.detectable:
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
