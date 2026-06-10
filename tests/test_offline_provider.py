from pronunciation_coach.core import phoneme_kb
from pronunciation_coach.providers.base import (
    EXERCISE_SCHEMA,
    parse_json_response,
)
from pronunciation_coach.providers.offline import OfflineProvider


def weak():
    return [phoneme_kb.get_info("th")]


def test_word_exercise():
    exercise = OfflineProvider().generate_exercise(weak(), "word")
    assert exercise.exercise_type == "word"
    assert exercise.target_phonemes == ["th"]
    assert len(exercise.items) >= 5
    assert all(isinstance(item, str) and item for item in exercise.items)


def test_minimal_pair_exercise():
    exercise = OfflineProvider().generate_exercise(weak(), "minimal_pair")
    assert all("—" in item for item in exercise.items)


def test_sentence_exercise_contains_target_sound():
    exercise = OfflineProvider().generate_exercise(weak(), "sentence", count=3)
    assert 1 <= len(exercise.items) <= 3


def test_interview_progression_and_completion():
    provider = OfflineProvider()
    history = []
    for _ in range(5):
        turn = provider.generate_interview_turn("dev", "easy", history)
        assert turn["done"] is False
        history.append({"role": "interviewer", "text": turn["reply"]})
        history.append({"role": "candidate", "text": "my answer"})
    final = provider.generate_interview_turn("dev", "easy", history)
    assert final["done"] is True


def test_parse_json_response_plain():
    data = parse_json_response('{"title": "t", "items": ["a"]}', EXERCISE_SCHEMA)
    assert data["items"] == ["a"]


def test_parse_json_response_fenced_with_prose():
    text = 'Here you go:\n```json\n{"title": "t", "items": ["a", "b"]}\n```\nEnjoy!'
    data = parse_json_response(text, EXERCISE_SCHEMA)
    assert data["title"] == "t"
