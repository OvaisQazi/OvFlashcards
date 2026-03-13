from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer, QRect
from PySide6.QtGui import QPainter, QFontMetrics, QFont, QColor, QPen


class MarqueeLabel(QWidget):
    """
    Displays text centred when it fits.
    When the text is wider than the widget it smoothly scrolls left,
    pauses, resets, pauses, then scrolls again.
    """

    def __init__(
        self,
        text: str = "",
        font: QFont = None,
        color: str = "#1A1A1A",
        bg_color: str = "#FFFFFF",
        speed: int = 1,
        pause_ms: int = 1400,
        parent=None,
    ):
        super().__init__(parent)
        self._text     = text
        self._font     = font or QFont("Georgia", 16)
        self._color    = QColor(color)
        self._bg_color = QColor(bg_color)
        self._speed    = speed
        self._pause_ms = pause_ms

        self._offset      = 0
        self._pausing     = False
        self._initialized = False   # True after first resizeEvent

        self._timer = QTimer(self)
        self._timer.setInterval(16)   # ~60 fps
        self._timer.timeout.connect(self._tick)

        self.setMinimumHeight(QFontMetrics(self._font).height() + 10)

    # ── Public API ─────────────────────────────────────────────────────────────

    def setText(self, text: str):
        self._text    = text
        self._offset  = 0
        self._pausing = False
        self._restart_if_needed()
        self.update()

    def setTextColor(self, color: str):
        self._color = QColor(color)
        self.update()

    def setBgColor(self, color: str):
        self._bg_color = QColor(color)
        self.update()

    def setTextFont(self, font: QFont):
        self._font   = font
        self._offset = 0
        self.setMinimumHeight(QFontMetrics(font).height() + 10)
        self._restart_if_needed()
        self.update()

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _text_width(self) -> int:
        return QFontMetrics(self._font).horizontalAdvance(self._text)

    def _overflow(self) -> int:
        return max(0, self._text_width() - self.width())

    def _restart_if_needed(self):
        if not self._initialized:
            return
        if self._overflow() > 0:
            self._offset  = 0
            self._pausing = True
            if not self._timer.isActive():
                self._timer.start()
            QTimer.singleShot(self._pause_ms, self._start_scroll)
        else:
            self._timer.stop()
            self._offset  = 0
            self._pausing = False

    # ── Qt events ──────────────────────────────────────────────────────────────

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._initialized = True
        self._restart_if_needed()

    def showEvent(self, event):
        super().showEvent(event)
        if self._initialized:
            self._restart_if_needed()

    def hideEvent(self, event):
        super().hideEvent(event)
        self._timer.stop()
        self._offset  = 0
        self._pausing = False

    # ── Animation ──────────────────────────────────────────────────────────────

    def _start_scroll(self):
        self._pausing = False

    def _tick(self):
        if self._pausing:
            return
        self._offset += self._speed
        ov = self._overflow()
        if self._offset >= ov + 16:
            self._offset  = ov + 16
            self._pausing = True
            QTimer.singleShot(self._pause_ms, self._do_reset)
        self.update()

    def _do_reset(self):
        self._offset  = 0
        self._pausing = True
        self.update()
        QTimer.singleShot(self._pause_ms, self._start_scroll)

    # ── Paint ──────────────────────────────────────────────────────────────────

    def paintEvent(self, event):
        if not self._text:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Explicitly fill background — never rely on transparency
        painter.fillRect(self.rect(), self._bg_color)

        painter.setFont(self._font)
        fm = QFontMetrics(self._font)
        tw = self._text_width()
        y  = (self.height() + fm.ascent() - fm.descent()) // 2

        if tw > self.width():
            painter.setClipRect(QRect(0, 0, self.width(), self.height()))
            painter.setPen(QPen(self._color))
            painter.drawText(-int(self._offset), y, self._text)

            # Soft fade on both edges
            fade = min(24, self.width() // 6)
            for i in range(fade):
                ratio = 1.0 - i / fade
                c = QColor(self._bg_color)
                c.setAlphaF(ratio)
                painter.setPen(QPen(c))
                painter.drawLine(i, 0, i, self.height())
                painter.drawLine(self.width() - i - 1, 0, self.width() - i - 1, self.height())
        else:
            x = max(0, (self.width() - tw) // 2)
            painter.setPen(QPen(self._color))
            painter.drawText(x, y, self._text)

        painter.end()