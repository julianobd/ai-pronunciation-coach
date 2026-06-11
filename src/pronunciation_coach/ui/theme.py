"""Dark theme colors, global stylesheet and small style helpers."""

ACCENT = "#3b82f6"
ACCENT_HOVER = "#2563eb"
ACCENT_PRESSED = "#1d4ed8"
DANGER = "#dc2626"
DANGER_HOVER = "#b91c1c"
GOOD = "#22c55e"
FAIR = "#f59e0b"
POOR = "#ef4444"
MUTED = "#9ca3af"

BG = "#111827"            # window background
SIDEBAR_BG = "#0d1424"    # slightly darker than the window for depth
SURFACE = "#1f2937"       # cards, inputs
SURFACE_HOVER = "#273548"
SURFACE_PRESSED = "#18222f"
BORDER = "#374151"
BORDER_HOVER = "#4b5563"
TEXT = "#e5e7eb"
TEXT_BRIGHT = "#f9fafb"

CATEGORY_COLORS = {0: GOOD, 1: FAIR, 2: POOR}


def color_for_category(category: int) -> str:
    return CATEGORY_COLORS.get(category, MUTED)


def color_for_accuracy(accuracy: float) -> str:
    if accuracy >= 80:
        return GOOD
    if accuracy >= 60:
        return FAIR
    return POOR


CARD_STYLE = f"""
QFrame#card {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 10px;
}}
"""


# Application-wide stylesheet. Buttons come in three flavors:
#   - default (no property): secondary surface button
#   - variant="primary":     accent call-to-action; :checked turns red (record)
#   - variant="tonal":       subtle accent-tinted companion button
GLOBAL_STYLE = f"""
QWidget {{
    font-family: "Segoe UI";
    font-size: 14px;
}}

QPushButton {{
    background: {SURFACE};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 8px 18px;
    font-weight: 600;
}}
QPushButton:hover {{
    background: {SURFACE_HOVER};
    border-color: {BORDER_HOVER};
}}
QPushButton:pressed {{
    background: {SURFACE_PRESSED};
}}
QPushButton:disabled {{
    color: #6b7280;
    background: #1a2230;
    border-color: #2a3344;
}}

QPushButton[variant="primary"] {{
    background: {ACCENT};
    color: white;
    border: none;
}}
QPushButton[variant="primary"]:hover {{
    background: {ACCENT_HOVER};
}}
QPushButton[variant="primary"]:pressed {{
    background: {ACCENT_PRESSED};
}}
QPushButton[variant="primary"]:checked {{
    background: {DANGER};
}}
QPushButton[variant="primary"]:checked:hover {{
    background: {DANGER_HOVER};
}}
QPushButton[variant="primary"]:disabled {{
    background: #1e3a5f;
    color: #8da4c4;
}}

QPushButton[variant="tonal"] {{
    background: rgba(59, 130, 246, 0.15);
    color: #93c5fd;
    border: 1px solid rgba(59, 130, 246, 0.45);
}}
QPushButton[variant="tonal"]:hover {{
    background: rgba(59, 130, 246, 0.28);
}}
QPushButton[variant="tonal"]:pressed {{
    background: rgba(59, 130, 246, 0.10);
}}
QPushButton[variant="tonal"]:disabled {{
    background: rgba(59, 130, 246, 0.06);
    color: #4d6486;
    border-color: rgba(59, 130, 246, 0.18);
}}

QComboBox {{
    background: {SURFACE};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 7px 32px 7px 12px;
}}
QComboBox:hover {{
    border-color: {BORDER_HOVER};
}}
QComboBox:focus {{
    border-color: {ACCENT};
}}
QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: center right;
    width: 28px;
    border: none;
}}
QComboBox::down-arrow {{
    width: 0;
    height: 0;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {MUTED};
    margin-right: 10px;
}}
QComboBox QAbstractItemView {{
    background: {SURFACE};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 4px;
    outline: none;
    selection-background-color: {ACCENT};
    selection-color: white;
}}

QLineEdit {{
    background: {SURFACE};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 7px 12px;
    selection-background-color: {ACCENT};
}}
QLineEdit:hover {{
    border-color: {BORDER_HOVER};
}}
QLineEdit:focus {{
    border-color: {ACCENT};
}}

QProgressBar {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 5px;
}}
QProgressBar::chunk {{
    background: {GOOD};
    border-radius: 4px;
}}

QTableWidget {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 8px;
    gridline-color: {BORDER};
}}
QTableWidget::item {{
    padding: 4px 8px;
}}
QTableWidget::item:selected {{
    background: {ACCENT};
    color: white;
}}
QHeaderView::section {{
    background: {BG};
    color: {MUTED};
    border: none;
    border-bottom: 1px solid {BORDER};
    padding: 8px 10px;
    font-weight: 600;
}}
QTableCornerButton::section {{
    background: {BG};
    border: none;
}}

QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    margin: 2px;
}}
QScrollBar::handle:vertical {{
    background: {BORDER};
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {BORDER_HOVER};
}}
QScrollBar:horizontal {{
    background: transparent;
    height: 10px;
    margin: 2px;
}}
QScrollBar::handle:horizontal {{
    background: {BORDER};
    border-radius: 4px;
    min-width: 30px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {BORDER_HOVER};
}}
QScrollBar::add-line, QScrollBar::sub-line {{
    width: 0;
    height: 0;
}}
QScrollBar::add-page, QScrollBar::sub-page {{
    background: transparent;
}}

QToolTip {{
    background: {SURFACE};
    color: {TEXT};
    border: 1px solid {BORDER};
    padding: 4px 8px;
}}

QStatusBar {{
    color: {MUTED};
}}
"""


SIDEBAR_STYLE = f"""
QListWidget {{
    background: {SIDEBAR_BG};
    color: {TEXT};
    border: none;
    font-size: 15px;
    padding: 8px 6px;
    outline: none;
}}
QListWidget::item {{
    padding: 12px 14px;
    border-radius: 8px;
    margin: 2px 4px;
}}
QListWidget::item:hover {{
    background: {SURFACE};
}}
QListWidget::item:selected {{
    background: {ACCENT};
    color: white;
}}
"""
