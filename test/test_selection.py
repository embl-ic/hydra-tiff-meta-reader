import sys
import unittest
import warnings
from types import ModuleType
from unittest.mock import Mock, patch

from PySide6.QtWidgets import QApplication, QMessageBox

from hydra_tiff_meta_reader.window import MainWindow


class TestMetadataSelection(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        warnings.simplefilter('ignore', category=Warning)
        self.window = MainWindow()
        self.addCleanup(self.window.close)

        self.module = ModuleType('squirrel.library.hydra')
        self.module.HYDRA_METADATA_FIELDS = {
            'pixel_size_x': {'unit': 'nm'},
            'slice_thickness': {'unit': 'nm'},
            'stage_x': {'unit': 'm'},
        }
        self.module.HYDRA_METADATA_PRESETS = {
            'resolution': ('pixel_size_x', 'slice_thickness'),
            'geometry': ('pixel_size_x', 'stage_x'),
        }
        self.module.read_hydra_metadata = Mock(return_value={'Metadata': {}})
        self.module.extract_hydra_metadata = Mock(side_effect=self._extract)
        self.modules = patch.dict(sys.modules, {
            'squirrel': ModuleType('squirrel'),
            'squirrel.library': ModuleType('squirrel.library'),
            'squirrel.library.hydra': self.module,
        })
        self.modules.start()
        self.addCleanup(self.modules.stop)

    def _extract(self, filepath, preset=None, fields=None):
        selected = list(self.module.HYDRA_METADATA_PRESETS.get(preset, ()))
        selected.extend(fields or [])
        return {field: {'value': None if field == 'stage_x' else 7.0,
                        'unit': self.module.HYDRA_METADATA_FIELDS[field]['unit']}
                for field in dict.fromkeys(selected)}

    def test_selection_controls_stay_at_top(self):
        print('Testing metadata selection: controls stay above bottom spacer')
        self.assertTrue(self.window.load_tiff('sample.tif'))
        layout = self.window.selection_layout
        self.assertTrue(layout.itemAt(layout.count() - 1).spacerItem())
        for checkbox in self.window.field_checks.values():
            index = layout.indexOf(checkbox)
            self.assertGreaterEqual(index, 0)
            self.assertLess(index, layout.count() - 1)

    def test_selected_metadata_is_default_tab(self):
        print('Testing metadata selection: selected metadata is first and active')
        self.assertEqual(self.window.tabs.tabText(0), 'Selected metadata')
        self.assertEqual(self.window.tabs.tabText(1), 'Complete metadata')
        self.assertEqual(self.window.tabs.currentIndex(), 0)

    def test_default_resolution_selection(self):
        print('Testing metadata selection: resolution preset on load')
        self.assertTrue(self.window.load_tiff('sample.tif'))
        self.assertEqual(self.window.preset_combo.currentData(), 'resolution')
        self.assertTrue(self.window.field_checks['pixel_size_x'].isChecked())
        self.assertTrue(self.window.field_checks['slice_thickness'].isChecked())
        self.assertFalse(self.window.field_checks['stage_x'].isChecked())
        self.assertEqual(self.window.named_table.rowCount(), 2)
        self.assertEqual(self.window.named_table.item(0, 0).text(), 'pixel_size_x')
        self.assertEqual(self.window.named_table.item(0, 1).text(), '7.0')
        self.assertEqual(self.window.named_table.item(0, 2).text(), 'nm')

    def test_custom_fields_and_missing_values(self):
        print('Testing metadata selection: additional fields and missing values')
        self.window.load_tiff('sample.tif')
        self.window.field_checks['stage_x'].setChecked(True)
        self.assertIsNone(self.window.preset_combo.currentData())
        self.assertEqual(self.window.named_table.rowCount(), 3)
        self.assertEqual(self.window.named_table.item(2, 0).text(), 'stage_x')
        self.assertEqual(self.window.named_table.item(2, 1).text(), '')
        self.assertEqual(self.window.named_table.item(2, 2).text(), 'm')

    def test_preset_change_and_no_preset(self):
        print('Testing metadata selection: switching presets and no preset')
        self.window.load_tiff('sample.tif')
        self.window.preset_combo.setCurrentIndex(
            self.window.preset_combo.findData('geometry')
        )
        self.assertEqual(self.window.named_table.rowCount(), 2)
        self.assertTrue(self.window.field_checks['stage_x'].isChecked())
        self.assertFalse(self.window.field_checks['slice_thickness'].isChecked())
        self.window.preset_combo.setCurrentIndex(0)
        self.assertEqual(self.window.named_table.rowCount(), 0)
        self.window.field_checks['slice_thickness'].setChecked(True)
        self.assertEqual(self.window.named_table.rowCount(), 1)

    def test_selection_error_preserves_table(self):
        print('Testing metadata selection: extraction failure preserves table')
        self.window.load_tiff('sample.tif')
        self.module.extract_hydra_metadata.side_effect = ValueError('Invalid value')
        with patch.object(QMessageBox, 'critical') as show_error:
            self.window.field_checks['stage_x'].setChecked(True)
        show_error.assert_called_once()
        self.assertEqual(self.window.named_table.rowCount(), 2)

    def test_unchecking_preset_field_switches_to_custom(self):
        print('Testing metadata selection: unchecking a preset field')
        self.window.load_tiff('sample.tif')
        self.window.field_checks['pixel_size_x'].setChecked(False)
        self.assertIsNone(self.window.preset_combo.currentData())
        self.assertEqual(self.window.named_table.rowCount(), 1)
        self.assertEqual(self.window.named_table.item(0, 0).text(),
                         'slice_thickness')

    def test_reselecting_preset_restores_exact_checkboxes(self):
        print('Testing metadata selection: reselecting a preset')
        self.window.load_tiff('sample.tif')
        self.window.field_checks['stage_x'].setChecked(True)
        self.window.preset_combo.setCurrentIndex(
            self.window.preset_combo.findData('resolution')
        )
        self.assertEqual(self.window._checked_fields(),
                         ['pixel_size_x', 'slice_thickness'])
        self.assertEqual(self.window.named_table.rowCount(), 2)

    def test_selection_panel_precedes_display(self):
        print('Testing metadata selection: side-by-side layout')
        named_widget = self.window.tabs.widget(0)
        layout = named_widget.layout()
        self.assertEqual(layout.itemAt(0).widget().title(), 'Selection')
        self.assertIs(layout.itemAt(1).widget(), self.window.named_table)
