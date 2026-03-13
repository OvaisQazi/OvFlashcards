from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QInputDialog, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import database
from ui.styles import *


class StartScreen(QWidget):
    """
    Landing screen: shows existing language decks and a button to add a new one.
    """

    def __init__(self, app_window):
        super().__init__()
        self.app = app_window
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        # ── Centered content column ────────────────────────────────────────────
        col = QVBoxLayout()
        col.setContentsMargins(80, 70, 80, 70)
        col.setSpacing(0)

        # Title
        title = QLabel("Flashcards")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Georgia", 44, QFont.Bold))
        title.setStyleSheet(f"color: {TEXT_PRIMARY};")
        col.addWidget(title)

        subtitle = QLabel("Your personal language learning companion")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-size: 15px; margin-top: 6px; margin-bottom: 52px;"
        )
        col.addWidget(subtitle)

        # ── Existing decks ─────────────────────────────────────────────────────
        languages = database.get_all_languages()

        if languages:
            section = QLabel("YOUR DECKS")
            section.setAlignment(Qt.AlignCenter)
            section.setStyleSheet(
                f"color: {TEXT_SECONDARY}; font-size: 11px; letter-spacing: 2.5px; margin-bottom: 14px;"
            )
            col.addWidget(section)

            for lang in languages:
                btn = QPushButton(f"  {lang}")
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {BG_CARD};
                        color: {TEXT_PRIMARY};
                        border: 1px solid {BORDER};
                        border-radius: 12px;
                        padding: 16px 24px;
                        font-size: 16px;
                        text-align: left;
                    }}
                    QPushButton:hover {{
                        border-color: {ACCENT};
                        background-color: #2D2520;
                    }}
                    QPushButton:pressed {{
                        background-color: {BG};
                    }}
                """)
                btn.clicked.connect(lambda _checked, l=lang: self._open_language(l))
                col.addWidget(btn)
                col.addSpacing(10)

            col.addSpacing(28)

        else:
            col.addStretch()
            empty = QLabel("No decks yet.\nCreate your first language deck to get started.")
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 15px; line-height: 1.8;")
            col.addWidget(empty)
            col.addSpacing(36)

        # ── New language button ────────────────────────────────────────────────
        new_btn = QPushButton("＋  New Language Deck")
        new_btn.setStyleSheet(BTN_PRIMARY)
        new_btn.setFixedHeight(52)
        new_btn.clicked.connect(self._new_language)

        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(new_btn)
        row.addStretch()
        col.addLayout(row)
        col.addStretch()

        outer.addLayout(col)

    # ── Handlers ───────────────────────────────────────────────────────────────

    def _open_language(self, language: str):
        database.create_language_db(language)
        self.app.go_home(language)

    def _new_language(self):
        text, ok = QInputDialog.getText(
            self, "New Language Deck", "Enter the language name:"
        )
        if not ok or not text.strip():
            return

        lang = text.strip().capitalize()

        if database.language_exists(lang):
            QMessageBox.information(
                self, "Already Exists",
                f'A deck for "{lang}" already exists. Opening it now.'
            )
        else:
            database.create_language_db(lang)

        self.app.go_home(lang)