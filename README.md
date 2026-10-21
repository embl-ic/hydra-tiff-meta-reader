# Hydra TIFF Metadata Reader

A lightweight, cross-platform GUI application for viewing and exporting metadata
from Hydra SEM TIFF files, powered by the
[squirrel](https://github.com/embl-ic/squirrel) Python package.

## Development setup

Use Python 3.10 or newer. From the repository root:

```bash
python -m pip install -e '.[dev]'
```

Start the initial (empty) application window:

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

Metadata extraction and export functionality will be added in later updates.

## License

MIT. See [LICENSE](LICENSE).
