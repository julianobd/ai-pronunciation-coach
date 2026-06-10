"""AI Pronunciation Coach - desktop English pronunciation trainer."""

import os

# ctranslate2 (faster-whisper) and torch (Silero TTS) both ship an OpenMP
# runtime; on Windows loading both in one process aborts with OMP Error #15
# unless duplicates are allowed. Must be set before either library loads.
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

__version__ = "0.1.0"
