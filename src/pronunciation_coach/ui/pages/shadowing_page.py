"""Shadowing page: listen to a native sentence, repeat it, compare."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ...audio.player import AudioPlayer
from ...core.shadowing_metrics import ShadowingResult
from ...services.shadowing_service import ShadowingExercise, ShadowingService
from .. import theme
from ..widgets.record_button import RecordWidget
from ..widgets.word_feedback import WordFeedbackWidget


class MetricCard(QFrame):
    def __init__(self, title: str, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("card")
        self.setStyleSheet(theme.CARD_STYLE)
        self.value_label = QLabel("—")
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setStyleSheet("font-size: 26px; font-weight: 700;")
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #6b7280;")
        layout = QVBoxLayout(self)
        layout.addWidget(self.value_label)
        layout.addWidget(title_label)

    def set_value(self, value: float) -> None:
        self.value_label.setText(f"{value:.0f}")
        self.value_label.setStyleSheet(
            f"font-size: 26px; font-weight: 700; color: {theme.color_for_accuracy(value)};"
        )


class ShadowingPage(QWidget):
    def __init__(self, service: ShadowingService, parent=None) -> None:
        super().__init__(parent)
        self.service = service
        self.player = AudioPlayer()
        self.last_user_audio = None

        self.difficulty = QComboBox()
        self.difficulty.addItems(["easy", "medium", "hard"])
        self.new_button = QPushButton("New sentence")
        self.new_button.clicked.connect(self._new_sentence)

        header = QHBoxLayout()
        header.addWidget(QLabel("Difficulty:"))
        header.addWidget(self.difficulty)
        header.addWidget(self.new_button)
        header.addStretch(1)

        self.sentence_label = QLabel("Click 'New sentence' to start shadowing.")
        self.sentence_label.setWordWrap(True)
        self.sentence_label.setAlignment(Qt.AlignCenter)
        self.sentence_label.setStyleSheet("font-size: 22px; font-weight: 600; padding: 14px;")

        self.listen_button = QPushButton("▶  Listen")
        self.listen_button.clicked.connect(self._play_reference)
        self.listen_button.setEnabled(False)
        self.play_mine_button = QPushButton("▶  My recording")
        self.play_mine_button.clicked.connect(self._play_mine)
        self.play_mine_button.setEnabled(False)

        self.record = RecordWidget()
        self.record.recording_finished.connect(self._on_recording)

        controls = QHBoxLayout()
        controls.addWidget(self.listen_button)
        controls.addWidget(self.record, stretch=1)
        controls.addWidget(self.play_mine_button)

        self.cards = {
            "score": MetricCard("Score"),
            "pronunciation": MetricCard("Pronunciation"),
            "timing": MetricCard("Timing"),
            "fluency": MetricCard("Fluency"),
        }
        grid = QGridLayout()
        for column, card in enumerate(self.cards.values()):
            grid.addWidget(card, 0, column)

        self.pauses_label = QLabel("")
        self.pauses_label.setStyleSheet("color: #6b7280;")
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #6b7280;")

        self.feedback = WordFeedbackWidget()

        self.service.exercise_ready.connect(self._on_exercise)
        self.service.result_ready.connect(self._on_result)
        self.service.failed.connect(self._on_error)

        layout = QVBoxLayout(self)
        layout.addLayout(header)
        layout.addWidget(self.sentence_label)
        layout.addLayout(controls)
        layout.addWidget(self.status_label)
        layout.addLayout(grid)
        layout.addWidget(self.pauses_label)
        layout.addWidget(self.feedback, stretch=1)

    def _new_sentence(self) -> None:
        self.new_button.setEnabled(False)
        self.listen_button.setEnabled(False)
        self.status_label.setText("Generating sentence audio… (first run may download the voice model)")
        self.service.new_exercise(self.difficulty.currentText())

    def _on_exercise(self, exercise: ShadowingExercise) -> None:
        self.new_button.setEnabled(True)
        self.listen_button.setEnabled(True)
        self.sentence_label.setText(exercise.text)
        self.status_label.setText("Listen first, then record yourself repeating it.")
        self.feedback.clear()
        self.pauses_label.clear()
        for card in self.cards.values():
            card.value_label.setText("—")

    def _play_reference(self) -> None:
        if self.service.current is not None:
            self.player.play(self.service.current.audio, self.service.current.sample_rate)

    def _play_mine(self) -> None:
        if self.last_user_audio is not None:
            self.player.play(self.last_user_audio, 16000)

    def _on_recording(self, audio) -> None:
        self.last_user_audio = audio
        self.play_mine_button.setEnabled(True)
        self.status_label.setText("Scoring…")
        self.service.submit_recording(audio)

    def _on_result(self, analysis, result: ShadowingResult) -> None:
        self.status_label.setText("")
        self.cards["score"].set_value(result.score)
        self.cards["pronunciation"].set_value(result.pronunciation)
        self.cards["timing"].set_value(result.timing)
        self.cards["fluency"].set_value(result.fluency)
        if result.pauses:
            pauses = ", ".join(f"{duration:.1f}s at {start:.1f}s" for start, duration in result.pauses)
            self.pauses_label.setText(
                f"Pauses: {pauses}   ·   your pace {result.speech_rate_wps:.1f} w/s, "
                f"reference {result.reference_rate_wps:.1f} w/s"
            )
        else:
            self.pauses_label.setText(
                f"No long pauses 👍   ·   your pace {result.speech_rate_wps:.1f} w/s, "
                f"reference {result.reference_rate_wps:.1f} w/s"
            )
        self.feedback.show_analysis(analysis)

    def _on_error(self, message: str) -> None:
        self.new_button.setEnabled(True)
        self.status_label.setText(f"Error: {message.splitlines()[-1] if message else 'unknown'}")
