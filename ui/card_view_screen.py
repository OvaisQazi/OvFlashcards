from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QMessageBox, QGraphicsOpacityEffect
)
from PySide6.QtCore import Qt, QPropertyAnimation
from PySide6.QtGui import QFont, QColor
import database
from ui.styles import *


class CardViewScreen(QWidget):
    """
    Shows a single flashcard.
    - Front: displays the Word
    - Back:  displays Translation + Description
    Click the card (or press Space) to flip.  Escape / Back button to return.
    """

    def __init__(self, app_window, language: str, card: dict):
        super().__init__()
        self.app = app_window
        self.language = language
        self.card = card
        self.is_front = True
        self._anim = None           # keep animation reference alive

        self._build_ui()

    # ── Build UI ───────────────────────────────────────────────────────────────

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(70, 50, 70, 60)
        layout.setSpacing(0)

        # ── Top bar ────────────────────────────────────────────────────────────
        top = QHBoxLayout()

        back_btn = QPushButton("← Back")
        back_btn.setStyleSheet(BTN_GHOST)
        back_btn.setFocusPolicy(Qt.NoFocus)
        back_btn.clicked.connect(self.app.go_back)
        top.addWidget(back_btn)
        top.addStretch()

        edit_btn = QPushButton("Edit")
        edit_btn.setStyleSheet(BTN_SECONDARY)
        edit_btn.setFocusPolicy(Qt.NoFocus)
        edit_btn.clicked.connect(self._edit)

        del_btn = QPushButton("Delete")
        del_btn.setStyleSheet(BTN_DANGER)
        del_btn.setFocusPolicy(Qt.NoFocus)
        del_btn.clicked.connect(self._delete)

        top.addWidget(edit_btn)
        top.addSpacing(10)
        top.addWidget(del_btn)
        layout.addLayout(top)

        layout.addStretch()

        # ── Card widget ────────────────────────────────────────────────────────
        self.card_frame = QFrame()
        self.card_frame.setFixedSize(460, 300)
        self.card_frame.setCursor(Qt.PointingHandCursor)
        self._apply_card_style()

        card_inner = QVBoxLayout(self.card_frame)
        card_inner.setContentsMargins(44, 40, 44, 40)
        card_inner.setSpacing(10)
        card_inner.setAlignment(Qt.AlignCenter)

        tc, sc = self._text_colors()

        # Front content
        self.front_word = QLabel(self.card["word"])
        self.front_word.setAlignment(Qt.AlignCenter)
        self.front_word.setFont(QFont("Georgia", 34, QFont.Bold))
        self.front_word.setWordWrap(True)
        self.front_word.setStyleSheet(
            f"color: {tc}; background: transparent; border: none;"
        )
        card_inner.addWidget(self.front_word)

        # Back content (hidden initially)
        self.back_trans = QLabel(self.card["translation"])
        self.back_trans.setAlignment(Qt.AlignCenter)
        self.back_trans.setFont(QFont("Georgia", 28, QFont.Bold))
        self.back_trans.setWordWrap(True)
        self.back_trans.setStyleSheet(
            f"color: {tc}; background: transparent; border: none;"
        )
        self.back_trans.hide()
        card_inner.addWidget(self.back_trans)

        self.back_desc = QLabel(self.card.get("description", ""))
        self.back_desc.setAlignment(Qt.AlignCenter)
        self.back_desc.setFont(QFont("Helvetica Neue", 13))
        self.back_desc.setWordWrap(True)
        self.back_desc.setStyleSheet(
            f"color: {sc}; background: transparent; border: none;"
        )
        self.back_desc.hide()
        card_inner.addWidget(self.back_desc)

        # Hint at the bottom
        self.hint = QLabel("Click card or press Space to flip")
        self.hint.setAlignment(Qt.AlignCenter)
        self.hint.setStyleSheet(
            f"color: {sc}; font-size: 11px; background: transparent; border: none; margin-top: 6px;"
        )
        card_inner.addWidget(self.hint)

        # Click-to-flip
        self.card_frame.mousePressEvent = lambda e: self._flip()

        center_row = QHBoxLayout()
        center_row.addStretch()
        center_row.addWidget(self.card_frame)
        center_row.addStretch()
        layout.addLayout(center_row)

        layout.addStretch()

        # Grab focus so Space/Escape are handled here, not by any button
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()

    # ── Styling helpers ────────────────────────────────────────────────────────

    def _text_colors(self):
        """Return (primary, secondary) text colors for the card background."""
        bg = QColor(self.card["color"])
        lum = (bg.red() * 299 + bg.green() * 587 + bg.blue() * 114) / 1000
        if lum > 140:
            return "#2A2018", "#7A6A58"
        return "#F5ECD7", "#C4B098"

    def _apply_card_style(self):
        self.card_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self.card['color']};
                border-radius: 22px;
                border: 1px solid rgba(0,0,0,0.12);
            }}
        """)

    # ── Flip animation ─────────────────────────────────────────────────────────

    def _flip(self):
        self._effect = QGraphicsOpacityEffect(self.card_frame)
        self.card_frame.setGraphicsEffect(self._effect)

        fade_out = QPropertyAnimation(self._effect, b"opacity")
        fade_out.setDuration(110)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.finished.connect(self._swap_and_fade_in)
        fade_out.start()
        self._anim = fade_out   # prevent GC

    def _swap_and_fade_in(self):
        self.is_front = not self.is_front

        if self.is_front:
            self.front_word.show()
            self.back_trans.hide()
            self.back_desc.hide()
            self.hint.setText("Click card or press Space to flip")
        else:
            self.front_word.hide()
            self.back_trans.show()
            if self.card.get("description", "").strip():
                self.back_desc.show()
            self.hint.setText("Click card or press Space to flip back")

        fade_in = QPropertyAnimation(self._effect, b"opacity")
        fade_in.setDuration(110)
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)
        fade_in.start()
        self._anim = fade_in

    # ── Key events ─────────────────────────────────────────────────────────────

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.app.go_back()
        elif event.key() in (Qt.Key_Space, Qt.Key_Return):
            self._flip()
        else:
            super().keyPressEvent(event)

    # ── Edit / Delete ──────────────────────────────────────────────────────────

    def _edit(self):
        from ui.add_card_dialog import AddCardDialog
        dialog = AddCardDialog(self, self.language, self.card)
        if dialog.exec():
            # Reload updated card from DB
            all_cards = database.get_all_cards(self.language)
            for c in all_cards:
                if c["id"] == self.card["id"]:
                    self.card = c
                    break
            self._refresh_card_display()

    def _refresh_card_display(self):
        """Update all labels and colours after an edit."""
        tc, sc = self._text_colors()
        self._apply_card_style()

        self.front_word.setText(self.card["word"])
        self.front_word.setStyleSheet(
            f"color: {tc}; background: transparent; border: none;"
        )
        self.back_trans.setText(self.card["translation"])
        self.back_trans.setStyleSheet(
            f"color: {tc}; background: transparent; border: none;"
        )
        self.back_desc.setText(self.card.get("description", ""))
        self.back_desc.setStyleSheet(
            f"color: {sc}; background: transparent; border: none;"
        )
        self.hint.setStyleSheet(
            f"color: {sc}; font-size: 11px; background: transparent; border: none; margin-top: 6px;"
        )

        # Reset to front face
        self.is_front = True
        self.front_word.show()
        self.back_trans.hide()
        self.back_desc.hide()

    def _delete(self):
        reply = QMessageBox.question(
            self,
            "Delete Card",
            f'Delete the card for "{self.card["word"]}"?\n\nThis cannot be undone.',
            QMessageBox.Yes | QMessageBox.Cancel,
            QMessageBox.Cancel
        )
        if reply == QMessageBox.Yes:
            database.delete_card(self.language, self.card["id"])
            self.app.go_back()