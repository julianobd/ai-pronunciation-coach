"""Pick weak phonemes from stats and produce targeted exercises.

Provider order: exercise cache -> configured LLM provider -> offline rules.
Generation runs on the caller's (worker) thread; this class has no Qt deps.
"""

from __future__ import annotations

from ..core import phoneme_kb
from ..persistence.repository import ExerciseCacheRepo, PhonemeStatsRepo
from ..providers.base import Exercise, ExerciseProvider
from ..providers.offline import OfflineProvider

# Sensible targets before the user has enough attempt history.
DEFAULT_TARGET_KEYS = ["th", "th_voiced", "r", "ih", "v", "w"]
MIN_ATTEMPTS_FOR_STATS = 5


class LearningEngine:
    def __init__(self, stats: PhonemeStatsRepo, cache: ExerciseCacheRepo,
                 provider: ExerciseProvider | None = None) -> None:
        self.stats = stats
        self.cache = cache
        self.provider = provider or OfflineProvider()
        self.offline = OfflineProvider()
        self.last_provider_error: str | None = None

    def set_provider(self, provider: ExerciseProvider) -> None:
        self.provider = provider

    def weakest_phoneme_keys(self, n: int = 2) -> list[str]:
        weak = [
            s.phoneme_key
            for s in self.stats.weakest(n=n, min_attempts=MIN_ATTEMPTS_FOR_STATS)
            if s.accuracy < 90
        ]
        for key in DEFAULT_TARGET_KEYS:
            if len(weak) >= n:
                break
            if key not in weak:
                weak.append(key)
        return weak[:n]

    def next_exercise(self, exercise_type: str,
                      target_keys: list[str] | None = None, count: int = 5) -> Exercise:
        keys = target_keys or self.weakest_phoneme_keys()
        infos = [info for info in (phoneme_kb.get_info(k) for k in keys) if info]
        if not infos:
            infos = [phoneme_kb.get_info(k) for k in DEFAULT_TARGET_KEYS[:2]]
            keys = [i.key for i in infos]

        cached = self.cache.pop_unconsumed(exercise_type, keys)
        if cached:
            return Exercise.from_payload(cached)

        self.last_provider_error = None
        if not isinstance(self.provider, OfflineProvider):
            try:
                exercise = self.provider.generate_exercise(infos, exercise_type, count)
                if exercise.items:
                    return exercise
            except Exception as exc:
                self.last_provider_error = str(exc)
        return self.offline.generate_exercise(infos, exercise_type, count)

    def prefetch(self, exercise_type: str, target_keys: list[str] | None = None) -> None:
        """Generate one exercise ahead of time into the cache (worker thread)."""
        keys = target_keys or self.weakest_phoneme_keys()
        infos = [info for info in (phoneme_kb.get_info(k) for k in keys) if info]
        if not infos or isinstance(self.provider, OfflineProvider):
            return
        try:
            exercise = self.provider.generate_exercise(infos, exercise_type)
            if exercise.items:
                self.cache.add(exercise.provider, exercise_type, keys, exercise.to_payload())
        except Exception:
            pass  # prefetch is best-effort
