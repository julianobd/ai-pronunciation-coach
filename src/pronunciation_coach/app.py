"""Application bootstrap and dependency wiring."""

from __future__ import annotations

import sys

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

from .config import AppConfig
from .core.analysis import PronunciationAnalyzer
from .paths import db_path
from .persistence.db import Database
from .persistence.repository import (
    AttemptRepo,
    ExerciseCacheRepo,
    PhonemeStatsRepo,
    SettingsRepo,
)
from .providers.factory import create_provider
from .services.interview_service import InterviewService
from .services.learning_engine import LearningEngine
from .services.practice_service import PracticeService
from .services.progress_service import ProgressService
from .services.shadowing_service import ShadowingService
from .services.workers import run_in_background, wait_for_workers
from .speech.asr import FasterWhisperASR
from .speech.tts import create_tts
from .ui import theme
from .ui.main_window import MainWindow
from .ui.pages.home_page import HomePage
from .ui.pages.interview_page import InterviewPage
from .ui.pages.practice_page import PracticePage
from .ui.pages.progress_page import ProgressPage
from .ui.pages.settings_page import SettingsPage
from .ui.pages.shadowing_page import ShadowingPage


def _dark_palette() -> QPalette:
    """Explicit dark palette so custom widget colors are predictable
    regardless of the Windows light/dark setting."""
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#111827"))
    palette.setColor(QPalette.WindowText, QColor("#e5e7eb"))
    palette.setColor(QPalette.Base, QColor("#1f2937"))
    palette.setColor(QPalette.AlternateBase, QColor("#374151"))
    palette.setColor(QPalette.ToolTipBase, QColor("#1f2937"))
    palette.setColor(QPalette.ToolTipText, QColor("#e5e7eb"))
    palette.setColor(QPalette.Text, QColor("#e5e7eb"))
    palette.setColor(QPalette.Button, QColor("#1f2937"))
    palette.setColor(QPalette.ButtonText, QColor("#e5e7eb"))
    palette.setColor(QPalette.BrightText, QColor("#ffffff"))
    palette.setColor(QPalette.Link, QColor("#60a5fa"))
    palette.setColor(QPalette.Highlight, QColor("#3b82f6"))
    palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    palette.setColor(QPalette.PlaceholderText, QColor("#6b7280"))
    for role in (QPalette.Text, QPalette.ButtonText, QPalette.WindowText):
        palette.setColor(QPalette.Disabled, role, QColor("#6b7280"))
    return palette


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("AI Pronunciation Coach")
    app.setStyle("Fusion")
    app.setPalette(_dark_palette())
    app.setStyleSheet(theme.GLOBAL_STYLE)

    # --- persistence -------------------------------------------------------
    db = Database(db_path())
    settings_repo = SettingsRepo(db)
    attempts = AttemptRepo(db)
    stats = PhonemeStatsRepo(db)
    cache = ExerciseCacheRepo(db)
    config = AppConfig.from_settings(settings_repo.get_all())

    # --- engines -----------------------------------------------------------
    asr = FasterWhisperASR(config.asr_model_size)
    analyzer = PronunciationAnalyzer(asr)
    tts = create_tts(config.tts_engine)
    provider = create_provider(config)

    learning = LearningEngine(stats, cache, provider)
    practice_service = PracticeService(analyzer, attempts, stats)
    shadowing_service = ShadowingService(analyzer, tts, attempts)
    interview_service = InterviewService(asr, provider, attempts)
    progress = ProgressService(attempts, stats)

    # --- UI ------------------------------------------------------------------
    home = HomePage(progress)
    practice = PracticePage(practice_service, learning)
    shadowing = ShadowingPage(shadowing_service)
    interview = InterviewPage(interview_service)
    progress_page = ProgressPage(progress)
    settings_page = SettingsPage(config)

    window = MainWindow([
        ("🏠  Home", home),
        ("🎯  Practice", practice),
        ("🎧  Shadowing", shadowing),
        ("💼  Interview", interview),
        ("📈  Progress", progress_page),
        ("⚙️  Settings", settings_page),
    ])

    home.practice_requested.connect(lambda: window.navigate_to("🎯  Practice"))

    def practice_phoneme(key: str) -> None:
        window.navigate_to("🎯  Practice")
        practice.set_target_phoneme(key)

    home.phoneme_practice_requested.connect(practice_phoneme)

    def on_settings_saved(new_config: AppConfig) -> None:
        settings_repo.set_many(new_config.to_settings())
        new_provider = create_provider(new_config)
        learning.set_provider(new_provider)
        interview_service.set_provider(new_provider)
        practice.record.set_device(new_config.mic_device)
        shadowing.record.set_device(new_config.mic_device)
        interview.record.set_device(new_config.mic_device)

    settings_page.settings_saved.connect(on_settings_saved)
    practice.record.set_device(config.mic_device)
    shadowing.record.set_device(config.mic_device)
    interview.record.set_device(config.mic_device)

    # Warm up the ASR model in the background (first run downloads it).
    window.statusBar().showMessage("Loading speech recognition model…")
    run_in_background(
        asr.load,
        on_result=lambda _none: window.statusBar().showMessage("Ready", 5000),
        on_error=lambda err: window.statusBar().showMessage(
            "Speech model failed to load — check your internet connection and restart.", 0
        ),
    )

    app.aboutToQuit.connect(wait_for_workers)

    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
