"""Settings: AI provider, microphone, ASR model, TTS engine."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ...audio.recorder import AudioRecorder
from ...config import PROVIDER_PRESETS, AppConfig
from ...providers.factory import create_provider
from ...services.workers import run_in_background
from .. import theme


class SettingsPage(QWidget):
    settings_saved = Signal(object)  # AppConfig

    def __init__(self, config: AppConfig, parent=None) -> None:
        super().__init__(parent)
        self.config = config

        self.provider = QComboBox()
        self.provider.addItems(list(PROVIDER_PRESETS.keys()))
        self.provider.setCurrentText(config.provider)
        self.provider.currentTextChanged.connect(self._on_provider_changed)

        self.base_url = QLineEdit(config.provider_base_url)
        self.api_key = QLineEdit(config.provider_api_key)
        self.api_key.setEchoMode(QLineEdit.Password)
        self.model = QLineEdit(config.provider_model)
        self.model.setPlaceholderText("empty = use server's loaded model")

        self.test_button = QPushButton("Test connection")
        self.test_button.clicked.connect(self._test_provider)
        self.test_result = QLabel("")

        self.mic = QComboBox()
        self.mic.addItem("System default", -1)
        for index, name in AudioRecorder.list_input_devices():
            self.mic.addItem(name, index)
        position = self.mic.findData(config.mic_device)
        if position >= 0:
            self.mic.setCurrentIndex(position)

        self.asr_size = QComboBox()
        self.asr_size.addItems(["tiny.en", "base.en", "small.en"])
        self.asr_size.setCurrentText(config.asr_model_size)

        self.tts_engine = QComboBox()
        self.tts_engine.addItems(["auto", "omnivoice", "silero", "sapi"])
        self.tts_engine.setCurrentText(config.tts_engine)

        save_button = QPushButton("Save settings")
        save_button.setProperty("variant", "primary")
        save_button.clicked.connect(self._save)
        self.saved_label = QLabel("")
        self.saved_label.setStyleSheet(f"color: {theme.GOOD};")

        form = QFormLayout()
        form.addRow(QLabel("<b>AI exercise provider</b>"))
        form.addRow("Provider:", self.provider)
        form.addRow("Base URL:", self.base_url)
        form.addRow("API key:", self.api_key)
        form.addRow("Model:", self.model)
        form.addRow("", self.test_button)
        form.addRow("", self.test_result)
        form.addRow(QLabel("<b>Audio & models</b>"))
        form.addRow("Microphone:", self.mic)
        form.addRow("Speech recognition:", self.asr_size)
        form.addRow("Text-to-speech:", self.tts_engine)
        form.addRow("", save_button)
        form.addRow("", self.saved_label)

        note = QLabel(
            "LMStudio (default) and Ollama run locally — start the server and a model, "
            "then test the connection. With no provider available the app still works "
            "using built-in offline exercises."
        )
        note.setWordWrap(True)
        note.setStyleSheet(f"color: {theme.MUTED};")

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(note)
        layout.addStretch(1)

    def _on_provider_changed(self, name: str) -> None:
        preset = PROVIDER_PRESETS.get(name)
        if preset:
            self.base_url.setText(preset["base_url"])

    def _current_config(self) -> AppConfig:
        return AppConfig(
            provider=self.provider.currentText(),
            provider_base_url=self.base_url.text().strip(),
            provider_api_key=self.api_key.text().strip(),
            provider_model=self.model.text().strip(),
            mic_device=self.mic.currentData(),
            asr_model_size=self.asr_size.currentText(),
            tts_engine=self.tts_engine.currentText(),
            daily_goal_minutes=self.config.daily_goal_minutes,
        )

    def _test_provider(self) -> None:
        self.test_result.setText("Testing…")
        provider = create_provider(self._current_config())
        run_in_background(
            provider.is_available,
            on_result=lambda ok: self.test_result.setText(
                "✅ Connected" if ok else "❌ Not reachable (is the server running?)"
            ),
            on_error=lambda _err: self.test_result.setText("❌ Test failed"),
        )

    def _save(self) -> None:
        self.config = self._current_config()
        self.saved_label.setText("Saved ✓  (speech model changes apply on restart)")
        self.settings_saved.emit(self.config)
