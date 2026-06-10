"""Home dashboard: streak, today's summary, weak phonemes."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ...services.progress_service import ProgressService
from .. import theme
from ..widgets.phoneme_chip import PhonemeChip


def _card(title: str) -> tuple[QFrame, QLabel]:
    frame = QFrame()
    frame.setObjectName("card")
    frame.setStyleSheet(theme.CARD_STYLE)
    value = QLabel("—")
    value.setAlignment(Qt.AlignCenter)
    value.setStyleSheet(f"font-size: 30px; font-weight: 700; color: {theme.TEXT_BRIGHT};")
    caption = QLabel(title)
    caption.setAlignment(Qt.AlignCenter)
    caption.setStyleSheet(f"color: {theme.MUTED};")
    layout = QVBoxLayout(frame)
    layout.addWidget(value)
    layout.addWidget(caption)
    return frame, value


class HomePage(QWidget):
    practice_requested = Signal()
    phoneme_practice_requested = Signal(str)

    def __init__(self, progress: ProgressService, parent=None) -> None:
        super().__init__(parent)
        self.progress = progress

        title = QLabel("AI Pronunciation Coach")
        title.setStyleSheet(f"font-size: 26px; font-weight: 700; color: {theme.TEXT_BRIGHT};")

        streak_card, self.streak_value = _card("day streak 🔥")
        minutes_card, self.minutes_value = _card("minutes today")
        attempts_card, self.attempts_value = _card("attempts today")
        accuracy_card, self.accuracy_value = _card("accuracy today")

        cards = QHBoxLayout()
        for card in (streak_card, minutes_card, attempts_card, accuracy_card):
            cards.addWidget(card)

        weak_title = QLabel("Sounds to work on (click to practice):")
        weak_title.setStyleSheet("font-weight: 600; margin-top: 10px;")
        self.chips_row = QHBoxLayout()
        self.chips_row.addStretch(1)
        self.chips_container = QWidget()
        self.chips_container.setLayout(self.chips_row)

        start_button = QPushButton("Start practicing →")
        start_button.setMinimumHeight(46)
        start_button.setStyleSheet(
            "QPushButton { font-size: 16px; background: #3b82f6; color: white;"
            " border-radius: 10px; padding: 8px 20px; }"
        )
        start_button.clicked.connect(self.practice_requested.emit)

        layout = QVBoxLayout(self)
        layout.addWidget(title)
        layout.addLayout(cards)
        layout.addWidget(weak_title)
        layout.addWidget(self.chips_container)
        layout.addStretch(1)
        layout.addWidget(start_button)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.refresh()

    def refresh(self) -> None:
        self.streak_value.setText(str(self.progress.current_streak()))
        today = self.progress.today_summary()
        self.minutes_value.setText(f"{today['minutes']:.0f}")
        self.attempts_value.setText(str(today["attempts"]))
        self.accuracy_value.setText(
            f"{today['accuracy']:.0f}%" if today["attempts"] else "—"
        )

        while self.chips_row.count() > 1:
            item = self.chips_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        weak = self.progress.weak_phonemes()
        if not weak:
            placeholder = QLabel("Practice a few sentences and your weak sounds will show up here.")
            placeholder.setStyleSheet(f"color: {theme.MUTED};")
            self.chips_row.insertWidget(0, placeholder)
        else:
            for position, stat in enumerate(weak):
                chip = PhonemeChip(stat.phoneme_key, stat.accuracy)
                chip.clicked.connect(self.phoneme_practice_requested.emit)
                self.chips_row.insertWidget(position, chip)
