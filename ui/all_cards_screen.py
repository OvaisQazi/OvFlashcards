from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QGridLayout, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import database
from ui.styles import *


# ── Mini card widget ───────────────────────────────────────────────────────────

class MiniCard(QFrame):
    """A small, clickable card thumbnail showing only the front (word)."""

    def __init__(self, card: dict, on_click, parent=None):
        super().__init__(parent)
        self.card = card
        self._on_click = on_click
        self.setFixedSize(210, 145)
        self.setCursor(Qt.PointingHandCursor)

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {card['color']};
                border-radius: 12px;
                border: 1px solid rgba(0,0,0,0.10);
            }}
            QFrame:hover {{
                border: 2px solid {ACCENT};
            }}
        """)

        inner = QVBoxLayout(self)
        inner.setContentsMargins(12, 12, 12, 12)
        inner.setAlignment(Qt.AlignCenter)

        word = QLabel(card["word"])
        word.setAlignment(Qt.AlignCenter)
        word.setFont(QFont("Georgia", 15, QFont.Bold))
        word.setWordWrap(True)
        word.setStyleSheet(
            "color: #1A1A1A; background: transparent; border: none;"
        )
        inner.addWidget(word)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._on_click(self.card)


# ── Screen ─────────────────────────────────────────────────────────────────────

class AllCardsScreen(QWidget):
    """
    Shows every card in the deck as a small coloured thumbnail.
    Cards are arranged in a scrollable grid, like physical cards on a table.
    """

    def __init__(self, app_window, language: str):
        super().__init__()
        self.app = app_window
        self.language = language
        self._build_ui()

    def _build_ui(self):
        # Clear old layout on rebuild
        if self.layout():
            while self.layout().count():
                item = self.layout().takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            QWidget().setLayout(self.layout())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(50, 50, 50, 40)
        layout.setSpacing(0)

        # ── Header ─────────────────────────────────────────────────────────────
        top = QHBoxLayout()
        back_btn = QPushButton("← Back")
        back_btn.setStyleSheet(BTN_GHOST)
        back_btn.clicked.connect(self.app.go_back)
        top.addWidget(back_btn)
        top.addStretch()
        layout.addLayout(top)
        layout.addSpacing(16)

        title = QLabel(f"All Cards — {self.language}")
        title.setFont(QFont("Georgia", 30, QFont.Bold))
        title.setStyleSheet(f"color: {TEXT_PRIMARY};")
        layout.addWidget(title)
        layout.addSpacing(24)

        # ── Scrollable card grid ───────────────────────────────────────────────
        color_order = {hex_: i for i, (hex_, _) in enumerate(CARD_COLORS)}
        cards = sorted(
            database.get_all_cards(self.language),
            key=lambda c: color_order.get(c["color"], 999)
        )

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        container = QWidget()
        grid = QGridLayout(container)
        grid.setSpacing(18)
        grid.setContentsMargins(4, 4, 4, 16)
        grid.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        COLS = 4
        for i, card in enumerate(cards):
            mini = MiniCard(card, self._open_card)
            grid.addWidget(mini, i // COLS, i % COLS)

        scroll.setWidget(container)
        layout.addWidget(scroll)

    def on_resume(self):
        """Rebuild grid after returning from card view (edit/delete)."""
        self._build_ui()

    def _open_card(self, card: dict):
        from ui.card_view_screen import CardViewScreen
        self.app.navigate_to(CardViewScreen(self.app, self.language, card))