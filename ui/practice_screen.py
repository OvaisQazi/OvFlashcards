from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QGraphicsOpacityEffect, QProgressBar
)
from PySide6.QtCore import Qt, QPropertyAnimation, QTimer
from PySide6.QtGui import QFont, QFontMetrics, QColor
import database
from scheduler import rate_card, Rating
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
    # check if cut
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


# ── Rating button ──────────────────────────────────────────────────────────────

_RATING_STYLES = {
    "Again": f"""
        QPushButton {{
            background-color: #4D2020;
            color: #FF8A80;
            border: 1px solid #7B3333;
            border-radius: 10px;
            padding: 12px 0px;
            font-size: 14px;
            font-weight: bold;
        }}
        QPushButton:hover {{ background-color: #6B2C2C; }}
    """,
    "Hard": f"""
        QPushButton {{
            background-color: #3D2E10;
            color: #FFB74D;
            border: 1px solid #6B4F1A;
            border-radius: 10px;
            padding: 12px 0px;
            font-size: 14px;
            font-weight: bold;
        }}
        QPushButton:hover {{ background-color: #5A4215; }}
    """,
    "Good": f"""
        QPushButton {{
            background-color: #1A3D2B;
            color: #69F0AE;
            border: 1px solid #2A6B47;
            border-radius: 10px;
            padding: 12px 0px;
            font-size: 14px;
            font-weight: bold;
        }}
        QPushButton:hover {{ background-color: #255C3F; }}
    """,
    "Easy": f"""
        QPushButton {{
            background-color: #1A2E4D;
            color: #64B5F6;
            border: 1px solid #1F4D80;
            border-radius: 10px;
            padding: 12px 0px;
            font-size: 14px;
            font-weight: bold;
        }}
        QPushButton:hover {{ background-color: #1E3F6B; }}
    """,
}


# ── Practice Screen ────────────────────────────────────────────────────────────

class PracticeScreen(QWidget):

    def __init__(self, app_window, language: str):
        super().__init__()
        self.app = app_window
        self.language = language
        self.is_front = True
        self._anim = None
        self._effect = None
        self._flipping = False

        self.queue = database.get_due_cards(language)
        self.total = len(self.queue)
        self.reviewed = 0

        self._build_ui()
        self._load_current_card()

    # ── Build static UI shell ──────────────────────────────────────────────────

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
        self.counter_label.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-size: 13px;"
        )
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
        self.main_layout.addSpacing(30)

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

        # Placeholder labels — filled in _load_current_card
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
            f"color: #6A6A6A; font-size: 11px; background: transparent; border: none;"
        )
        self.card_inner.addWidget(self.lbl_hint)

        card_row = QHBoxLayout()
        card_row.addStretch()
        card_row.addWidget(self.card_frame)
        card_row.addStretch()
        self.main_layout.addLayout(card_row)
        self.main_layout.addSpacing(28)

        # ── Flip button (shown before flip) ────────────────────────────────────
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

        # ── Rating buttons (shown after flip) ──────────────────────────────────
        self.rating_widget = QWidget()
        rating_layout = QHBoxLayout(self.rating_widget)
        rating_layout.setSpacing(12)
        rating_layout.setContentsMargins(0, 0, 0, 0)

        self._rating_btns = {}
        for label, rating in [("Again", Rating.Again), ("Hard", Rating.Hard),
                               ("Good", Rating.Good),  ("Easy", Rating.Easy)]:
            btn = QPushButton(label)
            btn.setStyleSheet(_RATING_STYLES[label])
            btn.setFixedHeight(50)
            btn.setFocusPolicy(Qt.NoFocus)
            btn.clicked.connect(lambda _checked, r=rating: self._rate(r))
            self._rating_btns[label] = btn
            rating_layout.addWidget(btn)

        self.rating_widget.hide()
        self.main_layout.addWidget(self.rating_widget)
        self.main_layout.addStretch()

        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()

    # ── Card loading ───────────────────────────────────────────────────────────

    def _load_current_card(self):
        if not self.queue:
            # Shouldn't happen since _rate refills, but guard just in case
            self.queue = database.get_due_cards(self.language)
            self.total = len(self.queue)
            self.reviewed = 0
            if not self.queue:
                self._show_finished()
                return

        card = self.queue[0]
        self.is_front = True

        # Card background
        self.card_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {card['color']};
                border-radius: 22px;
                border: 1px solid rgba(0,0,0,0.12);
            }}
        """)

        # Labels
        self.lbl_word.setText(card["word"])
        self.lbl_word.show()
        self.lbl_translation.hide()
        self.lbl_desc.hide()
        self.lbl_hint.setText("Click card or press Space to flip")

        self.flip_btn.setEnabled(True)
        self.flip_btn.show()
        self.rating_widget.hide()

        # Progress
        done = self.total - len(self.queue)
        self.counter_label.setText(f"{done} / {self.total}")
        self.progress.setMaximum(self.total)
        self.progress.setValue(done)

    # ── Flip ───────────────────────────────────────────────────────────────────

    def _on_card_click(self):
        if self.is_front and self.queue:
            self._flip()

    def _flip(self):
        if not self.queue or not self.is_front:
            return
        self.flip_btn.setEnabled(False)
        self._flipping = True      # guard so _show_back knows flip is in progress

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
        # Guard: if a rating was given while the animation was in flight, abort
        if not self._flipping or not self.queue or self.is_front is False:
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

        self.lbl_hint.setText("How well did you remember?")
        self.flip_btn.hide()
        self.rating_widget.show()

        fade_in = QPropertyAnimation(self._effect, b"opacity")
        fade_in.setDuration(100)
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)
        fade_in.start()
        self._anim = fade_in

    # ── Rating ─────────────────────────────────────────────────────────────────

    def _rate(self, rating: Rating):
        self._flipping = False     # cancel any in-flight flip animation
        if self._anim:
            self._anim.stop()

        card = self.queue.pop(0)
        updated = rate_card(card, rating)
        database.save_card_review(self.language, card["id"], updated)
        self.reviewed += 1

        # Refill queue if exhausted — keep cumulative reviewed count
        if not self.queue:
            self.queue = database.get_due_cards(self.language)
            self.total = len(self.queue)

        self._load_current_card()

    # ── Finished ───────────────────────────────────────────────────────────────

    def _show_finished(self):
        # Clear card frame
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

        done_lbl = QLabel("🎉")
        done_lbl.setAlignment(Qt.AlignCenter)
        done_lbl.setFont(QFont("Helvetica Neue", 48))
        done_lbl.setStyleSheet("background: transparent; border: none;")

        msg = QLabel(f"All done!\nYou reviewed {self.reviewed} card{'s' if self.reviewed != 1 else ''} today.")
        msg.setAlignment(Qt.AlignCenter)
        msg.setFont(QFont("Georgia", 18))
        msg.setWordWrap(True)
        msg.setStyleSheet(f"color: #1A1A1A; background: transparent; border: none;")

        self.card_inner.addWidget(done_lbl)
        self.card_inner.addWidget(msg)
        self.lbl_hint.setText("Press Escape to go back")

        self.counter_label.setText(f"{self.total} / {self.total}")
        self.progress.setValue(self.total)

    # ── Key events ─────────────────────────────────────────────────────────────

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.app.go_back()
        elif event.key() in (Qt.Key_Space, Qt.Key_Return):
            if self.is_front:
                self._flip()
        else:
            super().keyPressEvent(event)