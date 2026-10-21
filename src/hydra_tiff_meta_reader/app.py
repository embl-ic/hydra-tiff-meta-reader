"""Application entry point."""

import sys

from PySide6.QtWidgets import QApplication

from hydra_tiff_meta_reader.window import MainWindow


def main():
    """Launch the initial empty application window."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    window = MainWindow()
    window.show()
    return app.exec()
