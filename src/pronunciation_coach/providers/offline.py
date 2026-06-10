"""Rule-based exercise generator. No network, no LLM — always works.

Built from the phoneme knowledge base plus the bundled sentence bank.
"""

from __future__ import annotations

import random

from ..core import sentence_bank
from ..core.phoneme_kb import PhonemeInfo
from .base import (
    CONVERSATION,
    MINIMAL_PAIR,
    SENTENCE,
    WORD,
    Exercise,
    ExerciseProvider,
)

INTERVIEW_QUESTIONS = {
    "easy": [
        "Tell me a little about yourself.",
        "What do you do in your current job?",
        "Why are you interested in this position?",
        "What are your strengths?",
        "Where do you see yourself in five years?",
    ],
    "medium": [
        "Describe a project you are proud of and your role in it.",
        "Tell me about a time you disagreed with a colleague. What did you do?",
        "How do you prioritize your work when everything feels urgent?",
        "What is the most difficult problem you have solved recently?",
        "Why should we hire you over other candidates?",
    ],
    "hard": [
        "Walk me through a situation where a project failed. What would you do differently?",
        "How would you explain a complex technical concept to a non-technical stakeholder?",
        "Describe a time you had to deliver bad news to your team or manager.",
        "What trade-offs did you consider in the most important decision of your career?",
        "Tell me about a time you received hard feedback. How did you respond?",
    ],
}

CLOSING = "Thank you, that was my last question. Do you have any questions for me?"


class OfflineProvider(ExerciseProvider):
    name = "offline"

    def is_available(self) -> bool:
        return True

    def generate_exercise(self, weak_phonemes: list[PhonemeInfo], exercise_type: str,
                          count: int = 5) -> Exercise:
        keys = [p.key for p in weak_phonemes]
        title_target = ", ".join(p.display.split(" (")[0] for p in weak_phonemes)

        items: list[str] = []
        if exercise_type == WORD:
            for info in weak_phonemes:
                items.extend(info.example_words)
            random.shuffle(items)
            items = items[: max(count, 5)]
            title = f"Practice words with {title_target}"
        elif exercise_type == MINIMAL_PAIR:
            pairs = []
            for info in weak_phonemes:
                pairs.extend(info.minimal_pairs)
            random.shuffle(pairs)
            items = [f"{a} — {b}" for a, b in pairs[: max(count, 5)]]
            if not items:  # phoneme with no listed pairs (e.g. schwa)
                items = [", ".join(info.example_words[:2]) for info in weak_phonemes]
            title = f"Minimal pairs for {title_target}"
        elif exercise_type in (SENTENCE, CONVERSATION):
            for info in weak_phonemes:
                items.extend(
                    sentence_bank.sentences_with_phoneme(info.ipa, limit=count)
                )
            random.shuffle(items)
            items = items[:count]
            if not items:
                items = [sentence_bank.random_sentence() for _ in range(count)]
            title = (
                f"Read these lines aloud ({title_target})"
                if exercise_type == CONVERSATION
                else f"Sentences with {title_target}"
            )
        else:
            raise ValueError(f"Unknown exercise type: {exercise_type}")

        return Exercise(
            exercise_type=exercise_type,
            target_phonemes=keys,
            title=title,
            items=items,
            provider=self.name,
        )

    def generate_interview_turn(self, job_role: str, difficulty: str,
                                history: list[dict]) -> dict:
        questions = INTERVIEW_QUESTIONS.get(difficulty, INTERVIEW_QUESTIONS["medium"])
        asked = sum(1 for turn in history if turn["role"] == "interviewer")
        if asked >= len(questions):
            return {"reply": CLOSING, "done": True}
        return {"reply": questions[asked], "done": False}
