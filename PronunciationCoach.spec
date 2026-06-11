# -*- mode: python ; coding: utf-8 -*-
# Build:  python -m PyInstaller PronunciationCoach.spec --noconfirm
# Output: dist/PronunciationCoach/PronunciationCoach.exe (onedir, windowed)
#
# torch/torchaudio are intentionally EXCLUDED to keep the build small:
# in the .exe, shadowing uses the Windows SAPI voice (the app falls back
# automatically). The Whisper ASR model is still downloaded on first run
# to %LOCALAPPDATA%\PronunciationCoach\models.

from PyInstaller.utils.hooks import collect_all

datas = [
    ("src/pronunciation_coach/data/sentences_en.csv", "pronunciation_coach/data"),
    ("src/pronunciation_coach/data/phoneme_kb.json", "pronunciation_coach/data"),
    ("src/pronunciation_coach/data/clusters_kb.json", "pronunciation_coach/data"),
    ("src/pronunciation_coach/persistence/schema.sql", "pronunciation_coach/persistence"),
]
binaries = []
hiddenimports = [
    "pyttsx3.drivers",
    "pyttsx3.drivers.sapi5",
]

# Packages with bundled data files / native libs that static analysis misses:
# faster_whisper ships the Silero VAD onnx asset, ctranslate2 its DLLs,
# eng_to_ipa its CMU dictionary JSONs.
for package in ("faster_whisper", "ctranslate2", "eng_to_ipa", "pyqtgraph"):
    pkg_datas, pkg_binaries, pkg_hidden = collect_all(package)
    datas += pkg_datas
    binaries += pkg_binaries
    hiddenimports += pkg_hidden

a = Analysis(
    ["scripts/launcher.py"],
    pathex=["src"],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    excludes=[
        "torch", "torchaudio", "torchvision", "transformers", "g2p_en", "nltk",
        "tkinter", "matplotlib", "IPython", "jupyter", "pandas", "scipy",
        "numba", "cupy", "tensorflow", "PyQt5", "PyQt6",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name="PronunciationCoach",
    debug=False,
    strip=False,
    upx=False,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="PronunciationCoach",
)
