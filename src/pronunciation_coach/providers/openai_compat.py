"""OpenAI-compatible chat provider. Covers OpenAI, LMStudio and Ollama —
they all speak POST {base_url}/chat/completions; only base_url/key differ.
"""

from __future__ import annotations

import httpx

from ..core.phoneme_kb import PhonemeInfo
from .base import (
    EXERCISE_SCHEMA,
    EXERCISE_TYPE_LABELS,
    INTERVIEW_SCHEMA,
    Exercise,
    ExerciseProvider,
    ProviderError,
    parse_json_response,
)

_SYSTEM = (
    "You are an English pronunciation coach creating practice material for a "
    "non-native learner. Always respond with a single JSON object and nothing else."
)

_EXERCISE_PROMPTS = {
    "word": (
        "Create a word practice exercise. Return JSON: "
        '{{"title": string, "items": [string]}} where items is a list of {count} '
        "common English WORDS that each contain the target sound(s): {targets}. "
        "Choose everyday words a learner would actually use."
    ),
    "minimal_pair": (
        "Create a minimal pair exercise. Return JSON: "
        '{{"title": string, "items": [string]}} where each item is a minimal pair '
        'formatted as "word1 — word2" contrasting the target sound(s): {targets}. '
        "Return {count} pairs. The two words must differ only in the target sound."
    ),
    "sentence": (
        "Create a sentence practice exercise. Return JSON: "
        '{{"title": string, "items": [string]}} where items is {count} natural English '
        "sentences (8-14 words each), each containing several words with the target "
        "sound(s): {targets}."
    ),
    "conversation": (
        "Create a short dialogue practice. Return JSON: "
        '{{"title": string, "items": [string]}} where items is {count} lines of one '
        "side of a natural everyday conversation. The lines must naturally contain many "
        "words with the target sound(s): {targets}. The learner will read each line aloud."
    ),
}

_INTERVIEW_PROMPT = (
    "You are a job interviewer for the role: {job_role}. Difficulty: {difficulty}. "
    "Conversation so far:\n{history}\n\n"
    "Ask the next interview question (one question only, natural spoken English). "
    "After 5 questions, wrap up the interview. Return JSON: "
    '{{"reply": string, "done": boolean}} where done is true only when wrapping up.'
)


class OpenAICompatProvider(ExerciseProvider):
    def __init__(self, base_url: str, api_key: str = "", model: str = "",
                 name: str = "lmstudio", timeout: float = 60.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.name = name
        self.timeout = timeout

    def _headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def is_available(self) -> bool:
        try:
            response = httpx.get(f"{self.base_url}/models", headers=self._headers(),
                                 timeout=2.0)
            return response.status_code == 200
        except Exception:
            return False

    def _resolve_model(self) -> str:
        if self.model:
            return self.model
        # Local servers (LMStudio/Ollama): use whatever model is loaded.
        response = httpx.get(f"{self.base_url}/models", headers=self._headers(),
                             timeout=5.0)
        response.raise_for_status()
        models = response.json().get("data", [])
        if not models:
            raise ProviderError("No model loaded on the local LLM server.")
        return models[0]["id"]

    def _chat(self, user_prompt: str, schema: dict) -> dict:
        model = self._resolve_model()
        last_error: Exception | None = None
        for _attempt in range(3):
            try:
                response = httpx.post(
                    f"{self.base_url}/chat/completions",
                    headers=self._headers(),
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": _SYSTEM},
                            {"role": "user", "content": user_prompt},
                        ],
                        "temperature": 0.7,
                    },
                    timeout=self.timeout,
                )
                response.raise_for_status()
                content = response.json()["choices"][0]["message"]["content"]
                return parse_json_response(content, schema)
            except Exception as exc:
                last_error = exc
        raise ProviderError(f"{self.name} failed after retries: {last_error}")

    def generate_exercise(self, weak_phonemes: list[PhonemeInfo], exercise_type: str,
                          count: int = 5) -> Exercise:
        targets = "; ".join(
            f"{p.display} (IPA {'/'.join(p.ipa)}), e.g. {', '.join(p.example_words[:3])}"
            for p in weak_phonemes
        )
        prompt = _EXERCISE_PROMPTS[exercise_type].format(targets=targets, count=count)
        data = self._chat(prompt, EXERCISE_SCHEMA)
        return Exercise(
            exercise_type=exercise_type,
            target_phonemes=[p.key for p in weak_phonemes],
            title=data["title"] or EXERCISE_TYPE_LABELS[exercise_type],
            items=[item.strip() for item in data["items"] if item.strip()][:count * 2],
            provider=self.name,
        )

    def generate_interview_turn(self, job_role: str, difficulty: str,
                                history: list[dict]) -> dict:
        transcript = "\n".join(f"{t['role']}: {t['text']}" for t in history) or "(start)"
        prompt = _INTERVIEW_PROMPT.format(
            job_role=job_role, difficulty=difficulty, history=transcript
        )
        data = self._chat(prompt, INTERVIEW_SCHEMA)
        return {"reply": data["reply"], "done": bool(data.get("done", False))}
