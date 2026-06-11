"""Progress page: accuracy/minutes charts and per-phoneme history."""

from __future__ import annotations

from datetime import date

import pyqtgraph as pg
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ...core import phoneme_kb
from ...services.progress_service import ProgressService

pg.setConfigOptions(antialias=True, background="#1f2937", foreground="#9ca3af")


def _days_to_x(days: list[str]) -> list[float]:
    return [date.fromisoformat(d).toordinal() for d in days]


class DateAxis(pg.AxisItem):
    def tickStrings(self, values, scale, spacing):
        labels = []
        for value in values:
            try:
                labels.append(date.fromordinal(int(value)).strftime("%d %b"))
            except (ValueError, OverflowError):
                labels.append("")
        return labels


class ProgressPage(QWidget):
    def __init__(self, progress: ProgressService, parent=None) -> None:
        super().__init__(parent)
        self.progress = progress

        self.accuracy_plot = pg.PlotWidget(
            title="Overall accuracy", axisItems={"bottom": DateAxis(orientation="bottom")}
        )
        self.accuracy_plot.setYRange(0, 100)
        self.minutes_plot = pg.PlotWidget(
            title="Practice minutes per day",
            axisItems={"bottom": DateAxis(orientation="bottom")},
        )

        self.phoneme_combo = QComboBox()
        self.phoneme_plot = pg.PlotWidget(
            title="Phoneme accuracy over time",
            axisItems={"bottom": DateAxis(orientation="bottom")},
        )
        self.phoneme_plot.setYRange(0, 100)
        self.phoneme_combo.currentIndexChanged.connect(self._refresh_phoneme_plot)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Phoneme", "Accuracy", "Attempts", "Trend"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        charts_row = QHBoxLayout()
        charts_row.addWidget(self.accuracy_plot)
        charts_row.addWidget(self.minutes_plot)

        phoneme_row = QHBoxLayout()
        phoneme_row.addWidget(QLabel("Phoneme:"))
        phoneme_row.addWidget(self.phoneme_combo)
        phoneme_row.addStretch(1)

        layout = QVBoxLayout(self)
        layout.addLayout(charts_row, stretch=2)
        layout.addLayout(phoneme_row)
        layout.addWidget(self.phoneme_plot, stretch=2)
        layout.addWidget(self.table, stretch=2)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.refresh()

    def refresh(self) -> None:
        accuracy = self.progress.accuracy_history()
        self.accuracy_plot.clear()
        if accuracy:
            days, values = zip(*accuracy)
            self.accuracy_plot.plot(
                _days_to_x(list(days)), list(values),
                pen=pg.mkPen("#3b82f6", width=2), symbol="o", symbolBrush="#3b82f6",
            )

        minutes = self.progress.minutes_history()
        self.minutes_plot.clear()
        if minutes:
            days, values = zip(*minutes)
            bars = pg.BarGraphItem(
                x=_days_to_x(list(days)), height=list(values), width=0.7, brush="#10b981"
            )
            self.minutes_plot.addItem(bars)

        stats = self.progress.all_phoneme_stats()
        current_key = self.phoneme_combo.currentData()
        self.phoneme_combo.blockSignals(True)
        self.phoneme_combo.clear()
        for stat in stats:
            self.phoneme_combo.addItem(
                phoneme_kb.display_for_key(stat.phoneme_key), stat.phoneme_key
            )
        if current_key:
            index = self.phoneme_combo.findData(current_key)
            if index >= 0:
                self.phoneme_combo.setCurrentIndex(index)
        self.phoneme_combo.blockSignals(False)
        self._refresh_phoneme_plot()

        self.table.setRowCount(len(stats))
        for row, stat in enumerate(stats):
            history = self.progress.phoneme_history(stat.phoneme_key)
            trend = "→"
            if len(history) >= 2:
                delta = history[-1][1] - history[0][1]
                trend = "↑" if delta > 2 else ("↓" if delta < -2 else "→")
            self.table.setItem(row, 0, QTableWidgetItem(phoneme_kb.display_for_key(stat.phoneme_key)))
            self.table.setItem(row, 1, QTableWidgetItem(f"{stat.accuracy:.0f}%"))
            self.table.setItem(row, 2, QTableWidgetItem(f"{stat.attempts:.0f}"))
            self.table.setItem(row, 3, QTableWidgetItem(trend))

    def _refresh_phoneme_plot(self) -> None:
        self.phoneme_plot.clear()
        key = self.phoneme_combo.currentData()
        if not key:
            return
        history = self.progress.phoneme_history(key)
        if history:
            days, values = zip(*history)
            self.phoneme_plot.plot(
                _days_to_x(list(days)), list(values),
                pen=pg.mkPen("#8b5cf6", width=2), symbol="o", symbolBrush="#8b5cf6",
            )
