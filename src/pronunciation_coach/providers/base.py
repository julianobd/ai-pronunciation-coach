"""Exercise provider abstraction: OpenAI / Gemini / Ollama / LMStudio / offline.

Every provider returns the same Exercise shape; LLM output is validated
against a JSON schema with retries before being trusted.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import jsonschema

WORD, MINIMAL_PAIR, SENTENCE, CONVERSATION, CLUSTER = (
    "word", "minimal_pair", "sentence", "conversation", "cluster",
)
EXERCISE_TYPES = [WORD, MINIMAL_PAIR, SENTENCE, CONVERSATION, CLUSTER]

EXERCISE_TYPE_LABELS = {
    WORD: "Word practice",
    MINIMAL_PAIR: "Minimal pairs",
    SENTENCE: "Sentences",
    CONVERSATION: "Conversation",
    CLUSTER: "Consonant clusters",
}


@dataclass
class Exercise:
    exercise_type: str
    target_phonemes: list[str]          # teachable keys, e.g. ["th"]
    title: str
    items: list[str]                    # texts the learner reads aloud
    provider: str = "offline"

    def to_payload(self) -> dict:
        return {
            "exercise_type": self.exercise_type,
            "target_phonemes": self.target_phonemes,
            "title": self.title,
            "items": self.items,
            "provider": self.provider,
        }

    @classmethod
    def from_payload(cls, payload: dict) -> "Exercise":
        return cls(**payload)


EXERCISE_SCHEMA = {
    "type": "object",
    "required": ["title", "items"],
    "properties": {
        "title": {"type": "string"},
        "items": {
            "type": "array",
            "minItems": 1,
            "items": {"type": "string", "minLength": 1},
        },
    },
}

INTERVIEW_SCHEMA = {
    "type": "object",
    "required": ["reply"],
    "properties": {
        "reply": {"type": "string", "minLength": 1},
        "done": {"type": "boolean"},
    },
}


class ProviderError(RuntimeError):
    pass


class ExerciseProvider(ABC):
    name: str = "base"

    @abstractmethod
    def is_available(self) -> bool: ...

    @abstractmethod
    def generate_exercise(self, weak_phonemes: list, exercise_type: str,
                          count: int = 5) -> Exercise:
        """weak_phonemes: list of core.phoneme_kb.PhonemeInfo."""

    @abstractmethod
    def generate_interview_turn(self, job_role: str, difficulty: str,
                                history: list[dict]) -> dict:
        """history: [{"role": "interviewer"|"candidate", "text": ...}].
        Returns {"reply": str, "done": bool}."""


def parse_json_response(text: str, schema: dict) -> dict:
    """Extract and validate a JSON object from an LLM response."""
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ProviderError(f"No JSON object in response: {text[:200]}")
    data = json.loads(text[start : end + 1])
    jsonschema.validate(data, schema)
    return data
