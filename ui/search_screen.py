from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QLineEdit, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import database
from ui.styles import *


class SearchScreen(QWidget):
    """
    Live-search screen: results update as the user types.
    Clicking a result opens the card view.
    """

    def __init__(self, app_window, language: str):
        super().__init__()
        self.app = app_window
        self.language = language
        self._results: list[dict] = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(70, 50, 70, 60)
        layout.setSpacing(0)

        # Back
        back_btn = QPushButton("← Back")
        back_btn.setStyleSheet(BTN_GHOST)
        back_btn.clicked.connect(self.app.go_back)
        layout.addWidget(back_btn, alignment=Qt.AlignLeft)
        layout.addSpacing(20)

        # Title
        title = QLabel(f"Search — {self.language}")
        title.setFont(QFont("Georgia", 30, QFont.Bold))
        title.setStyleSheet(f"color: {TEXT_PRIMARY};")
        layout.addWidget(title)

        hint = QLabel("Search by word or translation")
        hint.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-size: 13px; margin-top: 4px; margin-bottom: 24px;"
        )
        layout.addWidget(hint)

        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Start typing…")
        self.search_input.setFixedHeight(48)
        self.search_input.textChanged.connect(self._on_text_changed)
        layout.addWidget(self.search_input)
        layout.addSpacing(16)

        # Results list
        self.results_list = QListWidget()
        self.results_list.itemClicked.connect(self._open_card)
        layout.addWidget(self.results_list)

    def on_resume(self):
        """Re-run the current search in case a card was edited/deleted."""
        self._on_text_changed(self.search_input.text())

    def _on_text_changed(self, query: str):
        self.results_list.clear()
        self._results = []

        if not query.strip():
            return

        self._results = database.search_cards(self.language, query.strip())

        for card in self._results:
            item = QListWidgetItem(f"  {card['word']}  →  {card['translation']}")
            self.results_list.addItem(item)

        if not self._results:
            self.results_list.addItem(QListWidgetItem("  No results found."))

    def _open_card(self, item):
        idx = self.results_list.currentRow()
        if 0 <= idx < len(self._results):
            card = self._results[idx]
            from ui.card_view_screen import CardViewScreen
            self.app.navigate_to(CardViewScreen(self.app, self.language, card))