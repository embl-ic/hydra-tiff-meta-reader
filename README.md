# Hydra TIFF Metadata Reader

A lightweight, cross-platform GUI application for viewing and exporting metadata
from Hydra SEM TIFF files, powered by the
[squirrel](https://github.com/embl-ic/squirrel) Python package.

## Development setup

Use Python 3.10 or newer. From the repository root:

```bash
python -m pip install -e '.[dev,hydra]'
```

Start the application:

```bash
hydra-tiff-meta-reader
```

Alternatively:

```bash
python -m hydra_tiff_meta_reader
```

Run the tests:

```bash
python -m pytest test/ -v -s
```

## Inspecting metadata

Click **Open TIFF…** and select a Hydra SEM TIFF file. The application uses
`squirrel.library.hydra.read_hydra_metadata` to display the complete metadata
hierarchy in an expandable tree. Invalid files produce an error dialog without
clearing the previously displayed metadata.

The `hydra` installation extra installs squirrel from its `hydra-dev` branch.
The application can launch without squirrel, but opening TIFF files requires it.
The **Selected metadata** tab is shown first and opens by default. It provides
squirrel's named metadata fields with values and units. The `resolution` preset is selected by default; switch to
`geometry` or `No preset`. Choosing a preset checks its fields automatically;
changing any checkbox switches to `No preset` while preserving the current
field selection. The selection controls appear beside the metadata table. Missing
values appear as blank cells. The **Complete metadata** tab continues to show
the original XML hierarchy.

To export the current selection, click **Export YAML…** and choose a destination.
The application re-extracts the active preset and checked fields, then uses
`squirrel.library.hydra.save_hydra_metadata` to write the YAML file. The button
is available after opening a TIFF file. Canceling the dialog writes nothing;
exporting with no fields selected displays a warning. Missing field values
are retained as `null` in the YAML output.

## License

MIT. See [LICENSE](LICENSE).

## Windows executable

Windows builds use PyInstaller and include the Python runtime, PySide6, and
squirrel. Users do not need to install Python.

Open **Actions → Windows executable → Run workflow** on GitHub to build a
Windows distribution. Pushing a tag starting with `v` also triggers a build.
Download the `HydraTiffMetaReader-windows` artifact from the workflow run,
extract the ZIP, and run `HydraTiffMetaReader.exe` inside the extracted folder.
Keep the other files alongside the executable.

To build locally **on Windows** (PyInstaller cannot cross-compile from Linux):

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev,hydra,build]"
python -m pytest test/ -v -s
python -m PyInstaller --noconfirm --clean packaging/HydraTiffMetaReader.spec
```

The output is in `dist/HydraTiffMetaReader/`. This is a *one-folder* build.
The `hydra` extra installs squirrel from the `0.5.9` Git tag at build
time, rather than from a moving development branch. For fully immutable
builds, pin the corresponding Git commit SHA. Test the
Windows executable with a real Hydra TIFF, including YAML export. Unsigned
builds may trigger Windows SmartScreen warnings.
