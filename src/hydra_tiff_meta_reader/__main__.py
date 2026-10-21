"""Allow launching the application with ``python -m hydra_tiff_meta_reader``."""

from hydra_tiff_meta_reader.app import main


if __name__ == '__main__':
    raise SystemExit(main())
