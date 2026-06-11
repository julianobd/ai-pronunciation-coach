"""Practice page: targeted exercises with record + phoneme feedback."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ...core import phoneme_kb
from ...providers.base import EXERCISE_TYPE_LABELS, EXERCISE_TYPES, Exercise
from ...services.learning_engine import LearningEngine
from ...services.practice_service import PracticeService
from ...services.workers import run_in_background
from .. import theme
from ..widgets.record_button import RecordWidget
from ..widgets.word_feedback import WordFeedbackWidget


class PracticePage(QWidget):
    def __init__(self, practice_service: PracticeService, engine: LearningEngine,
                 parent=None) -> None:
        super().__init__(parent)
        self.service = practice_service
        self.engine = engine
        self.exercise: Exercise | None = None
        self.item_index = 0
        self.target_keys: list[str] | None = None

        self.type_combo = QComboBox()
        for ex_type in EXERCISE_TYPES:
            self.type_combo.addItem(EXERCISE_TYPE_LABELS[ex_type], ex_type)
        self.type_combo.setCurrentIndex(EXERCISE_TYPES.index("sentence"))
        self.new_button = QPushButton("New exercise")
        self.new_button.setProperty("variant", "primary")
        self.new_button.clicked.connect(self.fetch_exercise)

        header = QHBoxLayout()
        header.addWidget(QLabel("Exercise:"))
        header.addWidget(self.type_combo)
        header.addWidget(self.new_button)
        header.addStretch(1)

        self.title_label = QLabel()
        self.title_label.setStyleSheet(f"color: {theme.MUTED}; font-size: 13px;")

        self.item_label = QLabel("Click 'New exercise' to begin.")
        self.item_label.setWordWrap(True)
        self.item_label.setAlignment(Qt.AlignCenter)
        self.item_label.setStyleSheet("font-size: 24px; font-weight: 600; padding: 18px;")

        self.prev_button = QPushButton("‹ Previous")
        self.next_button = QPushButton("Next ›")
        self.position_label = QLabel("")
        self.position_label.setStyleSheet(f"color: {theme.MUTED}; padding: 0 8px;")
        self.prev_button.clicked.connect(lambda: self._move(-1))
        self.next_button.clicked.connect(lambda: self._move(1))
        nav = QHBoxLayout()
        nav.addStretch(1)
        nav.addWidget(self.prev_button)
        nav.addWidget(self.position_label)
        nav.addWidget(self.next_button)
        nav.addStretch(1)

        self.record = RecordWidget()
        self.record.recording_finished.connect(self._on_recording)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet(f"color: {theme.MUTED};")

        self.feedback = WordFeedbackWidget()
        self.service.analysis_ready.connect(self._on_analysis)
        self.service.analysis_failed.connect(self._on_error)

        layout = QVBoxLayout(self)
        layout.addLayout(header)
        layout.addWidget(self.title_label)
        layout.addWidget(self.item_label)
        layout.addLayout(nav)
        layout.addWidget(self.record)
        layout.addWidget(self.status_label)
        layout.addWidget(self.feedback, stretch=1)

    # ---- exercise handling -------------------------------------------------

    def set_target_phoneme(self, key: str) -> None:
        """Called when the user clicks a weak-phoneme chip on Home."""
        self.target_keys = [key]
        info = phoneme_kb.get_info(key)
        self.status_label.setText(f"Targeting: {info.display if info else key}")
        self.fetch_exercise()

    def fetch_exercise(self) -> None:
        exercise_type = self.type_combo.currentData()
        self.new_button.setEnabled(False)
        self.status_label.setText("Preparing exercise…")
        run_in_background(
            self.engine.next_exercise, exercise_type, self.target_keys,
            on_result=self._show_exercise,
            on_error=self._on_error,
            on_finished=lambda: self.new_button.setEnabled(True),
        )

    def _show_exercise(self, exercise: Exercise) -> None:
        self.exercise = exercise
        self.item_index = 0
        self.title_label.setText(
            f"{exercise.title}   ·   source: {exercise.provider}"
        )
        note = ""
        if self.engine.last_provider_error:
            note = " (LLM provider unavailable — using offline exercises)"
        self.status_label.setText("Read the text aloud, then press Record." + note)
        self.feedback.clear()
        self._update_item()

    def _update_item(self) -> None:
        if not self.exercise or not self.exercise.items:
            return
        total = len(self.exercise.items)
        self.item_index = max(0, min(self.item_index, total - 1))
        self.item_label.setText(self.exercise.items[self.item_index])
        self.position_label.setText(f"{self.item_index + 1} / {total}")
        self.prev_button.setEnabled(self.item_index > 0)
        self.next_button.setEnabled(self.item_index < total - 1)

    def _move(self, delta: int) -> None:
        self.item_index += delta
        self.feedback.clear()
        self._update_item()

    # ---- recording / analysis ----------------------------------------------

    def current_text(self) -> str:
        if not self.exercise or not self.exercise.items:
            return ""
        text = self.exercise.items[self.item_index]
        # Minimal pairs are displayed as "word1 — word2"; read both words.
        return text.replace("—", " ").replace("/", " ")

    def _on_recording(self, audio) -> None:
        text = self.current_text()
        if not text:
            self.status_label.setText("Load an exercise first.")
            return
        self.status_label.setText("Analyzing…")
        self.record.set_enabled_recording(False)
        self.service.submit_recording(audio, text, mode="practice")

    def _on_analysis(self, analysis) -> None:
        self.record.set_enabled_recording(True)
        self.status_label.setText("")
        self.feedback.show_analysis(analysis)

    def _on_error(self, message: str) -> None:
        self.record.set_enabled_recording(True)
        self.new_button.setEnabled(True)
        self.status_label.setText(f"Error: {message.splitlines()[-1] if message else 'unknown'}")
