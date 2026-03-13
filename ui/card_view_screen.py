from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QMessageBox, QGraphicsOpacityEffect
)
from PySide6.QtCore import Qt, QPropertyAnimation
from PySide6.QtGui import QFont, QFontMetrics
import database
from ui.styles import *
from ui.marquee_label import MarqueeLabel

# Available text width inside card frame (560px wide - 88px margins)
_CARD_INNER_W = 472


def _truncate_to_lines(text: str, font: QFont, max_width: int, max_lines: int) -> str:
    """
    Respect the user's original line breaks first, then pixel-wrap any line
    that is too wide. Truncates to max_lines total, appending '…' if cut.
    """
    fm = QFontMetrics(font)
    result_lines = []

    for paragraph in text.splitlines():
        # Pixel-wrap each user paragraph into one or more display lines
        words = paragraph.split()
        if not words:
            # blank line the user entered — keep it
            result_lines.append("")
            if len(result_lines) >= max_lines:
                break
            continue

        current = ""
        for word in words:
            candidate = (current + " " + word).strip()
            if fm.horizontalAdvance(candidate) <= max_width:
                current = candidate
            else:
                if current:
                    result_lines.append(current)
                if len(result_lines) >= max_lines:
                    break
                current = word
        else:
            if current and len(result_lines) < max_lines:
                result_lines.append(current)

        if len(result_lines) >= max_lines:
            break

    # Check if we cut anything — if so, elide the last line
    full_lines = []
    for paragraph in text.splitlines():
        words = paragraph.split()
        if not words:
            full_lines.append("")
            continue
        current = ""
        for word in words:
            candidate = (current + " " + word).strip()
            if fm.horizontalAdvance(candidate) <= max_width:
                current = candidate
            else:
                full_lines.append(current)
                current = word
        if current:
            full_lines.append(current)

    if len(full_lines) > max_lines and result_lines:
        last = result_lines[-1]
        result_lines[-1] = fm.elidedText(last + " …", Qt.ElideRight, max_width)

    return "\n".join(result_lines)


def _smart_label(text: str, font: QFont, color: str, bg: str) -> QWidget:
    """
    Returns a QLabel (word-wrap) for normal text.
    Returns a MarqueeLabel ONLY when the text is a single unbreakable token
    that is too wide to fit on one line inside the card.
    """
    is_single_token = " " not in text.strip()
    too_wide = QFontMetrics(font).horizontalAdvance(text) > _CARD_INNER_W

    if is_single_token and too_wide:
        w = MarqueeLabel(text=text, font=font, color=color, bg_color=bg)
        return w

    lbl = QLabel(text)
    lbl.setFont(font)
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setWordWrap(True)
    lbl.setStyleSheet(f"color: {color}; background: transparent; border: none;")
    return lbl


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
        self.card_frame.setFixedSize(560, 480)
        self.card_frame.setCursor(Qt.PointingHandCursor)
        self.card_frame.setClipping = True   # prevent children painting outside
        self._apply_card_style()

        card_inner = QVBoxLayout(self.card_frame)
        card_inner.setContentsMargins(44, 40, 44, 40)
        card_inner.setSpacing(10)
        card_inner.setAlignment(Qt.AlignCenter)

        tc, sc = self._text_colors()
        bg = self.card["color"]

        # ── Front: word (QLabel with word-wrap; MarqueeLabel only for single
        #           long tokens that can't wrap)
        self.front_word = _smart_label(
            self.card["word"], QFont("Georgia", 44, QFont.Bold), tc, bg
        )
        self.front_word.setMinimumHeight(60)
        self.front_word.setMaximumHeight(130)
        card_inner.addWidget(self.front_word)

        # ── Back: translation
        self.back_trans = _smart_label(
            self.card["translation"], QFont("Georgia", 36, QFont.Bold), tc, bg
        )
        self.back_trans.setMinimumHeight(55)
        self.back_trans.setMaximumHeight(110)
        self.back_trans.hide()
        card_inner.addWidget(self.back_trans)

        # ── Back: description — pre-truncated to 3 lines, no Qt word-wrap needed
        desc_font = QFont("Helvetica Neue", 17)
        desc_fm   = QFontMetrics(desc_font)
        desc_h    = desc_fm.lineSpacing() * 5 + 8

        desc_text = _truncate_to_lines(
            self.card.get("description", ""), desc_font, _CARD_INNER_W, 5
        )
        self.back_desc = QLabel(desc_text)
        self.back_desc.setFont(desc_font)
        self.back_desc.setAlignment(Qt.AlignCenter)
        self.back_desc.setWordWrap(True)
        self.back_desc.setFixedHeight(desc_h)
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
        """All card colours are light pastels — always use dark text."""
        return "#1A1A1A", "#4A4A4A"

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
        bg = self.card["color"]
        self._apply_card_style()

        # Both QLabel and MarqueeLabel have setText; only MarqueeLabel has setTextColor/setBgColor
        self.front_word.setText(self.card["word"])
        if isinstance(self.front_word, MarqueeLabel):
            self.front_word.setTextColor(tc)
            self.front_word.setBgColor(bg)
        else:
            self.front_word.setStyleSheet(f"color: {tc}; background: transparent; border: none;")

        self.back_trans.setText(self.card["translation"])
        if isinstance(self.back_trans, MarqueeLabel):
            self.back_trans.setTextColor(tc)
            self.back_trans.setBgColor(bg)
        else:
            self.back_trans.setStyleSheet(f"color: {tc}; background: transparent; border: none;")

        desc_text = _truncate_to_lines(
            self.card.get("description", ""),
            self.back_desc.font(), _CARD_INNER_W, 5
        )
        self.back_desc.setText(desc_text)
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