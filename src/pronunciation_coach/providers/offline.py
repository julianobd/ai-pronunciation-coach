"""Rule-based exercise generator. No network, no LLM — always works.

Built from the phoneme knowledge base plus the bundled sentence bank.
"""

from __future__ import annotations

import random

from ..core import cluster_kb, sentence_bank
from ..core.phoneme_kb import PhonemeInfo
from .base import (
    CLUSTER,
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
        "What motivates you at work?",
        "What type of work environment do you prefer?",
        "What are your biggest achievements so far?",
        "What do you enjoy most about software development?",
        "How do you stay up to date with technology?",
        "What programming languages are you most comfortable with?",
        "Tell me about a recent project you worked on.",
        "What does a typical workday look like for you?",
        "What is your favorite technology and why?",
        "How do you handle tight deadlines?",
        "What is your biggest professional challenge right now?",
        "How do you approach learning a new technology?",
        "What do you expect from your next manager?",
        "What kind of team do you work best with?",
        "Why are you looking for a new opportunity?",
    ],
    "medium": [
        "Describe a project you are proud of and your role in it.",
        "Tell me about a time you disagreed with a colleague. What did you do?",
        "How do you prioritize your work when everything feels urgent?",
        "What is the most difficult problem you have solved recently?",
        "Why should we hire you over other candidates?",
        "Tell me about a production issue you helped resolve.",
        "Describe a situation where requirements changed unexpectedly.",
        "How do you estimate the effort for a task?",
        "Tell me about a time you had to learn something quickly.",
        "Describe a difficult bug you investigated.",
        "How do you ensure code quality in your projects?",
        "Tell me about a successful team collaboration.",
        "Describe a time when you missed a deadline.",
        "How do you handle technical debt?",
        "Tell me about a feature you designed from scratch.",
        "How do you balance speed and quality?",
        "Describe a time you mentored someone.",
        "Tell me about a decision you made with incomplete information.",
        "How do you approach code reviews?",
        "Describe a time when you improved a process.",
        "How do you deal with conflicting priorities?",
        "Tell me about a project that required cross-team collaboration.",
        "Describe a time when you had to take ownership unexpectedly.",
        "How do you evaluate different technical solutions?",
        "Tell me about a time you had to persuade others to adopt your idea.",
    ],
    "hard": [
        "Walk me through a situation where a project failed. What would you do differently?",
        "How would you explain a complex technical concept to a non-technical stakeholder?",
        "Describe a time you had to deliver bad news to your team or manager.",
        "What trade-offs did you consider in the most important decision of your career?",
        "Tell me about a time you received hard feedback. How did you respond?",
        "Describe a major architecture decision you made and its impact.",
        "How would you handle a critical production outage affecting thousands of users?",
        "Tell me about a time you strongly disagreed with your manager.",
        "Describe a situation where you had to make a high-risk decision.",
        "How would you scale a system that suddenly receives 100x more traffic?",
        "Tell me about a time your assumptions were completely wrong.",
        "How do you balance business needs against technical excellence?",
        "Describe the most complex system you have worked on.",
        "Tell me about a time you had to defend a controversial technical decision.",
        "How would you redesign a system that has become difficult to maintain?",
        "Describe a situation where you had to influence people without authority.",
        "Tell me about a significant mistake you made and what you learned.",
        "How do you decide when to refactor versus rebuild?",
        "Describe a time you had to manage competing stakeholder expectations.",
        "How would you approach migrating a monolith to microservices?",
        "Tell me about a project where performance was a major challenge.",
        "Describe a technical decision that had long-term consequences.",
        "How would you evaluate whether a new technology should be adopted?",
        "Tell me about a time you handled a crisis under pressure.",
        "What is the most difficult engineering trade-off you have ever faced?",
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
        elif exercise_type == SENTENCE:
            # Curated KB sentences first (easy -> hard); sentence bank tops up.
            pool: list[str] = []
            for info in weak_phonemes:
                pool.extend(info.practice_sentences)
            if len(pool) > count:
                picked = sorted(random.sample(range(len(pool)), count))
                items = [pool[i] for i in picked]
            else:
                items = list(pool)
            if len(items) < count:
                for info in weak_phonemes:
                    items.extend(
                        sentence_bank.sentences_with_phoneme(info.ipa, limit=count)
                    )
                items = list(dict.fromkeys(items))[:count]
            if not items:
                items = [sentence_bank.random_sentence() for _ in range(count)]
            title = f"Sentences with {title_target}"
        elif exercise_type == CONVERSATION:
            # Tongue twisters plus the hardest curated sentences.
            for info in weak_phonemes:
                items.extend(info.tongue_twisters)
                items.extend(info.practice_sentences[-2:])
            items = list(dict.fromkeys(items))[:count]
            if len(items) < count:
                for info in weak_phonemes:
                    items.extend(
                        sentence_bank.sentences_with_phoneme(info.ipa, limit=count)
                    )
                items = list(dict.fromkeys(items))[:count]
            if not items:
                items = [sentence_bank.random_sentence() for _ in range(count)]
            title = f"Read these lines aloud ({title_target})"
        elif exercise_type == CLUSTER:
            clusters = cluster_kb.clusters_for_phonemes(keys)
            if not clusters:
                clusters = list(cluster_kb.all_clusters().values())
            random.shuffle(clusters)
            clusters = clusters[: max(2, count // 2)]
            target = set()
            for cluster in clusters:
                target.update(cluster.phoneme_keys)
                items.append(", ".join(cluster.example_words[:4]))
                items.extend(cluster.practice_sentences[:2])
            keys = sorted(target)
            names = ", ".join(c.display.split(" (")[0] for c in clusters)
            title = f"Cluster drill: {names}"
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
