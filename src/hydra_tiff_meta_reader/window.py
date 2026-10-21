"""Main application window; UI controls will be added later."""

from PySide6.QtWidgets import QMainWindow


class MainWindow(QMainWindow):
    """Empty window used as the starting point for the GUI."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Hydra TIFF Metadata Reader')
        self.resize(900, 600)
