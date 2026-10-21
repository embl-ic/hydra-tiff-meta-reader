"""Regression tests for required squirrel dependency and install commands."""

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TestDependencyConfiguration(unittest.TestCase):

    def test_squirrel_is_required(self):
        print('Testing project dependencies: squirrel is required')

        content = (ROOT / 'pyproject.toml').read_text(encoding='utf-8')
        required = content.split('[project.optional-dependencies]')[0]
        optional = content.split('[project.optional-dependencies]')[1]

        self.assertIn(
            'squirrel @ git+https://github.com/embl-ic/squirrel.git@0.5.9',
            required,
        )
        self.assertNotRegex(optional, r'(?m)^hydra\s*=')

    def test_windows_workflow_uses_required_dependencies(self):
        print('Testing Windows workflow: no obsolete hydra extra')

        content = (ROOT / '.github/workflows/windows-build.yml').read_text(
            encoding='utf-8',
        )
        self.assertIn('".[dev,build]"', content)
        self.assertNotIn('dev,hydra', content)

    def test_readme_installation_is_current(self):
        print('Testing README: installation instructions use required squirrel')

        content = (ROOT / 'README.md').read_text(encoding='utf-8')
        self.assertIn("python -m pip install -e '.[dev]'", content)
        self.assertNotIn('hydra-dev', content)
        self.assertNotIn('dev,hydra', content)
        self.assertNotIn('`hydra` extra', content)


if __name__ == '__main__':
    unittest.main()
