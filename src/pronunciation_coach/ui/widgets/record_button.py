"""Record toggle button with a live input level meter."""

from __future__ import annotations

import numpy as np
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QWidget,
)

from ...audio.recorder import AudioRecorder


class RecordWidget(QWidget):
    recording_finished = Signal(object)  # np.ndarray float32 @16kHz

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.recorder = AudioRecorder(self)
        self.recorder.level_changed.connect(self._on_level)
        self.recorder.error.connect(self._on_error)

        self.button = QPushButton("🎙️  Record")
        self.button.setCheckable(True)
        self.button.setMinimumHeight(44)
        self.button.setStyleSheet(
            "QPushButton { font-size: 15px; border-radius: 8px; padding: 6px 18px;"
            " background: #3b82f6; color: white; }"
            "QPushButton:checked { background: #dc2626; }"
        )
        self.button.toggled.connect(self._on_toggle)

        self.level = QProgressBar()
        self.level.setRange(0, 100)
        self.level.setTextVisible(False)
        self.level.setFixedHeight(10)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.button)
        layout.addWidget(self.level, stretch=1)

    def set_device(self, device: int | None) -> None:
        self._device = device

    def _on_toggle(self, checked: bool) -> None:
        if checked:
            self.button.setText("⏹  Stop")
            self.recorder.start(getattr(self, "_device", None))
        else:
            self.button.setText("🎙️  Record")
            audio = self.recorder.stop()
            if audio.size > 0:
                self.recording_finished.emit(audio)

    def _on_level(self, rms: float) -> None:
        self.level.setValue(int(min(1.0, rms * 8) * 100))

    def _on_error(self, message: str) -> None:
        self.button.setChecked(False)
        QMessageBox.warning(self, "Microphone", message)

    def set_enabled_recording(self, enabled: bool) -> None:
        self.button.setEnabled(enabled)
