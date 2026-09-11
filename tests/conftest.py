"""Make the package and the test helpers importable, and register custom marks."""

import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "src"))
sys.path.insert(0, str(root / "tests"))


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: needs a real transcriber installed")
