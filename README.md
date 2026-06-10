# AI Pronunciation Coach

A desktop app (Windows-first) that helps you improve spoken English pronunciation
through personalized exercises generated from your own pronunciation mistakes.

Single user, no accounts, no cloud storage — all progress, statistics and
settings live locally in `%LOCALAPPDATA%\PronunciationCoach`.

> The previous web-based version of this project lives untouched in [`Legacy/`](Legacy/)
> and served as the reference for the analysis pipeline.

## What it does

- **Records your speech** and transcribes it with [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (offline, word timestamps).
- **Analyzes pronunciation at the phoneme level**: the expected text and the
  recognized speech are converted to IPA, aligned word-by-word (Needleman-Wunsch
  over an edit-distance matrix) and then phoneme-by-phoneme, producing explicit
  errors like:

  ```json
  {"word": "think", "expected": "θ", "detected": "t", "error_type": "phoneme_substitution"}
  ```

- **Tracks per-phoneme difficulty** persistently (accuracy %, attempts) and keeps
  a daily history for charts.
- **Generates personalized exercises** targeting your weakest sounds: word
  practice, minimal pairs, sentences and conversation lines.
- **Gives actionable feedback** with articulation tips
  ("place your tongue lightly between your teeth…") from a built-in phoneme
  knowledge base.
- **Shadowing mode**: a sentence is spoken by TTS, you repeat it, and you get
  scores for pronunciation, timing and fluency (speech rate, pauses).
- **Interview simulator**: an AI interviewer asks questions, you answer out
  loud, with fluency feedback per answer.
- **Progress dashboard**: daily streak, practice minutes, accuracy over time,
  per-phoneme improvement charts.

## AI providers

Exercise/dialogue generation works with interchangeable providers
(Settings page):

| Provider | Default endpoint | Notes |
|---|---|---|
| **LMStudio** (default) | `http://localhost:1234/v1` | local, free |
| Ollama | `http://localhost:11434/v1` | local, free |
| OpenAI | `https://api.openai.com/v1` | needs API key |
| Gemini | Google REST API | needs API key |
| Offline | — | rule-based, always available |

If no provider is reachable the app silently falls back to the built-in
offline generator — everything keeps working without any LLM.

## Install & run

Requires Python 3.10+.

```bash
pip install -e .
pronunciation-coach            # or: python -m pronunciation_coach
```

On first run the speech recognition model (~75 MB) is downloaded automatically.
Optional extras:

```bash
pip install -e .[tts-neural]   # Silero neural TTS (better voice, needs torch)
pip install -e .[g2p]          # better IPA for out-of-vocabulary words
pip install -e .[dev]          # pytest
```

Without `tts-neural`, shadowing uses the built-in Windows (SAPI) voice.

## Headless smoke test

```bash
python -m pronunciation_coach.cli --transcript "Tink about tree tings." "Think about three things."
python -m pronunciation_coach.cli recording.wav "Think about three things."
```

## Tests

```bash
python -m pytest
```

## Architecture

```
src/pronunciation_coach/
├── core/          pure analysis logic (IPA, alignment, scoring, metrics)
├── speech/        ASR (faster-whisper) and TTS (Silero / SAPI)
├── audio/         microphone recording & playback (sounddevice)
├── providers/     LLM exercise generation + offline fallback
├── persistence/   SQLite (attempts, phoneme stats, history, settings)
├── services/      orchestration between engine, storage and UI
└── ui/            PySide6 pages and widgets
```

Troubleshooting:

- **Microphone errors** — check *Windows Settings → Privacy & security →
  Microphone* and allow desktop apps.
- **LLM exercises not appearing** — make sure LMStudio/Ollama is running with a
  model loaded, then use *Settings → Test connection*. Offline exercises are
  used in the meantime.
