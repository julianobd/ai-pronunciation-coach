"""Static consonant-cluster knowledge base: drills for onset clusters.

Loaded once from data/clusters_kb.json. Clusters are not phonemes — they
never enter phoneme stats directly. Cluster exercises target the component
phoneme keys, so per-phoneme accuracy accrues through the normal pipeline.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from importlib import resources


@dataclass(frozen=True)
class ClusterInfo:
    key: str
    display: str
    phoneme_keys: tuple[str, ...]
    articulation_tip: str
    spellings: tuple[str, ...] = ()
    common_errors: tuple[str, ...] = ()
    example_words: tuple[str, ...] = ()
    practice_sentences: tuple[str, ...] = ()


@lru_cache(maxsize=1)
def _load() -> dict[str, ClusterInfo]:
    raw = json.loads(
        resources.files("pronunciation_coach.data").joinpath("clusters_kb.json").read_text(
            encoding="utf-8"
        )
    )
    infos: dict[str, ClusterInfo] = {}
    for entry in raw["clusters"]:
        info = ClusterInfo(
            key=entry["key"],
            display=entry["display"],
            phoneme_keys=tuple(entry["phoneme_keys"]),
            articulation_tip=entry["articulation_tip"],
            spellings=tuple(entry.get("spellings", [entry["key"]])),
            common_errors=tuple(entry.get("common_errors", [])),
            example_words=tuple(entry.get("example_words", [])),
            practice_sentences=tuple(entry.get("practice_sentences", [])),
        )
        infos[info.key] = info
    return infos


def all_clusters() -> dict[str, ClusterInfo]:
    return dict(_load())


def get_cluster(key: str) -> ClusterInfo | None:
    return _load().get(key)


def clusters_for_phonemes(keys: list[str]) -> list[ClusterInfo]:
    """Clusters that contain any of the given phoneme keys."""
    wanted = set(keys)
    return [c for c in _load().values() if wanted & set(c.phoneme_keys)]
