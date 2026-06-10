"""Dark theme colors and small style helpers."""

ACCENT = "#3b82f6"
GOOD = "#22c55e"
FAIR = "#f59e0b"
POOR = "#ef4444"
MUTED = "#9ca3af"

BG = "#111827"        # window background
SURFACE = "#1f2937"   # cards, inputs
BORDER = "#374151"
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
