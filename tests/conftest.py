"""Shared fixtures: the directory of input/expected fixture pairs."""
from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"
Z = "\u200c"  # ZWNJ


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES
