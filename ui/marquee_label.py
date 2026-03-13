from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer, QRect
from PySide6.QtGui import QPainter, QFontMetrics, QFont, QColor


class MarqueeLabel(QWidget):
    """
    A label that displays text normally when it fits.
    When the text is too wide it smoothly slides left and then resets,
    giving a ticker-tape / marquee effect.

    Parameters
    ----------
    text        : str   — text to display
    font        : QFont — font to use
    color       : str   — CSS hex color for the text
    bg_color    : str   — hex color of the card background (for fade edges)
    speed       : int   — pixels per timer tick (default 1)
    pause_ms    : int   — milliseconds to pause at each end (default 1200)
    """

    def __init__(
        self,
        text: str = "",
        font: QFont = None,
        color: str = "#1A1A1A",
        bg_color: str = "#FFFFFF",
        speed: int = 1,
        pause_ms: int = 1200,
        parent=None,
    ):
        super().__init__(parent)
        self._text = text
        self._font = font or QFont("Georgia", 16)
        self._color = QColor(color)
        self._bg_color = QColor(bg_color)
        self._speed = speed
        self._pause_ms = pause_ms

        self._offset = 0
        self._text_width = 0
        self._scrolling = False
        self._pausing = False

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)

        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumHeight(self._line_height() + 8)

    # ── Public API ─────────────────────────────────────────────────────────────

    def setText(self, text: str):
        self._text = text
        self._offset = 0
        self._update_scroll_state()
        self.update()

    def setTextColor(self, color: str):
        self._color = QColor(color)
        self.update()

    def setBgColor(self, color: str):
        self._bg_color = QColor(color)
        self.update()

    def setTextFont(self, font: QFont):
        self._font = font
        self.setMinimumHeight(self._line_height() + 8)
        self._offset = 0
        self._update_scroll_state()
        self.update()

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _line_height(self) -> int:
        return QFontMetrics(self._font).height()

    def _measure_text(self) -> int:
        return QFontMetrics(self._font).horizontalAdvance(self._text)

    def _update_scroll_state(self):
        self._text_width = self._measure_text()
        needs_scroll = self._text_width > self.width()
        if needs_scroll and not self._timer.isActive():
            self._offset = 0
            self._pausing = True
            self._timer.start(16)        # ~60 fps
        elif not needs_scroll:
            self._timer.stop()
            self._offset = 0
            self._scrolling = False

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_scroll_state()

    def showEvent(self, event):
        super().showEvent(event)
        self._update_scroll_state()

    def hideEvent(self, event):
        super().hideEvent(event)
        self._timer.stop()
        self._offset = 0

    def _tick(self):
        if self._pausing:
            return

        self._offset += self._speed
        overflow = self._text_width - self.width()

        if self._offset >= overflow + 20:       # scrolled fully off + small gap
            self._offset = overflow + 20
            self._pausing = True
            QTimer.singleShot(self._pause_ms, self._reset)

        self.update()

    def _reset(self):
        self._offset = 0
        self._pausing = True
        self.update()
        QTimer.singleShot(self._pause_ms, self._start_scroll)

    def _start_scroll(self):
        self._pausing = False

    # ── Paint ──────────────────────────────────────────────────────────────────

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setFont(self._font)

        fm = QFontMetrics(self._font)
        y = (self.height() + fm.ascent() - fm.descent()) // 2

        needs_scroll = self._text_width > self.width()

        if needs_scroll:
            painter.setClipRect(QRect(0, 0, self.width(), self.height()))
            painter.setPen(self._color)
            painter.drawText(-int(self._offset), y, self._text)

            # Soft fade edges so the scroll looks polished
            fade_w = min(28, self.width() // 5)
            for x in range(fade_w):
                alpha = int(255 * (1 - x / fade_w))
                fade_color = QColor(self._bg_color)
                fade_color.setAlpha(alpha)
                painter.setPen(fade_color)
                painter.drawLine(x, 0, x, self.height())                    # left edge
                painter.drawLine(self.width() - x - 1, 0,
                                 self.width() - x - 1, self.height())       # right edge
        else:
            # Centre the text when it fits
            x = (self.width() - self._text_width) // 2
            painter.setPen(self._color)
            painter.drawText(x, y, self._text)

        painter.end()