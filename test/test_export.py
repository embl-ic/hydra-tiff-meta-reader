import sys
import unittest
import warnings
from types import ModuleType
from unittest.mock import Mock, patch

from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox

from hydra_tiff_meta_reader.window import MainWindow


class TestYamlExport(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        warnings.simplefilter('ignore', category=Warning)
        self.window = MainWindow()
        self.addCleanup(self.window.close)

        self.hydra = ModuleType('squirrel.library.hydra')
        self.hydra.HYDRA_METADATA_FIELDS = {
            'pixel_size_x': {'unit': 'nm'},
            'stage_x': {'unit': 'm'},
        }
        self.hydra.HYDRA_METADATA_PRESETS = {
            'resolution': ('pixel_size_x',),
        }
        self.hydra.read_hydra_metadata = Mock(return_value={'Metadata': {}})
        self.hydra.extract_hydra_metadata = Mock(return_value={
            'pixel_size_x': {'value': 7.0, 'unit': 'nm'},
        })
        self.hydra.save_hydra_metadata = Mock()
        modules = patch.dict(sys.modules, {
            'squirrel': ModuleType('squirrel'),
            'squirrel.library': ModuleType('squirrel.library'),
            'squirrel.library.hydra': self.hydra,
        })
        modules.start()
        self.addCleanup(modules.stop)

    def test_export_yaml_initially_disabled(self):
        print('Testing export_yaml_dialog: disabled before loading TIFF')
        self.assertFalse(self.window.export_button.isEnabled())
        self.assertFalse(self.window.export_yaml_dialog())
        self.hydra.save_hydra_metadata.assert_not_called()

    def test_export_yaml_selected_metadata(self):
        print('Testing export_yaml_dialog: exports selected metadata')
        self.assertTrue(self.window.load_tiff('sample.tif'))
        self.assertTrue(self.window.export_button.isEnabled())
        self.window.field_checks['stage_x'].setChecked(True)

        with patch.object(QFileDialog, 'getSaveFileName', return_value=(
                'result.yaml', 'YAML files (*.yaml *.yml)')):
            self.assertTrue(self.window.export_yaml_dialog())

        self.hydra.extract_hydra_metadata.assert_called_with(
            'sample.tif', preset='resolution', fields=['stage_x'],
        )
        self.hydra.save_hydra_metadata.assert_called_once_with(
            {'pixel_size_x': {'value': 7.0, 'unit': 'nm'}}, 'result.yaml',
        )

    def test_export_yaml_cancel(self):
        print('Testing export_yaml_dialog: cancel writes no file')
        self.window.load_tiff('sample.tif')
        with patch.object(QFileDialog, 'getSaveFileName', return_value=('', '')):
            self.assertFalse(self.window.export_yaml_dialog())
        self.hydra.save_hydra_metadata.assert_not_called()

    def test_export_yaml_empty_selection(self):
        print('Testing export_yaml_dialog: empty selection shows warning')
        self.window.load_tiff('sample.tif')
        self.window.preset_combo.setCurrentIndex(0)
        self.hydra.extract_hydra_metadata.return_value = {}
        with patch.object(QFileDialog, 'getSaveFileName', return_value=(
                'result.yaml', '')):
            with patch.object(QMessageBox, 'warning') as warning:
                self.assertFalse(self.window.export_yaml_dialog())
        warning.assert_called_once()
        self.hydra.save_hydra_metadata.assert_not_called()

    def test_export_yaml_error(self):
        print('Testing export_yaml_dialog: save error shows dialog')
        self.window.load_tiff('sample.tif')
        self.hydra.save_hydra_metadata.side_effect = OSError('Disk full')
        with patch.object(QFileDialog, 'getSaveFileName', return_value=(
                'result.yaml', '')):
            with patch.object(QMessageBox, 'critical') as critical:
                self.assertFalse(self.window.export_yaml_dialog())
        self.assertIn('Disk full', critical.call_args.args[2])
