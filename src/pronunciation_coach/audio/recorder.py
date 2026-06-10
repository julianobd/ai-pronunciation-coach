"""Microphone recording via sounddevice (PortAudio), 16 kHz mono float32."""

from __future__ import annotations

import numpy as np
import sounddevice as sd
from PySide6.QtCore import QObject, Signal

SAMPLE_RATE = 16000


class AudioRecorder(QObject):
    level_changed = Signal(float)  # RMS 0..1, for the input level meter
    error = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._stream: sd.InputStream | None = None
        self._chunks: list[np.ndarray] = []

    @staticmethod
    def list_input_devices() -> list[tuple[int, str]]:
        devices = []
        for idx, dev in enumerate(sd.query_devices()):
            if dev.get("max_input_channels", 0) > 0:
                devices.append((idx, dev["name"]))
        return devices

    @property
    def is_recording(self) -> bool:
        return self._stream is not None

    def start(self, device: int | None = None) -> None:
        if self._stream is not None:
            return
        self._chunks = []

        def callback(indata, _frames, _time, status):
            if status:
                pass  # over/underflows are non-fatal; keep recording
            mono = indata[:, 0].copy()
            self._chunks.append(mono)
            self.level_changed.emit(float(np.sqrt(np.mean(mono**2))))

        try:
            self._stream = sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype="float32",
                device=device if device is not None and device >= 0 else None,
                callback=callback,
            )
            self._stream.start()
        except Exception as exc:  # device missing, permission denied, ...
            self._stream = None
            self.error.emit(
                f"Could not open the microphone: {exc}\n\n"
                "Check Windows Settings > Privacy & security > Microphone, and "
                "make sure desktop apps are allowed to access it."
            )

    def stop(self) -> np.ndarray:
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        self.level_changed.emit(0.0)
        if not self._chunks:
            return np.zeros(0, dtype=np.float32)
        return np.concatenate(self._chunks)
