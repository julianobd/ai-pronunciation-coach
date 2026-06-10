"""Small clickable pill showing a phoneme and its accuracy: [ th 38% ]."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel

from ...core import phoneme_kb
from .. import theme


class PhonemeChip(QLabel):
    clicked = Signal(str)  # phoneme key

    def __init__(self, phoneme_key: str, accuracy: float, parent=None) -> None:
        super().__init__(parent)
        self.phoneme_key = phoneme_key
        color = theme.color_for_accuracy(accuracy)
        info = phoneme_kb.get_info(phoneme_key)
        label = info.display.split(" (")[0] if info else phoneme_key
        self.setText(f" {label}  {accuracy:.0f}% ")
        self.setToolTip(info.display if info else phoneme_key)
        self.setStyleSheet(
            f"QLabel {{ background: {color}; color: white; border-radius: 12px;"
            f" padding: 4px 10px; font-weight: 600; }}"
        )
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, event) -> None:
        self.clicked.emit(self.phoneme_key)
        super().mousePressEvent(event)
