"""Tests for screenshot review and deletion dialog."""
import pytest
import tkinter as tk
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


def test_screenshot_review_dialog_instantiation():
    """Test that dialog can be instantiated with a mock database."""
    from syncopaid.screenshot_review_dialog import ScreenshotReviewDialog

    mock_db = MagicMock()
    mock_db.get_screenshots.return_value = []

    # Create root window for testing
    root = tk.Tk()
    root.withdraw()  # Hide window

    try:
        dialog = ScreenshotReviewDialog(root, mock_db)
        assert dialog is not None
        assert dialog.db == mock_db
    finally:
        root.destroy()
