"""Pytest configuration and fixtures."""
import sys
from pathlib import Path
from unittest.mock import MagicMock

# Add src directory to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Mock tkinter for CI environments where it's not available
try:
    import tkinter
except ModuleNotFoundError:
    sys.modules['tkinter'] = MagicMock()
    sys.modules['tkinter.ttk'] = MagicMock()
