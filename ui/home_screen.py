from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import database
from ui.styles import *


class HomeScreen(QWidget):
    """
    Per-language home screen.  Shows different options depending on whether
    the deck has cards or not.
    """

    def __init__(self, app_window, language: str):
        super().__init__()
        self.app = app_window
        self.language = language
        self._build_ui()

    # ── Build / rebuild ────────────────────────────────────────────────────────

    def _build_ui(self):
        # Clear any existing layout children so we can rebuild on refresh
        if self.layout():
            while self.layout().count():
                item = self.layout().takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            # Delete the old layout itself
            old_layout = self.layout()
            QWidget().setLayout(old_layout)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(70, 50, 70, 70)
        layout.setSpacing(0)

        # ── Top bar ────────────────────────────────────────────────────────────
        top = QHBoxLayout()
        back_btn = QPushButton("← All Decks")
        back_btn.setStyleSheet(BTN_GHOST)
        back_btn.clicked.connect(self.app.go_to_start)
        top.addWidget(back_btn)
        top.addStretch()
        layout.addLayout(top)
        layout.addSpacing(30)

        # ── Language title ─────────────────────────────────────────────────────
        title = QLabel(self.language)
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Georgia", 40, QFont.Bold))
        title.setStyleSheet(f"color: {TEXT_PRIMARY};")
        layout.addWidget(title)

        cards = database.get_all_cards(self.language)
        count_text = f"{len(cards)} {'card' if len(cards) == 1 else 'cards'}"
        count_label = QLabel(count_text)
        count_label.setAlignment(Qt.AlignCenter)
        count_label.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-size: 14px; margin-top: 6px; margin-bottom: 52px;"
        )
        layout.addWidget(count_label)

        # ── Action buttons ─────────────────────────────────────────────────────
        buttons = [("＋  Add Card", self._add_card, BTN_PRIMARY)]

        if cards:
            buttons += [
                ("⌕  Search Cards",        self._search,    BTN_SECONDARY),
                ("⊞  Show All Cards",       self._show_all,  BTN_SECONDARY),
                ("◈  Spaced Repetition",    self._spaced,    BTN_SECONDARY),
            ]

        for label, handler, style in buttons:
            btn = QPushButton(label)
            btn.setStyleSheet(style)
            btn.setFixedHeight(52)
            btn.clicked.connect(handler)

            row = QHBoxLayout()
            row.addStretch()
            row.addWidget(btn)
            row.addStretch()
            layout.addLayout(row)
            layout.addSpacing(14)

        layout.addStretch()

    def on_resume(self):
        """Called by AppWindow when this screen becomes visible again."""
        self._build_ui()

    # ── Button handlers ────────────────────────────────────────────────────────

    def _add_card(self):
        from ui.add_card_dialog import AddCardDialog
        dialog = AddCardDialog(self, self.language)
        if dialog.exec():
            self._build_ui()   # refresh card count

    def _search(self):
        from ui.search_screen import SearchScreen
        self.app.navigate_to(SearchScreen(self.app, self.language))

    def _show_all(self):
        from ui.all_cards_screen import AllCardsScreen
        self.app.navigate_to(AllCardsScreen(self.app, self.language))

    def _spaced(self):
        QMessageBox.information(
            self, "Coming Soon",
            "Spaced repetition practice is coming soon!\n\nIt will use the FSRS algorithm to schedule your reviews."
        )