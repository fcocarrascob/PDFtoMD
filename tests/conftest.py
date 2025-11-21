"""Pytest configuration to ensure local packages are importable."""

import sys
from pathlib import Path

# Add project root to sys.path so "notebook" and "converter" resolve correctly.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
