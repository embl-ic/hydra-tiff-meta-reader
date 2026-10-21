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
The **Selected metadata** tab provides squirrel's named metadata fields with
values and units. The `resolution` preset is selected by default; switch to
`geometry` or `No preset` and optionally check additional fields. Missing
values appear as blank cells. The **Complete metadata** tab continues to show
the original XML hierarchy.

YAML export will be added in a later update.

## License

MIT. See [LICENSE](LICENSE).
