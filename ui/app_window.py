from PySide6.QtWidgets import QMainWindow, QStackedWidget
from ui.styles import APP_STYLE


class AppWindow(QMainWindow):
    """
    Central window that owns a QStackedWidget for screen navigation.
    Screens call methods here to push/pop themselves.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Flashcards")
        self.setMinimumSize(920, 660)
        self.resize(1020, 740)
        self.setStyleSheet(APP_STYLE)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        self._history: list = []

        self._show_start()

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _push(self, widget):
        self.stack.addWidget(widget)
        self.stack.setCurrentWidget(widget)
        self._history.append(widget)

    def _clear_history(self):
        while self._history:
            w = self._history.pop()
            self.stack.removeWidget(w)
            w.deleteLater()

    def _show_start(self):
        from ui.start_screen import StartScreen
        self._push(StartScreen(self))

    # ── Public navigation API ──────────────────────────────────────────────────

    def navigate_to(self, widget):
        """Push a new screen onto the navigation stack."""
        self._push(widget)

    def go_back(self):
        """Pop the current screen and resume the previous one."""
        if len(self._history) > 1:
            old = self._history.pop()
            self.stack.setCurrentWidget(self._history[-1])
            self.stack.removeWidget(old)
            old.deleteLater()
            # Let the newly visible screen refresh its content
            current = self._history[-1]
            if hasattr(current, "on_resume"):
                current.on_resume()

    def go_home(self, language: str):
        """Clear the stack and go to the home screen for a language."""
        self._clear_history()
        from ui.home_screen import HomeScreen
        self._push(HomeScreen(self, language))

    def go_to_start(self):
        """Clear the stack and return to the start / deck-selection screen."""
        self._clear_history()
        self._show_start()