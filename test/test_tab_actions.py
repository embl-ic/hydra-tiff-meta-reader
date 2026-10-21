import sys
import unittest
from types import ModuleType
from unittest.mock import Mock, patch

import yaml
from PySide6.QtWidgets import QApplication, QFileDialog

from hydra_tiff_meta_reader.window import MainWindow


class TestActiveTabActions(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.raw = {'Metadata': {'BinaryResult': {'PixelSize': {'X': '7e-9'}}}}
        self.selected = {'pixel_size_x': {'value': 7.0, 'unit': 'nm'}}
        self.hydra = ModuleType('squirrel.library.hydra')
        self.hydra.HYDRA_METADATA_FIELDS = {'pixel_size_x': {'unit': 'nm'}}
        self.hydra.HYDRA_METADATA_PRESETS = {'resolution': ('pixel_size_x',)}
        self.hydra.read_hydra_metadata = Mock(return_value=self.raw)
        self.hydra.extract_hydra_metadata = Mock(return_value=self.selected)
        self.hydra.save_hydra_metadata = Mock()
        modules = patch.dict(sys.modules, {
            'squirrel': ModuleType('squirrel'),
            'squirrel.library': ModuleType('squirrel.library'),
            'squirrel.library.hydra': self.hydra,
        })
        modules.start()
        self.addCleanup(modules.stop)

        self.window = MainWindow()
        self.addCleanup(self.window.close)
        self.assertTrue(self.window.load_tiff('sample.tif'))

    def test_copy_metadata_follows_active_tab(self):
        print('Testing copy_yaml_to_clipboard: copies active tab metadata')
        for index, expected in ((0, self.selected), (1, self.raw),
                                (0, self.selected)):
            with self.subTest(tab=index):
                self.window.tabs.setCurrentIndex(index)
                self.assertTrue(self.window.copy_yaml_to_clipboard())
                self.assertEqual(yaml.safe_load(QApplication.clipboard().text()),
                                 expected)

    def test_export_metadata_follows_active_tab(self):
        print('Testing export_yaml_dialog: exports active tab metadata')
        with patch.object(QFileDialog, 'getSaveFileName',
                          return_value=('output.yaml', '')):
            for index, expected in ((0, self.selected), (1, self.raw)):
                with self.subTest(tab=index):
                    self.window.tabs.setCurrentIndex(index)
                    self.assertTrue(self.window.export_yaml_dialog())
                    self.hydra.save_hydra_metadata.assert_called_with(
                        expected, 'output.yaml')

    def test_complete_metadata_ignores_empty_field_selection(self):
        print('Testing metadata actions: full view ignores unchecked fields')
        self.window.preset_combo.setCurrentIndex(0)
        self.window.tabs.setCurrentIndex(1)
        self.assertTrue(self.window.copy_yaml_to_clipboard())
        self.assertEqual(yaml.safe_load(QApplication.clipboard().text()),
                         self.raw)
