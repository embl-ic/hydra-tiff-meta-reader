"""Main window for inspecting Hydra SEM TIFF metadata."""

from pathlib import Path

from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFileDialog, QGroupBox, QHBoxLayout, QLabel,
    QMainWindow, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem,
    QTabWidget, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget
)
from PySide6.QtCore import QSignalBlocker


class MainWindow(QMainWindow):
    """Open a Hydra TIFF file and inspect raw or selected metadata."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Hydra TIFF Metadata Reader')
        self.resize(900, 600)
        self.current_filepath = None

        self.open_button = QPushButton('Open TIFF…')
        self.open_button.clicked.connect(self.open_tiff_dialog)

        self.export_button = QPushButton('Export YAML…')
        self.export_button.setEnabled(False)
        self.export_button.clicked.connect(self.export_yaml_dialog)

        self.file_label = QLabel('No TIFF file selected')
        self.metadata_tree = QTreeWidget()
        self.metadata_tree.setHeaderLabels(['Metadata', 'Value'])
        self.metadata_tree.setAlternatingRowColors(True)

        self.preset_combo = QComboBox()
        self.preset_combo.addItem('No preset', None)
        self.field_checks = {}
        self.named_table = QTableWidget(0, 3)
        self.named_table.setHorizontalHeaderLabels(['Field', 'Value', 'Unit'])
        self.named_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.named_table.horizontalHeader().setStretchLastSection(True)

        self.selection_layout = QVBoxLayout()
        self.selection_layout.addWidget(QLabel('Preset'))
        self.selection_layout.addWidget(self.preset_combo)
        self.selection_layout.addWidget(QLabel('Fields'))
        self.selection_layout.addStretch()
        selection_box = QGroupBox('Selection')
        selection_box.setLayout(self.selection_layout)

        named_layout = QHBoxLayout()
        named_layout.addWidget(selection_box, 1)
        named_layout.addWidget(self.named_table, 3)
        named_widget = QWidget()
        named_widget.setLayout(named_layout)

        self.tabs = QTabWidget()
        self.tabs.addTab(self.metadata_tree, 'Complete metadata')
        self.tabs.addTab(named_widget, 'Selected metadata')

        layout = QVBoxLayout()
        buttons = QHBoxLayout()
        buttons.addWidget(self.open_button)
        buttons.addWidget(self.export_button)

        layout.addLayout(buttons)
        layout.addWidget(self.file_label)
        layout.addWidget(self.tabs)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.preset_combo.currentIndexChanged.connect(self._apply_preset)

    def open_tiff_dialog(self):
        """Ask the user for a TIFF file and load its metadata."""
        filepath, _ = QFileDialog.getOpenFileName(
            self, 'Open Hydra TIFF', '', 'TIFF files (*.tif *.tiff);;All files (*)'
        )
        if filepath:
            self.load_tiff(filepath)

    def load_tiff(self, filepath):
        """Read metadata using squirrel, preserving the display on errors."""
        try:
            from squirrel.library.hydra import (
                HYDRA_METADATA_FIELDS, HYDRA_METADATA_PRESETS,
                extract_hydra_metadata, read_hydra_metadata,
            )

            metadata = read_hydra_metadata(filepath)
            self._populate_selection_controls(
                HYDRA_METADATA_FIELDS, HYDRA_METADATA_PRESETS
            )
            selected = extract_hydra_metadata(
                filepath, fields=self._checked_fields(),
            )
        except Exception as error:
            QMessageBox.critical(self, 'Unable to read Hydra TIFF', str(error))
            return False

        self.metadata_tree.clear()
        self._add_metadata_items(self.metadata_tree.invisibleRootItem(), metadata)
        self.metadata_tree.expandToDepth(0)
        self._show_named_metadata(selected)
        self.current_filepath = str(Path(filepath))
        self.export_button.setEnabled(True)
        self.file_label.setText(self.current_filepath)
        return True

    def export_yaml_dialog(self):
        """Export the current named-field selection using squirrel."""
        if self.current_filepath is None:
            return False

        default_path = str(Path(self.current_filepath).with_suffix('.yaml'))
        filepath, _ = QFileDialog.getSaveFileName(
            self, 'Export selected metadata', default_path,
            'YAML files (*.yaml *.yml);;All files (*)',
        )
        if not filepath:
            return False

        try:
            from squirrel.library.hydra import (
                extract_hydra_metadata, save_hydra_metadata,
            )

            metadata = extract_hydra_metadata(
                self.current_filepath, fields=self._checked_fields(),
            )
            if not metadata:
                QMessageBox.warning(
                    self, 'No metadata selected',
                    'Choose a preset or at least one field before exporting.',
                )
                return False

            save_hydra_metadata(metadata, filepath)
        except Exception as error:
            QMessageBox.critical(self, 'Unable to export YAML', str(error))
            return False

        return True

    def _populate_selection_controls(self, fields, presets):
        """Build controls from squirrel's supported fields and presets."""
        if self.field_checks:
            return

        self.preset_combo.blockSignals(True)
        for preset in presets:
            self.preset_combo.addItem(preset, preset)
        index = self.preset_combo.findData('resolution')
        if index >= 0:
            self.preset_combo.setCurrentIndex(index)
        self.preset_combo.blockSignals(False)

        for field in fields:
            checkbox = QCheckBox(field)
            checkbox.toggled.connect(self._field_toggled)
            self.selection_layout.insertWidget(
                self.selection_layout.count() - 1, checkbox
            )
            self.field_checks[field] = checkbox

        self._presets = presets
        self._apply_preset()

    def _apply_preset(self, *_):
        """Check exactly the fields defined by the selected preset."""
        selected = set(self._presets.get(self.preset_combo.currentData(), ()))
        for name, checkbox in self.field_checks.items():
            with QSignalBlocker(checkbox):
                checkbox.setChecked(name in selected)
        self.refresh_selected_metadata()

    def _field_toggled(self, *_):
        """Treat any manual checkbox change as a custom selection."""
        with QSignalBlocker(self.preset_combo):
            self.preset_combo.setCurrentIndex(0)
        self.refresh_selected_metadata()

    def _checked_fields(self):
        return [name for name, checkbox in self.field_checks.items()
                if checkbox.isChecked()]

    def refresh_selected_metadata(self, *_):
        """Re-extract selected fields from the current TIFF file."""
        if self.current_filepath is None:
            return

        try:
            from squirrel.library.hydra import extract_hydra_metadata

            selected = extract_hydra_metadata(
                self.current_filepath, fields=self._checked_fields(),
            )
        except Exception as error:
            QMessageBox.critical(self, 'Unable to extract metadata', str(error))
            return

        self._show_named_metadata(selected)

    def _show_named_metadata(self, metadata):
        self.named_table.setRowCount(len(metadata))
        for row, (field, details) in enumerate(metadata.items()):
            value = details['value']
            for column, text in enumerate((
                field, '' if value is None else str(value), details['unit']
            )):
                self.named_table.setItem(row, column, QTableWidgetItem(text))

    def _add_metadata_items(self, parent, data):
        """Recursively render nested dictionaries and repeated XML elements."""
        if isinstance(data, dict):
            for key, value in data.items():
                item = QTreeWidgetItem(parent, [str(key), ''])
                self._add_metadata_items(item, value)
        elif isinstance(data, list):
            for index, value in enumerate(data):
                item = QTreeWidgetItem(parent, [f'[{index}]', ''])
                self._add_metadata_items(item, value)
        else:
            parent.setText(1, '' if data is None else str(data))
