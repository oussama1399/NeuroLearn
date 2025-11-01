import sys
from pathlib import Path

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication
from dotenv import load_dotenv

from ui.MainWindow import MainWindow


def main() -> None:
    load_dotenv()

    app = QApplication(sys.argv)
    app.setApplicationName("NeuroLearn")

    # Use image.png as logo if present
    logo_path = Path(__file__).resolve().parent / "image.png"
    if logo_path.exists():
        app.setWindowIcon(QIcon(str(logo_path)))
    else:
        icon_path = Path(__file__).resolve().parent / "assets" / "app_icon.png"
        if icon_path.exists():
            app.setWindowIcon(QIcon(str(icon_path)))

    style_path = Path(__file__).resolve().parent / "style.qss"
    if style_path.exists():
        app.setStyleSheet(style_path.read_text(encoding="utf-8"))

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
