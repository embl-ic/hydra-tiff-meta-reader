# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller configuration for the Windows desktop application."""

from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files


project_root = Path(SPECPATH).parent

analysis = Analysis(
    [str(project_root / 'src' / 'hydra_tiff_meta_reader' / '__main__.py')],
    pathex=[str(project_root / 'src')],
    binaries=[],
    datas=collect_data_files('squirrel'),
    hiddenimports=['squirrel.library.hydra'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(analysis.pure)
exe = EXE(
    pyz,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name='HydraTiffMetaReader',
    console=False,
)
coll = COLLECT(
    exe,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=False,
    name='HydraTiffMetaReader',
)
