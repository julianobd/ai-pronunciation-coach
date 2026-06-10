"""Progress queries for the Home and Progress pages."""

from __future__ import annotations

from ..persistence.repository import AttemptRepo, PhonemeStat, PhonemeStatsRepo


class ProgressService:
    def __init__(self, attempts: AttemptRepo, stats: PhonemeStatsRepo) -> None:
        self.attempts = attempts
        self.stats = stats

    def current_streak(self) -> int:
        return self.attempts.current_streak()

    def today_summary(self) -> dict:
        return self.attempts.daily_summary()

    def weak_phonemes(self, n: int = 5) -> list[PhonemeStat]:
        return self.stats.weakest(n=n, min_attempts=3)

    def all_phoneme_stats(self) -> list[PhonemeStat]:
        return self.stats.all_stats()

    def accuracy_history(self, days: int = 90) -> list[tuple[str, float]]:
        return self.attempts.accuracy_by_day(days)

    def minutes_history(self, days: int = 30) -> list[tuple[str, float]]:
        return self.attempts.minutes_by_day(days)

    def phoneme_history(self, key: str, days: int = 90) -> list[tuple[str, float]]:
        return self.stats.history(key, days)
