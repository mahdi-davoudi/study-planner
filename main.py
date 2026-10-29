"""Study Planner - application entry point."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from config import APP_NAME
from database import DatabaseManager
from gui.main_window import MainWindow
from gui.theme import apply_theme


def main() -> int:
    if sys.platform == "win32":  # give the app its own taskbar identity/icon
        try:
            import ctypes

            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "StudyPlanner.App"
            )
        except (AttributeError, OSError):
            pass

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    apply_theme(app)

    try:
        db = DatabaseManager()
    except ConnectionError as exc:
        QMessageBox.critical(None, "Database error", str(exc))
        return 1
    app.aboutToQuit.connect(db.close)

    window = MainWindow(db)
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
