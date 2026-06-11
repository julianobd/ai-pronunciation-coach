"""Main window: sidebar navigation + stacked pages."""

from __future__ import annotations

from PySide6.QtCore import QSize
from PySide6.QtWidgets import (
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QStackedWidget,
    QWidget,
)

from . import theme


class MainWindow(QMainWindow):
    def __init__(self, pages: list[tuple[str, QWidget]], parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("AI Pronunciation Coach")
        self.resize(1000, 720)

        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(180)
        self.sidebar.setIconSize(QSize(20, 20))
        self.sidebar.setStyleSheet(theme.SIDEBAR_STYLE)

        self.stack = QStackedWidget()
        self._page_names: list[str] = []
        for name, widget in pages:
            QListWidgetItem(name, self.sidebar)
            container = QWidget()
            layout = QHBoxLayout(container)
            layout.setContentsMargins(18, 14, 18, 14)
            layout.addWidget(widget)
            self.stack.addWidget(container)
            self._page_names.append(name)

        self.sidebar.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.sidebar.setCurrentRow(0)

        central = QWidget()
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self.sidebar)
        root.addWidget(self.stack, stretch=1)
        self.setCentralWidget(central)

    def navigate_to(self, name: str) -> None:
        if name in self._page_names:
            self.sidebar.setCurrentRow(self._page_names.index(name))
