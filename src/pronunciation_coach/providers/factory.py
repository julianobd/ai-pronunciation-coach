"""Provider construction from AppConfig, with offline fallback."""

from __future__ import annotations

from ..config import PROVIDER_PRESETS, AppConfig
from .base import ExerciseProvider
from .gemini import GeminiProvider
from .offline import OfflineProvider
from .openai_compat import OpenAICompatProvider


def create_provider(config: AppConfig) -> ExerciseProvider:
    """Build the configured provider. Callers should still catch ProviderError
    and fall back to OfflineProvider (see services.learning_engine)."""
    name = config.provider
    if name == "offline":
        return OfflineProvider()
    if name == "gemini":
        return GeminiProvider(api_key=config.provider_api_key, model=config.provider_model)
    if name in ("lmstudio", "ollama", "openai"):
        base_url = config.provider_base_url or PROVIDER_PRESETS[name]["base_url"]
        return OpenAICompatProvider(
            base_url=base_url,
            api_key=config.provider_api_key,
            model=config.provider_model,
            name=name,
        )
    return OfflineProvider()
