from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QTextEdit,
    QButtonGroup, QMessageBox
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont
import database
from ui.styles import *


# ── Colour swatch button ───────────────────────────────────────────────────────

class ColorButton(QPushButton):
    def __init__(self, color_hex: str, color_name: str, parent=None):
        super().__init__(parent)
        self.color_hex = color_hex
        self.color_name = color_name
        self.setFixedSize(36, 36)
        self.setToolTip(color_name)
        self.setCheckable(True)
        self._refresh_style()

    def _refresh_style(self):
        ring = f"3px solid {ACCENT}" if self.isChecked() else f"2px solid {BORDER}"
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.color_hex};
                border: {ring};
                border-radius: 18px;
            }}
            QPushButton:hover {{
                border: 2px solid {ACCENT};
            }}
        """)

    def setChecked(self, checked: bool):
        super().setChecked(checked)
        self._refresh_style()

    # Force button group to call setChecked instead of toggling off
    def nextCheckState(self):
        self.setChecked(True)


# ── Dialog ─────────────────────────────────────────────────────────────────────

class AddCardDialog(QDialog):
    """
    Modal form for adding a new card or editing an existing one.
    Pass `card_data` (dict) to pre-fill fields for editing.
    """

    def __init__(self, parent, language: str, card_data: dict = None):
        super().__init__(parent)
        self.language = language
        self.card_data = card_data
        self.selected_color = card_data["color"] if card_data else "#FFF8E7"
        self._color_btns: list[ColorButton] = []

        self.setWindowTitle("Edit Card" if card_data else "New Card")
        self.setMinimumWidth(540)
        self.setModal(True)

        # Apply a variant of the app style suited to a dialog background
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {BG_CARD};
            }}
            QWidget {{
                background-color: {BG_CARD};
                color: {TEXT_PRIMARY};
                font-family: 'Helvetica Neue', 'SF Pro Text', Arial, sans-serif;
            }}
            QLineEdit {{
                background-color: {BG};
                color: {TEXT_PRIMARY};
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 14px;
            }}
            QLineEdit:focus {{ border-color: {ACCENT}; }}
            QTextEdit {{
                background-color: {BG};
                color: {TEXT_PRIMARY};
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 14px;
            }}
            QTextEdit:focus {{ border-color: {ACCENT}; }}
        """)

        self._build_ui()

    # ── Layout ─────────────────────────────────────────────────────────────────

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 36, 36, 36)
        layout.setSpacing(18)

        # Dialog title
        heading = QLabel("Edit Card" if self.card_data else "New Card")
        heading.setFont(QFont("Georgia", 22, QFont.Bold))
        heading.setStyleSheet(f"color: {TEXT_PRIMARY};")
        layout.addWidget(heading)

        # ── Word ───────────────────────────────────────────────────────────────
        layout.addWidget(self._label("WORD"))
        self.word_input = QLineEdit()
        self.word_input.setPlaceholderText("Enter the word…")
        if self.card_data:
            self.word_input.setText(self.card_data["word"])
        layout.addWidget(self.word_input)

        # ── Translation ────────────────────────────────────────────────────────
        layout.addWidget(self._label("TRANSLATION"))
        self.trans_input = QLineEdit()
        self.trans_input.setPlaceholderText("Enter the translation…")
        if self.card_data:
            self.trans_input.setText(self.card_data["translation"])
        layout.addWidget(self.trans_input)

        # ── Description ────────────────────────────────────────────────────────
        layout.addWidget(self._label("DESCRIPTION  (optional)"))
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText(
            "Add notes, example sentences, usage context…"
        )
        self.desc_input.setFixedHeight(88)
        if self.card_data:
            self.desc_input.setPlainText(self.card_data.get("description", ""))
        layout.addWidget(self.desc_input)

        # ── Colour picker ──────────────────────────────────────────────────────
        layout.addWidget(self._label("CARD COLOUR"))
        grid = QGridLayout()
        grid.setSpacing(8)
        group = QButtonGroup(self)
        group.setExclusive(True)

        for idx, (hex_color, name) in enumerate(CARD_COLORS):
            btn = ColorButton(hex_color, name)
            btn.clicked.connect(lambda _checked, h=hex_color: self._pick_color(h))
            if hex_color == self.selected_color:
                btn.setChecked(True)
            group.addButton(btn)
            self._color_btns.append(btn)
            grid.addWidget(btn, idx // 8, idx % 8)

        layout.addLayout(grid)

        # ── Action buttons ─────────────────────────────────────────────────────
        layout.addSpacing(6)
        btn_row = QHBoxLayout()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(BTN_SECONDARY)
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Save Card")
        save_btn.setStyleSheet(BTN_PRIMARY)
        save_btn.setDefault(True)
        save_btn.clicked.connect(self._save)

        btn_row.addWidget(cancel_btn)
        btn_row.addStretch()
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-size: 11px; letter-spacing: 1.5px;"
        )
        return lbl

    # ── Handlers ───────────────────────────────────────────────────────────────

    def _pick_color(self, hex_color: str):
        self.selected_color = hex_color
        for btn in self._color_btns:
            btn._refresh_style()

    def _save(self):
        word  = self.word_input.text().strip()
        trans = self.trans_input.text().strip()
        desc  = self.desc_input.toPlainText().strip()

        if not word or not trans:
            QMessageBox.warning(
                self, "Missing Fields",
                "Please fill in both the Word and Translation fields."
            )
            return

        if self.card_data:
            database.update_card(
                self.language, self.card_data["id"],
                word, trans, desc, self.selected_color
            )
        else:
            database.add_card(self.language, word, trans, desc, self.selected_color)

        self.accept()