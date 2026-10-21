import unittest
import warnings
from unittest.mock import Mock, patch
from types import ModuleType
import sys

from PySide6.QtCore import QMimeData, QUrl
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox

from hydra_tiff_meta_reader.window import MainWindow


class TestMainWindow(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        warnings.simplefilter('ignore', category=Warning)
        self.window = MainWindow()
        self.addCleanup(self.window.close)

    def test_initial_state(self):
        print('Testing MainWindow: initial metadata display is empty')
        self.assertEqual(self.window.metadata_tree.topLevelItemCount(), 0)
        self.assertEqual(self.window.file_label.text(), 'No TIFF file selected')

    def test_metadata_tree_default_column_width(self):
        print('Testing MainWindow: metadata column is wide by default')
        self.assertEqual(self.window.metadata_tree.columnWidth(0), 300)

    def _mock_reader(self, **kwargs):
        module = ModuleType('squirrel.library.hydra')
        from unittest.mock import Mock
        module.read_hydra_metadata = Mock(**kwargs)
        module.extract_hydra_metadata = Mock(return_value={})
        module.HYDRA_METADATA_FIELDS = {'pixel_size_x': {'unit': 'nm'}}
        module.HYDRA_METADATA_PRESETS = {'resolution': ('pixel_size_x',)}
        return patch.dict(sys.modules, {'squirrel': ModuleType('squirrel'),
                                        'squirrel.library': ModuleType('squirrel.library'),
                                        'squirrel.library.hydra': module})

    def test_load_tiff_nested_metadata(self):
        print('Testing load_tiff: nested and repeated metadata elements')
        metadata = {'Metadata': {'PixelSize': {'X': '7e-9'},
                                 'Item': ['first', 'second'], 'Empty': None}}
        with self._mock_reader(return_value=metadata):
            self.assertTrue(self.window.load_tiff('/tmp/example.tif'))

        root = self.window.metadata_tree.topLevelItem(0)
        self.assertEqual(root.text(0), 'Metadata')
        pixel_size = root.child(0)
        self.assertEqual(pixel_size.child(0).text(1), '7e-9')
        repeated = root.child(1)
        self.assertEqual(repeated.child(0).text(0), '[0]')
        self.assertEqual(repeated.child(1).text(1), 'second')
        self.assertEqual(root.child(2).text(1), '')
        self.assertEqual(self.window.file_label.text(), '/tmp/example.tif')

    def test_load_tiff_failure_keeps_previous_display(self):
        print('Testing load_tiff: errors leave previous metadata visible')
        self.window.file_label.setText('previous.tif')
        with self._mock_reader(side_effect=ValueError('Missing tag')):
            with patch.object(QMessageBox, 'critical') as show_error:
                self.assertFalse(self.window.load_tiff('invalid.tif'))

        show_error.assert_called_once()
        self.assertEqual(self.window.file_label.text(), 'previous.tif')

    def test_open_tiff_dialog_cancel(self):
        print('Testing open_tiff_dialog: cancel does not load a file')
        with patch.object(QFileDialog, 'getOpenFileName', return_value=('', '')):
            with patch.object(self.window, 'load_tiff') as load:
                self.window.open_tiff_dialog()
        load.assert_not_called()

    def test_open_tiff_dialog_selection(self):
        print('Testing open_tiff_dialog: selected path is loaded')
        with patch.object(QFileDialog, 'getOpenFileName',
                          return_value=('selected.tif', 'TIFF files')):
            with patch.object(self.window, 'load_tiff') as load:
                self.window.open_tiff_dialog()
        load.assert_called_once_with('selected.tif')

    def _drop_event(self, paths):
        mime_data = QMimeData()
        mime_data.setUrls([QUrl.fromLocalFile(path) for path in paths])
        event = Mock()
        event.mimeData.return_value = mime_data
        return event

    def test_drag_enter_accepts_tiff(self):
        print('Testing dragEnterEvent: accept local TIFF files')
        for path in ('/tmp/sample.tif', '/tmp/sample.TIFF'):
            with self.subTest(path=path):
                event = self._drop_event([path])
                self.window.dragEnterEvent(event)
                event.acceptProposedAction.assert_called_once_with()
                event.ignore.assert_not_called()

    def test_drag_enter_rejects_other_files_and_multiple_files(self):
        print('Testing dragEnterEvent: reject unsupported drops')
        for paths in ([], ['/tmp/sample.png'],
                      ['/tmp/a.tif', '/tmp/b.tif']):
            with self.subTest(paths=paths):
                event = self._drop_event(paths)
                self.window.dragEnterEvent(event)
                event.ignore.assert_called_once_with()
                event.acceptProposedAction.assert_not_called()

    def test_drop_tiff_loads_metadata(self):
        print('Testing dropEvent: dropped TIFF is loaded')
        event = self._drop_event(['/tmp/sample.tif'])
        with patch.object(self.window, 'load_tiff', return_value=True) as load:
            self.window.dropEvent(event)
        load.assert_called_once_with('/tmp/sample.tif')
        event.acceptProposedAction.assert_called_once_with()

    def test_drop_invalid_file_is_ignored(self):
        print('Testing dropEvent: non-TIFF files are ignored')
        event = self._drop_event(['/tmp/sample.txt'])
        with patch.object(self.window, 'load_tiff') as load:
            self.window.dropEvent(event)
        load.assert_not_called()
        event.ignore.assert_called_once_with()

    def test_drag_move_accepts_tiff(self):
        print('Testing dragMoveEvent: keep TIFF drag accepted')
        event = self._drop_event(['/tmp/sample.tiff'])
        self.window.dragMoveEvent(event)
        event.acceptProposedAction.assert_called_once_with()
