from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QGraphicsOpacityEffect, QProgressBar
)
from PySide6.QtCore import Qt, QPropertyAnimation
from PySide6.QtGui import QFont, QFontMetrics

import database
from scheduler import EASY, MEDIUM, HARD
from ui.styles import *

_CARD_INNER_W = 472


def _truncate_to_lines(text, font, max_width, max_lines):
    fm = QFontMetrics(font)
    result_lines = []
    for paragraph in text.splitlines():
        words = paragraph.split()
        if not words:
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
    # check if truncated
    all_lines = []
    for para in text.splitlines():
        words = para.split()
        if not words:
            all_lines.append("")
            continue
        cur = ""
        for w in words:
            cand = (cur + " " + w).strip()
            if fm.horizontalAdvance(cand) <= max_width:
                cur = cand
            else:
                all_lines.append(cur)
                cur = w
        if cur:
            all_lines.append(cur)
    if len(all_lines) > max_lines and result_lines:
        result_lines[-1] = fm.elidedText(result_lines[-1] + " …", Qt.ElideRight, max_width)
    return "\n".join(result_lines)


# ── Rating button styles ───────────────────────────────────────────────────────

_BTN_HARD = """
QPushButton {
    background-color: #4D2020;
    color: #FF8A80;
    border: 1px solid #7B3333;
    border-radius: 10px;
    padding: 12px 0px;
    font-size: 14px;
    font-weight: bold;
}
QPushButton:hover { background-color: #6B2C2C; }
QPushButton:disabled { opacity: 0.4; }
"""

_BTN_MEDIUM = """
QPushButton {
    background-color: #3D2E10;
    color: #FFB74D;
    border: 1px solid #6B4F1A;
    border-radius: 10px;
    padding: 12px 0px;
    font-size: 14px;
    font-weight: bold;
}
QPushButton:hover { background-color: #5A4215; }
QPushButton:disabled { opacity: 0.4; }
"""

_BTN_EASY = """
QPushButton {
    background-color: #1A3D2B;
    color: #69F0AE;
    border: 1px solid #2A6B47;
    border-radius: 10px;
    padding: 12px 0px;
    font-size: 14px;
    font-weight: bold;
}
QPushButton:hover { background-color: #255C3F; }
QPushButton:disabled { opacity: 0.4; }
"""


# ── Practice Screen ────────────────────────────────────────────────────────────

class PracticeScreen(QWidget):

    def __init__(self, app_window, language: str):
        super().__init__()
        self.app      = app_window
        self.language = language
        self.is_front = True
        self._anim    = None
        self._effect  = None
        self._flipping = False

        self._load_queue()
        self._build_ui()

        if self.queue:
            self._show_current_card()
        else:
            self._show_empty()

    # ── Queue management ───────────────────────────────────────────────────────

    def _load_queue(self):
        due, new = database.get_practice_cards(self.language)
        # Due cards first (already sorted by date), then new cards
        self.queue     = due + new
        self.due_count = len(due)
        self.new_count = len(new)
        self.total     = len(self.queue)
        self.reviewed  = 0

    # ── Build UI ───────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(70, 50, 70, 60)
        self.main_layout.setSpacing(0)

        # ── Top bar ────────────────────────────────────────────────────────────
        top = QHBoxLayout()
        back_btn = QPushButton("← Back")
        back_btn.setStyleSheet(BTN_GHOST)
        back_btn.setFocusPolicy(Qt.NoFocus)
        back_btn.clicked.connect(self.app.go_back)
        top.addWidget(back_btn)
        top.addStretch()

        self.counter_label = QLabel("")
        self.counter_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
        top.addWidget(self.counter_label)
        self.main_layout.addLayout(top)
        self.main_layout.addSpacing(10)

        # ── Progress bar ───────────────────────────────────────────────────────
        self.progress = QProgressBar()
        self.progress.setFixedHeight(6)
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: {BORDER};
                border-radius: 3px;
                border: none;
            }}
            QProgressBar::chunk {{
                background-color: {ACCENT};
                border-radius: 3px;
            }}
        """)
        self.main_layout.addWidget(self.progress)
        self.main_layout.addSpacing(20)

        # ── Session info ───────────────────────────────────────────────────────
        self.session_label = QLabel("")
        self.session_label.setAlignment(Qt.AlignCenter)
        self.session_label.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-size: 13px; margin-bottom: 10px;"
        )
        self.main_layout.addWidget(self.session_label)

        # ── Title ──────────────────────────────────────────────────────────────
        title = QLabel(f"Practice — {self.language}")
        title.setFont(QFont("Georgia", 22, QFont.Bold))
        title.setStyleSheet(f"color: {TEXT_PRIMARY};")
        self.main_layout.addWidget(title)
        self.main_layout.addSpacing(24)

        # ── Card frame ─────────────────────────────────────────────────────────
        self.card_frame = QFrame()
        self.card_frame.setFixedSize(560, 420)
        self.card_frame.setCursor(Qt.PointingHandCursor)
        self.card_frame.mousePressEvent = lambda e: self._on_card_click()

        self.card_inner = QVBoxLayout(self.card_frame)
        self.card_inner.setContentsMargins(44, 36, 44, 36)
        self.card_inner.setSpacing(12)
        self.card_inner.setAlignment(Qt.AlignCenter)

        self.lbl_word = QLabel("")
        self.lbl_word.setAlignment(Qt.AlignCenter)
        self.lbl_word.setWordWrap(True)
        self.lbl_word.setFont(QFont("Georgia", 44, QFont.Bold))
        self.lbl_word.setStyleSheet("color: #1A1A1A; background: transparent; border: none;")
        self.card_inner.addWidget(self.lbl_word)

        self.lbl_translation = QLabel("")
        self.lbl_translation.setAlignment(Qt.AlignCenter)
        self.lbl_translation.setWordWrap(True)
        self.lbl_translation.setFont(QFont("Georgia", 32, QFont.Bold))
        self.lbl_translation.setStyleSheet("color: #1A1A1A; background: transparent; border: none;")
        self.lbl_translation.hide()
        self.card_inner.addWidget(self.lbl_translation)

        desc_font = QFont("Helvetica Neue", 16)
        self.lbl_desc = QLabel("")
        self.lbl_desc.setAlignment(Qt.AlignCenter)
        self.lbl_desc.setWordWrap(True)
        self.lbl_desc.setFont(desc_font)
        fm = QFontMetrics(desc_font)
        self.lbl_desc.setFixedHeight(fm.lineSpacing() * 5 + 8)
        self.lbl_desc.setStyleSheet("color: #4A4A4A; background: transparent; border: none;")
        self.lbl_desc.hide()
        self.card_inner.addWidget(self.lbl_desc)

        self.lbl_hint = QLabel("Click card or press Space to flip")
        self.lbl_hint.setAlignment(Qt.AlignCenter)
        self.lbl_hint.setStyleSheet(
            "color: #6A6A6A; font-size: 11px; background: transparent; border: none;"
        )
        self.card_inner.addWidget(self.lbl_hint)

        card_row = QHBoxLayout()
        card_row.addStretch()
        card_row.addWidget(self.card_frame)
        card_row.addStretch()
        self.main_layout.addLayout(card_row)
        self.main_layout.addSpacing(28)

        # ── Flip button ────────────────────────────────────────────────────────
        self.flip_btn = QPushButton("Flip Card")
        self.flip_btn.setStyleSheet(BTN_PRIMARY)
        self.flip_btn.setFixedHeight(50)
        self.flip_btn.setFocusPolicy(Qt.NoFocus)
        self.flip_btn.clicked.connect(self._flip)

        flip_row = QHBoxLayout()
        flip_row.addStretch()
        flip_row.addWidget(self.flip_btn)
        flip_row.addStretch()
        self.main_layout.addLayout(flip_row)

        # ── Rating buttons ─────────────────────────────────────────────────────
        self.rating_widget = QWidget()
        rating_layout = QHBoxLayout(self.rating_widget)
        rating_layout.setSpacing(12)
        rating_layout.setContentsMargins(0, 0, 0, 0)

        self.btn_hard   = QPushButton(f"Hard  (+{HARD}d)")
        self.btn_medium = QPushButton(f"Medium  (+{MEDIUM}d)")
        self.btn_easy   = QPushButton(f"Easy  (+{EASY}d)")

        self.btn_hard.setStyleSheet(_BTN_HARD)
        self.btn_medium.setStyleSheet(_BTN_MEDIUM)
        self.btn_easy.setStyleSheet(_BTN_EASY)

        for btn in (self.btn_hard, self.btn_medium, self.btn_easy):
            btn.setFixedHeight(50)
            btn.setFocusPolicy(Qt.NoFocus)

        self.btn_hard.clicked.connect(lambda: self._rate(HARD))
        self.btn_medium.clicked.connect(lambda: self._rate(MEDIUM))
        self.btn_easy.clicked.connect(lambda: self._rate(EASY))

        rating_layout.addWidget(self.btn_hard)
        rating_layout.addWidget(self.btn_medium)
        rating_layout.addWidget(self.btn_easy)

        self.rating_widget.hide()
        self.main_layout.addWidget(self.rating_widget)
        self.main_layout.addStretch()

        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()

    # ── Show current card ──────────────────────────────────────────────────────

    def _show_current_card(self):
        if not self.queue:
            self._show_empty()
            return

        card = self.queue[0]
        self.is_front  = True
        self._flipping = False

        # Determine label for this card
        idx = self.total - len(self.queue)
        if idx < self.due_count:
            tag = "📅 Revision"
        else:
            tag = "🆕 New Card"
        self.session_label.setText(tag)

        # Card background
        self.card_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {card['color']};
                border-radius: 22px;
                border: 1px solid rgba(0,0,0,0.12);
            }}
        """)

        self.lbl_word.setText(card["word"])
        self.lbl_word.show()
        self.lbl_translation.hide()
        self.lbl_desc.hide()
        self.lbl_hint.setText("Click card or press Space to flip")

        self.flip_btn.setEnabled(True)
        self.flip_btn.show()
        self.rating_widget.hide()

        done = self.total - len(self.queue)
        self.counter_label.setText(f"{done} / {self.total}")
        self.progress.setMaximum(max(self.total, 1))
        self.progress.setValue(done)

    # ── Empty state ────────────────────────────────────────────────────────────

    def _show_empty(self):
        self.card_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_CARD};
                border-radius: 22px;
                border: 1px solid {BORDER};
            }}
        """)
        self.lbl_word.hide()
        self.lbl_translation.hide()
        self.lbl_desc.hide()
        self.flip_btn.hide()
        self.rating_widget.hide()
        self.session_label.setText("")
        self.counter_label.setText("")
        self.progress.setValue(0)

        icon = QLabel("✓")
        icon.setAlignment(Qt.AlignCenter)
        icon.setFont(QFont("Helvetica Neue", 52))
        icon.setStyleSheet("background: transparent; border: none; color: #4A9A6A;")

        msg = QLabel("You're all caught up!\nNo cards are due for practice today.")
        msg.setAlignment(Qt.AlignCenter)
        msg.setFont(QFont("Georgia", 17))
        msg.setWordWrap(True)
        msg.setStyleSheet(f"color: #1A1A1A; background: transparent; border: none;")

        self.card_inner.addWidget(icon)
        self.card_inner.addWidget(msg)
        self.lbl_hint.setText("Press Escape to go back")
        self.lbl_hint.show()

    # ── Flip ───────────────────────────────────────────────────────────────────

    def _on_card_click(self):
        if self.is_front and self.queue and not self._flipping:
            self._flip()

    def _flip(self):
        if not self.queue or not self.is_front or self._flipping:
            return
        self._flipping = True
        self.flip_btn.setEnabled(False)

        self._effect = QGraphicsOpacityEffect(self.card_frame)
        self.card_frame.setGraphicsEffect(self._effect)

        fade_out = QPropertyAnimation(self._effect, b"opacity")
        fade_out.setDuration(100)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.finished.connect(self._show_back)
        fade_out.start()
        self._anim = fade_out

    def _show_back(self):
        if not self._flipping or not self.queue:
            self._flipping = False
            return
        self._flipping = False
        self.is_front = False
        card = self.queue[0]

        self.lbl_word.hide()
        self.lbl_translation.setText(card["translation"])
        self.lbl_translation.show()

        desc = card.get("description", "").strip()
        if desc:
            desc_font = QFont("Helvetica Neue", 16)
            truncated = _truncate_to_lines(desc, desc_font, _CARD_INNER_W, 5)
            self.lbl_desc.setText(truncated)
            self.lbl_desc.show()

        self.lbl_hint.setText("How difficult was this card?")
        self.flip_btn.hide()
        self.rating_widget.show()

        fade_in = QPropertyAnimation(self._effect, b"opacity")
        fade_in.setDuration(100)
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)
        fade_in.start()
        self._anim = fade_in

    # ── Rating ─────────────────────────────────────────────────────────────────

    def _rate(self, days: int):
        if not self.queue:
            return
        self._flipping = False
        if self._anim:
            self._anim.stop()

        card = self.queue.pop(0)
        database.save_review(self.language, card["id"], days)
        self.reviewed += 1
        self._show_current_card()

    # ── Key events ─────────────────────────────────────────────────────────────

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.app.go_back()
        elif event.key() in (Qt.Key_Space, Qt.Key_Return):
            if self.is_front and self.queue:
                self._flip()
        else:
            super().keyPressEvent(event)