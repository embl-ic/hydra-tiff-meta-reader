"""Tests for Windows packaging configuration."""

import unittest
import warnings
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TestWindowsPackaging(unittest.TestCase):

    def setUp(self):
        warnings.simplefilter('ignore', category=Warning)

    def test_pyinstaller_spec_compiles(self):
        print('Testing PyInstaller spec: Python syntax')
        source = (ROOT / 'packaging' / 'HydraTiffMetaReader.spec').read_text()
        compile(source, 'HydraTiffMetaReader.spec', 'exec')

    def test_pyinstaller_spec_bundles_squirrel(self):
        print('Testing PyInstaller spec: squirrel hidden import')
        source = (ROOT / 'packaging' / 'HydraTiffMetaReader.spec').read_text()
        self.assertIn("'squirrel.library.hydra'", source)
        self.assertIn('console=False', source)

    def test_windows_workflow_exists(self):
        print('Testing Windows workflow: build and upload steps')
        source = (ROOT / '.github' / 'workflows' / 'windows-build.yml').read_text()
        self.assertIn('windows-latest', source)
        self.assertIn('PyInstaller', source)
        self.assertIn('upload-artifact', source)

    def test_squirrel_dependency_uses_release_tag(self):
        print('Testing packaging dependency: squirrel release 0.5.9')
        source = (ROOT / 'pyproject.toml').read_text()
        self.assertIn('squirrel.git@0.5.9', source)
        self.assertNotIn('squirrel.git@hydra-dev', source)
