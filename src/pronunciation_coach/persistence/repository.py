"""Typed repositories over the SQLite database."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from .db import Database


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _today() -> str:
    return date.today().isoformat()


class SettingsRepo:
    def __init__(self, db: Database) -> None:
        self.db = db

    def get_all(self) -> dict[str, str]:
        return {row["key"]: row["value"] for row in self.db.query("SELECT key, value FROM settings")}

    def set_many(self, values: dict[str, str]) -> None:
        for key, value in values.items():
            self.db.execute(
                "INSERT INTO settings(key, value) VALUES(?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, value),
            )


class SessionRepo:
    def __init__(self, db: Database) -> None:
        self.db = db

    def start(self, mode: str) -> int:
        cursor = self.db.execute(
            "INSERT INTO sessions(started_at, mode) VALUES(?, ?)", (_now(), mode)
        )
        return cursor.lastrowid

    def end(self, session_id: int) -> None:
        self.db.execute("UPDATE sessions SET ended_at = ? WHERE id = ?", (_now(), session_id))


class AttemptRepo:
    def __init__(self, db: Database) -> None:
        self.db = db

    def add(self, mode: str, expected_text: str, transcript: str,
            overall_accuracy: float, duration_s: float, detail: dict,
            session_id: int | None = None) -> int:
        cursor = self.db.execute(
            "INSERT INTO attempts(session_id, created_at, mode, expected_text, transcript,"
            " overall_accuracy, duration_s, detail_json) VALUES(?,?,?,?,?,?,?,?)",
            (session_id, _now(), mode, expected_text, transcript,
             overall_accuracy, duration_s, json.dumps(detail, ensure_ascii=False)),
        )
        return cursor.lastrowid

    def practice_days(self) -> list[str]:
        rows = self.db.query(
            "SELECT DISTINCT date(created_at) AS day FROM attempts ORDER BY day DESC"
        )
        return [row["day"] for row in rows]

    def current_streak(self) -> int:
        days = {date.fromisoformat(d) for d in self.practice_days()}
        if not days:
            return 0
        cursor = date.today()
        if cursor not in days:
            cursor -= timedelta(days=1)  # today not yet practiced still keeps streak
            if cursor not in days:
                return 0
        streak = 0
        while cursor in days:
            streak += 1
            cursor -= timedelta(days=1)
        return streak

    def daily_summary(self, day: str | None = None) -> dict:
        day = day or _today()
        row = self.db.query_one(
            "SELECT COUNT(*) AS attempts, COALESCE(SUM(duration_s), 0) AS seconds,"
            " COALESCE(AVG(overall_accuracy), 0) AS accuracy"
            " FROM attempts WHERE date(created_at) = ?",
            (day,),
        )
        return {
            "attempts": row["attempts"],
            "minutes": round(row["seconds"] / 60.0, 1),
            "accuracy": round(row["accuracy"], 1),
        }

    def accuracy_by_day(self, days: int = 90) -> list[tuple[str, float]]:
        since = (date.today() - timedelta(days=days)).isoformat()
        rows = self.db.query(
            "SELECT date(created_at) AS day, AVG(overall_accuracy) AS accuracy"
            " FROM attempts WHERE date(created_at) >= ? AND overall_accuracy IS NOT NULL"
            " GROUP BY day ORDER BY day",
            (since,),
        )
        return [(row["day"], round(row["accuracy"], 1)) for row in rows]

    def minutes_by_day(self, days: int = 30) -> list[tuple[str, float]]:
        since = (date.today() - timedelta(days=days)).isoformat()
        rows = self.db.query(
            "SELECT date(created_at) AS day, COALESCE(SUM(duration_s), 0) / 60.0 AS minutes"
            " FROM attempts WHERE date(created_at) >= ? GROUP BY day ORDER BY day",
            (since,),
        )
        return [(row["day"], round(row["minutes"], 1)) for row in rows]


@dataclass
class PhonemeStat:
    phoneme_key: str
    attempts: float
    errors: float
    accuracy: float


class PhonemeStatsRepo:
    def __init__(self, db: Database) -> None:
        self.db = db

    def record(self, phoneme_key: str, attempts: float, errors: float) -> None:
        """Add attempt/error counts to the rolling stat and the daily rollup."""
        self.db.execute(
            "INSERT INTO phoneme_stats(phoneme_key, attempts, errors, accuracy, updated_at)"
            " VALUES(?, ?, ?, CASE WHEN ? > 0 THEN 100.0 * (? - ?) / ? ELSE 0 END, ?)"
            " ON CONFLICT(phoneme_key) DO UPDATE SET"
            "  attempts = phoneme_stats.attempts + excluded.attempts,"
            "  errors = phoneme_stats.errors + excluded.errors,"
            "  accuracy = 100.0 * (phoneme_stats.attempts + excluded.attempts"
            "             - phoneme_stats.errors - excluded.errors)"
            "             / (phoneme_stats.attempts + excluded.attempts),"
            "  updated_at = excluded.updated_at",
            (phoneme_key, attempts, errors, attempts, attempts, errors, attempts, _now()),
        )
        self.db.execute(
            "INSERT INTO phoneme_history(phoneme_key, day, attempts, errors)"
            " VALUES(?, ?, ?, ?)"
            " ON CONFLICT(phoneme_key, day) DO UPDATE SET"
            "  attempts = phoneme_history.attempts + excluded.attempts,"
            "  errors = phoneme_history.errors + excluded.errors",
            (phoneme_key, _today(), attempts, errors),
        )

    def all_stats(self) -> list[PhonemeStat]:
        rows = self.db.query(
            "SELECT phoneme_key, attempts, errors, accuracy FROM phoneme_stats"
            " ORDER BY accuracy ASC"
        )
        return [PhonemeStat(r["phoneme_key"], r["attempts"], r["errors"], r["accuracy"]) for r in rows]

    def weakest(self, n: int = 3, min_attempts: float = 5) -> list[PhonemeStat]:
        rows = self.db.query(
            "SELECT phoneme_key, attempts, errors, accuracy FROM phoneme_stats"
            " WHERE attempts >= ? ORDER BY accuracy ASC LIMIT ?",
            (min_attempts, n),
        )
        return [PhonemeStat(r["phoneme_key"], r["attempts"], r["errors"], r["accuracy"]) for r in rows]

    def history(self, phoneme_key: str, days: int = 90) -> list[tuple[str, float]]:
        since = (date.today() - timedelta(days=days)).isoformat()
        rows = self.db.query(
            "SELECT day, attempts, errors FROM phoneme_history"
            " WHERE phoneme_key = ? AND day >= ? ORDER BY day",
            (phoneme_key, since),
        )
        return [
            (r["day"], round(100.0 * (r["attempts"] - r["errors"]) / r["attempts"], 1))
            for r in rows if r["attempts"] > 0
        ]


class ExerciseCacheRepo:
    def __init__(self, db: Database) -> None:
        self.db = db

    def add(self, provider: str, exercise_type: str, target_phonemes: list[str],
            payload: dict) -> int:
        cursor = self.db.execute(
            "INSERT INTO exercises_cache(created_at, provider, exercise_type,"
            " target_phonemes, payload_json) VALUES(?,?,?,?,?)",
            (_now(), provider, exercise_type, json.dumps(target_phonemes),
             json.dumps(payload, ensure_ascii=False)),
        )
        return cursor.lastrowid

    def pop_unconsumed(self, exercise_type: str, target_phonemes: list[str]) -> dict | None:
        row = self.db.query_one(
            "SELECT id, payload_json FROM exercises_cache"
            " WHERE exercise_type = ? AND target_phonemes = ? AND consumed = 0"
            " ORDER BY created_at DESC LIMIT 1",
            (exercise_type, json.dumps(target_phonemes)),
        )
        if row is None:
            return None
        self.db.execute("UPDATE exercises_cache SET consumed = 1 WHERE id = ?", (row["id"],))
        return json.loads(row["payload_json"])
