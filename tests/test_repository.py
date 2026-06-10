from datetime import date, timedelta

from pronunciation_coach.persistence.db import Database
from pronunciation_coach.persistence.repository import (
    AttemptRepo,
    ExerciseCacheRepo,
    PhonemeStatsRepo,
    SettingsRepo,
)


def make_db(tmp_path):
    return Database(tmp_path / "test.db")


def test_settings_roundtrip(tmp_path):
    repo = SettingsRepo(make_db(tmp_path))
    repo.set_many({"provider": "ollama", "asr_model_size": "tiny.en"})
    repo.set_many({"provider": "openai"})  # upsert
    values = repo.get_all()
    assert values["provider"] == "openai"
    assert values["asr_model_size"] == "tiny.en"


def test_attempts_and_daily_summary(tmp_path):
    repo = AttemptRepo(make_db(tmp_path))
    repo.add("practice", "hello world", "hello world", 90.0, 3.0, {})
    repo.add("practice", "good morning", "good morning", 70.0, 2.0, {})
    summary = repo.daily_summary()
    assert summary["attempts"] == 2
    assert summary["accuracy"] == 80.0
    assert summary["minutes"] == round(5.0 / 60, 1)


def test_streak_counts_today(tmp_path):
    db = make_db(tmp_path)
    repo = AttemptRepo(db)
    repo.add("practice", "x", "x", 80.0, 1.0, {})
    assert repo.current_streak() == 1


def test_streak_consecutive_days(tmp_path):
    db = make_db(tmp_path)
    repo = AttemptRepo(db)
    today = date.today()
    for offset in (0, 1, 2, 4):  # gap at day 3
        day = (today - timedelta(days=offset)).isoformat()
        db.execute(
            "INSERT INTO attempts(created_at, mode, expected_text) VALUES(?, 'practice', 'x')",
            (f"{day}T10:00:00",),
        )
    assert repo.current_streak() == 3


def test_streak_zero_when_stale(tmp_path):
    db = make_db(tmp_path)
    repo = AttemptRepo(db)
    old_day = (date.today() - timedelta(days=3)).isoformat()
    db.execute(
        "INSERT INTO attempts(created_at, mode, expected_text) VALUES(?, 'practice', 'x')",
        (f"{old_day}T10:00:00",),
    )
    assert repo.current_streak() == 0


def test_phoneme_stats_accumulate(tmp_path):
    repo = PhonemeStatsRepo(make_db(tmp_path))
    repo.record("th", attempts=10, errors=6)
    repo.record("th", attempts=10, errors=2)
    stats = {s.phoneme_key: s for s in repo.all_stats()}
    assert stats["th"].attempts == 20
    assert stats["th"].errors == 8
    assert stats["th"].accuracy == 60.0


def test_weakest_respects_min_attempts(tmp_path):
    repo = PhonemeStatsRepo(make_db(tmp_path))
    repo.record("th", attempts=20, errors=15)   # 25% but enough attempts
    repo.record("zh", attempts=2, errors=2)     # 0% but too few attempts
    weakest = repo.weakest(n=3, min_attempts=5)
    assert [s.phoneme_key for s in weakest] == ["th"]


def test_phoneme_history(tmp_path):
    repo = PhonemeStatsRepo(make_db(tmp_path))
    repo.record("r", attempts=4, errors=2)
    history = repo.history("r")
    assert len(history) == 1
    assert history[0][1] == 50.0


def test_exercise_cache_pop(tmp_path):
    repo = ExerciseCacheRepo(make_db(tmp_path))
    payload = {"exercise_type": "word", "target_phonemes": ["th"],
               "title": "t", "items": ["think"], "provider": "lmstudio"}
    repo.add("lmstudio", "word", ["th"], payload)
    assert repo.pop_unconsumed("word", ["th"]) == payload
    assert repo.pop_unconsumed("word", ["th"]) is None  # consumed
