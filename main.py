import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from ui.app_window import AppWindow


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")          # consistent cross-platform base style
    app.setApplicationName("Flashcards")

    window = AppWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()