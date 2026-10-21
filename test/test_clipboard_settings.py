import sys
import unittest
import warnings
from pathlib import Path
from tempfile import TemporaryDirectory
from types import ModuleType
from unittest.mock import Mock, patch

import yaml
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox

from hydra_tiff_meta_reader.window import MainWindow


class TestClipboardAndSettings(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        warnings.simplefilter('ignore', category=Warning)
        self.tmpdir = TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)

        settings_path = str(Path(self.tmpdir.name) / 'settings.ini')
        settings_patcher = patch(
            'hydra_tiff_meta_reader.window.QSettings',
            side_effect=lambda *args: QSettings(settings_path, QSettings.IniFormat),
        )
        settings_patcher.start()
        self.addCleanup(settings_patcher.stop)

        self.hydra = ModuleType('squirrel.library.hydra')
        self.hydra.HYDRA_METADATA_FIELDS = {
            'pixel_size_x': {'unit': 'nm'},
            'stage_x': {'unit': 'm'},
        }
        self.hydra.HYDRA_METADATA_PRESETS = {
            'resolution': ('pixel_size_x',),
        }
        self.hydra.read_hydra_metadata = Mock(return_value={'Metadata': {}})
        self.hydra.extract_hydra_metadata = Mock(side_effect=self._extract)
        self.modules = patch.dict(sys.modules, {
            'squirrel': ModuleType('squirrel'),
            'squirrel.library': ModuleType('squirrel.library'),
            'squirrel.library.hydra': self.hydra,
        })
        self.modules.start()
        self.addCleanup(self.modules.stop)

        self.window = MainWindow()
        self.addCleanup(self.window.close)

    def _extract(self, filepath, fields=None):
        return {field: {'value': 7.0, 'unit': 'nm'} for field in fields or []}

    def test_copy_button_disabled_before_load(self):
        print('Testing copy_yaml_to_clipboard: disabled before TIFF load')
        self.assertFalse(self.window.copy_button.isEnabled())
        self.assertFalse(self.window.copy_yaml_to_clipboard())

    def test_copy_yaml_uses_current_fields(self):
        print('Testing copy_yaml_to_clipboard: copies current fields as YAML')
        self.assertTrue(self.window.load_tiff('sample.tif'))
        self.window.field_checks['stage_x'].setChecked(True)

        self.assertTrue(self.window.copy_yaml_to_clipboard())

        metadata = yaml.safe_load(QApplication.clipboard().text())
        self.assertEqual(list(metadata), ['pixel_size_x', 'stage_x'])
        self.hydra.extract_hydra_metadata.assert_called_with(
            'sample.tif', fields=['pixel_size_x', 'stage_x'],
        )

    def test_copy_empty_selection_warns_and_preserves_clipboard(self):
        print('Testing copy_yaml_to_clipboard: empty selection warns')
        self.window.load_tiff('sample.tif')
        self.window.preset_combo.setCurrentIndex(0)

        QApplication.clipboard().setText('previous')
        with patch.object(QMessageBox, 'warning') as warning:
            self.assertFalse(self.window.copy_yaml_to_clipboard())
        warning.assert_called_once()
        self.assertEqual(QApplication.clipboard().text(), 'previous')

    def test_copy_failure_preserves_clipboard(self):
        print('Testing copy_yaml_to_clipboard: extraction errors are handled')
        self.window.load_tiff('sample.tif')
        self.hydra.extract_hydra_metadata.side_effect = ValueError('bad field')

        QApplication.clipboard().setText('previous')
        with patch.object(QMessageBox, 'critical') as critical:
            self.assertFalse(self.window.copy_yaml_to_clipboard())
        critical.assert_called_once()
        self.assertEqual(QApplication.clipboard().text(), 'previous')

    def test_last_directory_is_remembered(self):
        print('Testing open_tiff_dialog: remembers last opened directory')
        filepath = str(Path(self.tmpdir.name) / 'image.tif')
        self.assertTrue(self.window.load_tiff(filepath))
        self.window.close()
        other_window = MainWindow()
        self.addCleanup(other_window.close)

        with patch.object(QFileDialog, 'getOpenFileName', return_value=('', '')) as dialog:
            other_window.open_tiff_dialog()
        self.assertEqual(dialog.call_args.args[2], str(Path(filepath).parent))

    def test_failed_load_does_not_change_last_directory(self):
        print('Testing load_tiff: failed loads do not overwrite last directory')
        filepath = str(Path(self.tmpdir.name) / 'image.tif')
        self.assertTrue(self.window.load_tiff(filepath))
        self.hydra.read_hydra_metadata.side_effect = ValueError('bad TIFF')

        with patch.object(QMessageBox, 'critical'):
            self.assertFalse(self.window.load_tiff('/other/invalid.tif'))
        self.assertEqual(
            self.window.settings.value('last_tiff_directory'),
            str(Path(filepath).parent),
        )
