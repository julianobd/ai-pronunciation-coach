"""Google Gemini provider via the REST generateContent endpoint (httpx only)."""

from __future__ import annotations

import httpx

from ..core.phoneme_kb import PhonemeInfo
from .base import (
    EXERCISE_SCHEMA,
    INTERVIEW_SCHEMA,
    Exercise,
    ExerciseProvider,
    ProviderError,
    parse_json_response,
)
from .openai_compat import _EXERCISE_PROMPTS, _INTERVIEW_PROMPT, _SYSTEM

DEFAULT_MODEL = "gemini-2.0-flash"
BASE_URL = "https://generativelanguage.googleapis.com/v1beta"


class GeminiProvider(ExerciseProvider):
    name = "gemini"

    def __init__(self, api_key: str, model: str = "", timeout: float = 60.0) -> None:
        self.api_key = api_key
        self.model = model or DEFAULT_MODEL
        self.timeout = timeout

    def is_available(self) -> bool:
        if not self.api_key:
            return False
        try:
            response = httpx.get(
                f"{BASE_URL}/models/{self.model}",
                params={"key": self.api_key},
                timeout=3.0,
            )
            return response.status_code == 200
        except Exception:
            return False

    def _generate(self, user_prompt: str, schema: dict) -> dict:
        last_error: Exception | None = None
        for _attempt in range(3):
            try:
                response = httpx.post(
                    f"{BASE_URL}/models/{self.model}:generateContent",
                    params={"key": self.api_key},
                    json={
                        "system_instruction": {"parts": [{"text": _SYSTEM}]},
                        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
                        "generationConfig": {
                            "responseMimeType": "application/json",
                            "temperature": 0.7,
                        },
                    },
                    timeout=self.timeout,
                )
                response.raise_for_status()
                content = response.json()["candidates"][0]["content"]["parts"][0]["text"]
                return parse_json_response(content, schema)
            except Exception as exc:
                last_error = exc
        raise ProviderError(f"gemini failed after retries: {last_error}")

    def generate_exercise(self, weak_phonemes: list[PhonemeInfo], exercise_type: str,
                          count: int = 5) -> Exercise:
        targets = "; ".join(
            f"{p.display} (IPA {'/'.join(p.ipa)}), e.g. {', '.join(p.example_words[:3])}"
            for p in weak_phonemes
        )
        prompt = _EXERCISE_PROMPTS[exercise_type].format(targets=targets, count=count)
        data = self._generate(prompt, EXERCISE_SCHEMA)
        return Exercise(
            exercise_type=exercise_type,
            target_phonemes=[p.key for p in weak_phonemes],
            title=data["title"],
            items=[item.strip() for item in data["items"] if item.strip()][:count * 2],
            provider=self.name,
        )

    def generate_interview_turn(self, job_role: str, difficulty: str,
                                history: list[dict]) -> dict:
        transcript = "\n".join(f"{t['role']}: {t['text']}" for t in history) or "(start)"
        prompt = _INTERVIEW_PROMPT.format(
            job_role=job_role, difficulty=difficulty, history=transcript
        )
        data = self._generate(prompt, INTERVIEW_SCHEMA)
        return {"reply": data["reply"], "done": bool(data.get("done", False))}
