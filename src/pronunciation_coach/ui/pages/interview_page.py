"""Interview simulator: chat-style spoken interview practice."""

from __future__ import annotations

import html

from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from ...services.interview_service import InterviewService
from .. import theme
from ..widgets.record_button import RecordWidget


class InterviewPage(QWidget):
    def __init__(self, service: InterviewService, parent=None) -> None:
        super().__init__(parent)
        self.service = service
        self._log: list[str] = []

        self.role_edit = QLineEdit()
        self.role_edit.setPlaceholderText("Job role, e.g. software developer")
        self.difficulty = QComboBox()
        self.difficulty.addItems(["easy", "medium", "hard"])
        self.start_button = QPushButton("Start interview")
        self.start_button.setProperty("variant", "primary")
        self.start_button.clicked.connect(self._start)

        header = QHBoxLayout()
        header.addWidget(QLabel("Role:"))
        header.addWidget(self.role_edit, stretch=1)
        header.addWidget(QLabel("Difficulty:"))
        header.addWidget(self.difficulty)
        header.addWidget(self.start_button)

        self.chat = QTextBrowser()
        self.chat.setStyleSheet(
            f"QTextBrowser {{ background: #0f172a; border: 1px solid {theme.BORDER};"
            f" border-radius: 10px; padding: 10px; }}"
        )

        self.record = RecordWidget()
        self.record.recording_finished.connect(self._on_recording)
        self.record.setEnabled(False)

        self.status_label = QLabel("Start an interview, then answer each question out loud.")
        self.status_label.setStyleSheet(f"color: {theme.MUTED};")

        self.service.interviewer_says.connect(self._on_question)
        self.service.answer_processed.connect(self._on_answer)
        self.service.failed.connect(self._on_error)

        layout = QVBoxLayout(self)
        layout.addLayout(header)
        layout.addWidget(self.chat, stretch=1)
        layout.addWidget(self.status_label)
        layout.addWidget(self.record)

    def _append(self, html_block: str) -> None:
        self._log.append(html_block)
        self.chat.setHtml("".join(self._log))
        self.chat.verticalScrollBar().setValue(self.chat.verticalScrollBar().maximum())

    def _start(self) -> None:
        self._log = []
        self.chat.clear()
        self.record.setEnabled(False)
        self.status_label.setText("Interviewer is thinking…")
        self.service.start(self.role_edit.text().strip(), self.difficulty.currentText())

    def _on_question(self, text: str, done: bool) -> None:
        self._append(
            f"<p style='background:#1e3a8a; color:#dbeafe; border-radius:8px; padding:8px;"
            f" margin:6px 40px 6px 4px;'>"
            f"<b>Interviewer:</b> {html.escape(text)}</p>"
        )
        if done:
            self.status_label.setText("Interview finished — start a new one any time.")
            self.record.setEnabled(False)
        else:
            self.status_label.setText("Record your answer.")
            self.record.setEnabled(True)

    def _on_recording(self, audio) -> None:
        self.record.setEnabled(False)
        self.status_label.setText("Transcribing your answer…")
        self.service.submit_answer(audio)

    def _on_answer(self, transcript: str, fluency: float) -> None:
        color = theme.color_for_accuracy(fluency)
        badge = (f"<span style='background:{color}; color:white; border-radius:8px;"
                 f" padding:1px 8px; font-size:12px;'>fluency {fluency:.0f}</span>")
        self._append(
            f"<p style='background:#14532d; color:#dcfce7; border-radius:8px; padding:8px;"
            f" margin:6px 4px 6px 40px;'>"
            f"<b>You:</b> {html.escape(transcript or '(nothing heard)')} {badge}</p>"
        )
        self.status_label.setText("Interviewer is thinking…")

    def _on_error(self, message: str) -> None:
        self.status_label.setText(f"Error: {message.splitlines()[-1] if message else 'unknown'}")
        self.record.setEnabled(True)
