"""Colored per-word feedback with phoneme-level detail and tips."""

from __future__ import annotations

import html

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QTextBrowser, QVBoxLayout, QWidget

from ...core import phoneme_kb, scoring
from ...core.analysis import UtteranceAnalysis
from .. import theme


def words_to_html(analysis: UtteranceAnalysis) -> str:
    parts = []
    for result in analysis.word_results:
        color = theme.color_for_accuracy(result.accuracy)
        parts.append(
            f'<span style="color:{color}; font-size:22px; font-weight:600;">'
            f"{html.escape(result.word)}</span>"
        )
    return " ".join(parts)


def feedback_html(analysis: UtteranceAnalysis, max_tips: int = 3) -> str:
    """Actionable feedback: what was wrong and how to fix it."""
    if analysis.too_quiet:
        return "<p>I couldn't hear anything — try recording again, a bit closer to the microphone.</p>"
    if analysis.low_confidence:
        return ("<p>I couldn't match what you said to the text. "
                "Try reading the sentence again, slowly and clearly.</p>")

    lines: list[str] = []
    seen_keys: set[str] = set()
    for result in analysis.word_results:
        if result.word_missing or result.accuracy >= 80:
            continue
        bad_ops = [op for op in result.ops if op.op == "substitution"]
        if bad_ops and result.detected_ipa:
            lines.append(
                f"<p><b>{html.escape(result.word)}</b>: expected "
                f"/{html.escape(result.expected_ipa)}/, heard /{html.escape(result.detected_ipa)}/.</p>"
            )
        for op in bad_ops:
            key = phoneme_kb.key_for_ipa(op.expected) if op.expected else None
            if not key or key in seen_keys:
                continue
            seen_keys.add(key)
            info = phoneme_kb.get_info(key)
            if info:
                practice = ", ".join(info.example_words[:4])
                lines.append(
                    f"<p style='margin-left:12px;'>💡 <b>{html.escape(info.display)}</b>: "
                    f"{html.escape(info.articulation_tip)}<br/>"
                    f"<i>Practice: {html.escape(practice)}</i></p>"
                )
            if len(seen_keys) >= max_tips:
                break
        if len(seen_keys) >= max_tips:
            break

    if not lines:
        return "<p>✅ Great job — no major pronunciation problems detected!</p>"
    return "\n".join(lines)


class WordFeedbackWidget(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.words_label = QLabel()
        self.words_label.setWordWrap(True)
        self.words_label.setTextFormat(Qt.TextFormat.RichText)

        self.detail = QTextBrowser()
        self.detail.setOpenExternalLinks(False)
        self.detail.setStyleSheet("QTextBrowser { border: none; background: transparent; }")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.words_label)
        layout.addWidget(self.detail, stretch=1)

    def show_analysis(self, analysis: UtteranceAnalysis) -> None:
        self.words_label.setText(words_to_html(analysis))
        score_line = ""
        if not analysis.too_quiet:
            color = theme.color_for_accuracy(analysis.overall_accuracy)
            score_line = (
                f"<p style='font-size:16px;'>Score: <b style='color:{color};'>"
                f"{analysis.overall_accuracy:.0f}%</b>"
                f" &nbsp;|&nbsp; Heard: <i>{html.escape(analysis.transcript or '—')}</i></p>"
            )
        self.detail.setHtml(score_line + feedback_html(analysis))

    def clear(self) -> None:
        self.words_label.clear()
        self.detail.clear()
