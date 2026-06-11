"""Application configuration, persisted via the settings table."""

from __future__ import annotations

from dataclasses import dataclass, asdict, fields


PROVIDER_PRESETS = {
    "lmstudio": {"base_url": "http://localhost:1234/v1", "needs_key": False},
    "ollama": {"base_url": "http://localhost:11434/v1", "needs_key": False},
    "openai": {"base_url": "https://api.openai.com/v1", "needs_key": True},
    "gemini": {"base_url": "https://generativelanguage.googleapis.com", "needs_key": True},
    "offline": {"base_url": "", "needs_key": False},
}


@dataclass
class AppConfig:
    provider: str = "lmstudio"
    provider_base_url: str = "http://localhost:1234/v1"
    provider_api_key: str = ""
    provider_model: str = ""
    mic_device: int = -1  # -1 = system default
    asr_model_size: str = "base.en"
    tts_engine: str = "auto"  # auto | omnivoice | silero | sapi
    daily_goal_minutes: int = 10

    @classmethod
    def from_settings(cls, values: dict[str, str]) -> "AppConfig":
        cfg = cls()
        for f in fields(cls):
            if f.name in values:
                raw = values[f.name]
                if f.type in ("int", int):
                    try:
                        setattr(cfg, f.name, int(raw))
                    except ValueError:
                        pass
                else:
                    setattr(cfg, f.name, raw)
        return cfg

    def to_settings(self) -> dict[str, str]:
        return {k: str(v) for k, v in asdict(self).items()}
