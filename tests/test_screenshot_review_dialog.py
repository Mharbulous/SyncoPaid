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

    try:
        # Create root window for testing
        root = tk.Tk()
        root.withdraw()  # Hide window

        dialog = ScreenshotReviewDialog(root, mock_db)
        assert dialog is not None
        assert dialog.db == mock_db
    except tk.TclError:
        # Skip test if tkinter is not available (headless environment)
        pytest.skip("tkinter not available in headless environment")
    finally:
        try:
            root.destroy()
        except:
            pass


def test_show_creates_window():
    """Test that show() creates a Toplevel window."""
    from syncopaid.screenshot_review_dialog import ScreenshotReviewDialog

    mock_db = MagicMock()
    mock_db.get_screenshots.return_value = []

    try:
        root = tk.Tk()
        root.withdraw()

        dialog = ScreenshotReviewDialog(root, mock_db)
        dialog.show()

        assert dialog.window is not None
        assert dialog.window.winfo_exists()
    except tk.TclError:
        # Skip test if tkinter is not available (headless environment)
        pytest.skip("tkinter not available in headless environment")
    finally:
        try:
            if dialog.window:
                dialog.window.destroy()
            root.destroy()
        except:
            pass
