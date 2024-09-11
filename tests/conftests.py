"""
Register pytest plugins, fixtures, and hooks to be used during test execution.

Docs: https://stackoverflow.com/questions/34466027/in-pytest-what-is-the-use-of-conftest-py-files
"""

import sys
from pathlib import Path

THIS_DIR = Path(__file__).parent

TESTS_DIR_PARENT = (THIS_DIR / "..").resolve()

sys.path.insert(0, str(TESTS_DIR_PARENT))

pytest_plugins = [
    "tests.fixtures.example_fixture",
]
