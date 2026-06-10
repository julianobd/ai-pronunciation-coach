"""Headless smoke test:  python -m pronunciation_coach.cli <audio.wav> "<expected text>"

Prints the full analysis as JSON. Also accepts --transcript to skip ASR:
  python -m pronunciation_coach.cli --transcript "tink about tree tings" "Think about three things."
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys


def _to_jsonable(obj):
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return {k: _to_jsonable(v) for k, v in dataclasses.asdict(obj).items()}
    if isinstance(obj, (list, tuple)):
        return [_to_jsonable(v) for v in obj]
    if isinstance(obj, dict):
        return {k: _to_jsonable(v) for k, v in obj.items()}
    return obj


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # IPA output on cp1252 consoles
    parser = argparse.ArgumentParser(description="Analyze pronunciation from a wav file.")
    parser.add_argument("source", help="path to .wav file, or detected transcript with --transcript")
    parser.add_argument("expected", help="the expected (read) text")
    parser.add_argument("--transcript", action="store_true",
                        help="treat <source> as the detected transcript instead of audio")
    parser.add_argument("--model", default="base.en", help="faster-whisper model size")
    args = parser.parse_args(argv)

    from .core.analysis import PronunciationAnalyzer

    if args.transcript:
        analyzer = PronunciationAnalyzer(asr=None)
        analysis = analyzer.analyze_transcript(args.expected, args.source)
    else:
        import soundfile as sf

        from .speech.asr import FasterWhisperASR

        audio, sample_rate = sf.read(args.source, dtype="float32")
        if audio.ndim > 1:
            audio = audio.mean(axis=1)
        if sample_rate != 16000:
            import numpy as np

            duration = audio.shape[0] / sample_rate
            target_len = int(duration * 16000)
            audio = np.interp(
                np.linspace(0, audio.shape[0] - 1, target_len),
                np.arange(audio.shape[0]),
                audio,
            ).astype("float32")
        analyzer = PronunciationAnalyzer(FasterWhisperASR(args.model))
        analysis = analyzer.analyze(audio, args.expected)

    print(json.dumps(_to_jsonable(analysis), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
