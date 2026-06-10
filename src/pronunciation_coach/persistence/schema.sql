CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    id         INTEGER PRIMARY KEY,
    started_at TEXT NOT NULL,
    ended_at   TEXT,
    mode       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS attempts (
    id               INTEGER PRIMARY KEY,
    session_id       INTEGER REFERENCES sessions(id),
    created_at       TEXT NOT NULL,
    mode             TEXT NOT NULL,
    expected_text    TEXT NOT NULL,
    transcript       TEXT,
    overall_accuracy REAL,
    duration_s       REAL,
    detail_json      TEXT
);

CREATE TABLE IF NOT EXISTS phoneme_stats (
    phoneme_key TEXT PRIMARY KEY,
    attempts    REAL NOT NULL DEFAULT 0,
    errors      REAL NOT NULL DEFAULT 0,
    accuracy    REAL NOT NULL DEFAULT 0,
    updated_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS phoneme_history (
    phoneme_key TEXT NOT NULL,
    day         TEXT NOT NULL,
    attempts    REAL NOT NULL DEFAULT 0,
    errors      REAL NOT NULL DEFAULT 0,
    PRIMARY KEY (phoneme_key, day)
);

CREATE TABLE IF NOT EXISTS exercises_cache (
    id              INTEGER PRIMARY KEY,
    created_at      TEXT NOT NULL,
    provider        TEXT NOT NULL,
    exercise_type   TEXT NOT NULL,
    target_phonemes TEXT NOT NULL,
    payload_json    TEXT NOT NULL,
    consumed        INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_attempts_created ON attempts(created_at);
CREATE INDEX IF NOT EXISTS idx_history_key ON phoneme_history(phoneme_key, day);
