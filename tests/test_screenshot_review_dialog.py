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


def test_delete_selected_calls_secure_delete():
    """Test that delete calls database secure delete method."""
    from syncopaid.screenshot_review_dialog import ScreenshotReviewDialog

    mock_db = MagicMock()
    mock_db.get_screenshots.return_value = [
        {'id': 1, 'captured_at': '2025-12-23T10:00:00', 'file_path': '/path/1.jpg', 'window_title': 'Test1'},
        {'id': 2, 'captured_at': '2025-12-23T10:01:00', 'file_path': '/path/2.jpg', 'window_title': 'Test2'},
    ]
    mock_db.delete_screenshots_securely.return_value = 1

    root = tk.Tk()
    root.withdraw()

    try:
        dialog = ScreenshotReviewDialog(root, mock_db)
        dialog.show()

        # Mock listbox.curselection to return (0,) indicating first item is selected
        dialog.listbox.curselection = MagicMock(return_value=(0,))

        # Mock the confirmation dialog to return True
        with patch('tkinter.messagebox.askyesno', return_value=True), \
             patch('tkinter.messagebox.showinfo'):
            dialog._delete_selected()

        # Verify secure delete was called with correct ID
        mock_db.delete_screenshots_securely.assert_called_once_with([1])
    finally:
        if dialog.window:
            dialog.window.destroy()
        root.destroy()


def test_show_screenshot_review_dialog_function():
    """Test the convenience function for showing the dialog."""
    from syncopaid.screenshot_review_dialog import show_screenshot_review_dialog

    mock_db = MagicMock()
    mock_db.get_screenshots.return_value = []

    root = tk.Tk()
    root.withdraw()

    try:
        # Should not raise
        dialog = show_screenshot_review_dialog(root, mock_db)
        assert dialog is not None
    finally:
        if dialog and dialog.window:
            dialog.window.destroy()
        root.destroy()


def test_date_filter_refreshes_list():
    """Test that changing date filter refreshes the screenshot list."""
    from syncopaid.screenshot_review_dialog import ScreenshotReviewDialog
    from datetime import datetime

    mock_db = MagicMock()
    mock_db.get_screenshots.return_value = [
        {'id': 1, 'captured_at': '2025-12-23T10:00:00', 'file_path': '/path/1.jpg', 'window_title': 'Test1'},
    ]

    root = tk.Tk()
    root.withdraw()

    try:
        dialog = ScreenshotReviewDialog(root, mock_db)
        dialog.show()

        # Initial call
        assert mock_db.get_screenshots.call_count == 1

        # Simulate date change and refresh - mock the get() to return our test date
        dialog.date_var.get = MagicMock(return_value='2025-12-22')
        dialog._refresh()

        # Should have called get_screenshots again with date filter
        assert mock_db.get_screenshots.call_count == 2
        call_args = mock_db.get_screenshots.call_args
        # Check that start_date and end_date parameters were passed
        assert 'start_date' in call_args.kwargs
        assert 'end_date' in call_args.kwargs
        assert call_args.kwargs['start_date'] == '2025-12-22'
        assert call_args.kwargs['end_date'] == '2025-12-22'
    finally:
        if dialog.window:
            dialog.window.destroy()
        root.destroy()
