"""Application data directories. All user data lives under %LOCALAPPDATA%\\PronunciationCoach."""

import os
from pathlib import Path

APP_NAME = "PronunciationCoach"


def app_data_dir() -> Path:
    base = os.environ.get("LOCALAPPDATA")
    if not base:
        base = str(Path.home() / ".local" / "share")
    d = Path(base) / APP_NAME
    d.mkdir(parents=True, exist_ok=True)
    return d


def db_path() -> Path:
    return app_data_dir() / "coach.db"


def model_cache_dir() -> Path:
    d = app_data_dir() / "models"
    d.mkdir(parents=True, exist_ok=True)
    return d
