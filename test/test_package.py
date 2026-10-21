import unittest
import warnings
from unittest.mock import patch


class TestPackage(unittest.TestCase):

    def setUp(self):
        warnings.simplefilter('ignore', category=Warning)

    def test_package_import(self):
        print('Testing package: package can be imported')
        import hydra_tiff_meta_reader

        self.assertIsNotNone(hydra_tiff_meta_reader)

    def test_main_window_title(self):
        print('Testing MainWindow: initial window title')
        from PySide6.QtWidgets import QApplication
        from hydra_tiff_meta_reader.window import MainWindow

        app = QApplication.instance() or QApplication([])
        window = MainWindow()
        self.assertEqual(window.windowTitle(), 'Hydra TIFF Metadata Reader')
        window.close()
        self.assertIsNotNone(app)

    def test_application_entry_point(self):
        print('Testing main: application creates and shows a window')
        from hydra_tiff_meta_reader import app

        with patch.object(app, 'QApplication') as application:
            with patch.object(app, 'MainWindow') as main_window:
                application.instance.return_value = None
                application.return_value.exec.return_value = 0

                self.assertEqual(app.main(), 0)
                main_window.return_value.show.assert_called_once_with()
