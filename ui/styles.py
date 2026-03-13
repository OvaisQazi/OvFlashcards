# ── Palette ───────────────────────────────────────────────────────────────────
BG          = "#1A1612"   # dark walnut background
BG_CARD     = "#231E1A"   # slightly lighter for cards/panels
ACCENT      = "#C4956A"   # warm amber-gold
ACCENT_HOVER= "#D4A574"
TEXT_PRIMARY= "#F5ECD7"   # warm off-white
TEXT_SECONDARY = "#9E8E7E"
BORDER      = "#3D3228"

# ── 15 card colour options ────────────────────────────────────────────────────
CARD_COLORS = [
    ("#FEFEFE", "Snow White"),
    ("#FFF8E7", "Cream"),
    ("#FFF9C4", "Lemon"),
    ("#FFE0B2", "Peach"),
    ("#FFCCBC", "Apricot"),
    ("#F8BBD9", "Blush"),
    ("#E1BEE7", "Lavender"),
    ("#C5CAE9", "Periwinkle"),
    ("#B3E5FC", "Sky Blue"),
    ("#B2EBF2", "Aqua"),
    ("#C8E6C9", "Mint"),
    ("#DCEDC8", "Sage"),
    ("#FFE082", "Amber"),
    ("#FFAB91", "Coral"),
    ("#CFD8DC", "Slate"),
]

# ── Global stylesheet ─────────────────────────────────────────────────────────
APP_STYLE = f"""
QMainWindow, QDialog {{
    background-color: {BG};
}}
QWidget {{
    background-color: {BG};
    color: {TEXT_PRIMARY};
    font-family: 'Helvetica Neue', 'SF Pro Text', Arial, sans-serif;
}}
QScrollArea {{
    border: none;
    background-color: {BG};
}}
QScrollBar:vertical {{
    background: {BG};
    width: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {BORDER};
    border-radius: 4px;
    min-height: 20px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
QScrollBar:horizontal {{
    background: {BG};
    height: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:horizontal {{
    background: {BORDER};
    border-radius: 4px;
    min-width: 20px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0px; }}
QLineEdit {{
    background-color: {BG_CARD};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 14px;
}}
QLineEdit:focus {{ border-color: {ACCENT}; }}
QTextEdit {{
    background-color: {BG_CARD};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 14px;
}}
QTextEdit:focus {{ border-color: {ACCENT}; }}
QListWidget {{
    background-color: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: 10px;
    padding: 4px;
    outline: none;
}}
QListWidget::item {{
    padding: 12px 14px;
    border-radius: 6px;
    color: {TEXT_PRIMARY};
}}
QListWidget::item:selected {{
    background-color: {ACCENT};
    color: #1A1612;
}}
QListWidget::item:hover:!selected {{
    background-color: {BG};
}}
QMessageBox {{
    background-color: {BG_CARD};
}}
QInputDialog {{
    background-color: {BG_CARD};
}}
"""

# ── Button styles ─────────────────────────────────────────────────────────────
BTN_PRIMARY = f"""
QPushButton {{
    background-color: {ACCENT};
    color: #1A1612;
    border: none;
    border-radius: 10px;
    padding: 12px 28px;
    font-size: 15px;
    font-weight: bold;
    min-width: 140px;
}}
QPushButton:hover {{ background-color: {ACCENT_HOVER}; }}
QPushButton:pressed {{ background-color: #A87850; }}
"""

BTN_SECONDARY = f"""
QPushButton {{
    background-color: transparent;
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 10px;
    padding: 12px 28px;
    font-size: 15px;
    min-width: 140px;
}}
QPushButton:hover {{
    background-color: {BG_CARD};
    border-color: {ACCENT};
}}
QPushButton:pressed {{ background-color: {BG}; }}
"""

BTN_DANGER = f"""
QPushButton {{
    background-color: transparent;
    color: #E57373;
    border: 1px solid #6B3333;
    border-radius: 10px;
    padding: 12px 28px;
    font-size: 15px;
    min-width: 100px;
}}
QPushButton:hover {{
    background-color: #3D2020;
    border-color: #E57373;
}}
"""

BTN_GHOST = f"""
QPushButton {{
    background-color: transparent;
    color: {TEXT_SECONDARY};
    border: none;
    padding: 8px 4px;
    font-size: 13px;
    text-align: left;
}}
QPushButton:hover {{ color: {TEXT_PRIMARY}; }}
"""