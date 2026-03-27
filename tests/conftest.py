"""
Pytest configuration for cv-generator tests.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def fixtures_dir():
    """Return path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def templates_dir():
    """Return path to templates directory."""
    return Path(__file__).parent.parent / "templates"
