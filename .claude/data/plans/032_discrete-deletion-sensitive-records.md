# Discrete Deletion of Sensitive Records - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Story ID:** 5.5 | **Created:** 2025-12-23 | **Stage:** `planned`

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

---

**Goal:** Enable lawyers to discretely delete sensitive screenshots they notice while reviewing their activity (e.g., accidental capture of privileged calls, inappropriate content).

**Approach:** Create a screenshot review dialog accessible from View menu that displays screenshots with metadata. Users can select and delete individual screenshots using the existing secure deletion infrastructure.

**Tech Stack:** tkinter (dialogs), PIL/Pillow (image thumbnails), Database.delete_screenshots_securely()

---

## Story Context

**Title:** Discrete Deletion of Sensitive Records

**Description:** Database.py has insert/query methods but no delete for individual records. Screenshots stored in %LOCALAPPDATA%\SyncoPaid\screenshots\YYYY-MM-DD\. Tray.py provides menu interface. Use case: User reviewing screenshots notices sensitive content (attorney-client call, private browsing, accidental Zoom incident) and needs immediate discrete removal.

**Acceptance Criteria:**
- [ ] User can view a list of their captured screenshots with timestamp and window title
- [ ] User can select one or more screenshots to delete
- [ ] Deletion is secure (files overwritten before removal)
- [ ] Deleted records are removed from both filesystem and database
- [ ] Confirmation dialog prevents accidental deletion

## Prerequisites

- [ ] venv activated: `venv\Scripts\activate`
- [ ] Baseline tests pass: `python -m pytest -v`

## TDD Tasks

### Task 1: Create Screenshot Review Dialog Structure (~5 min)

**Files:**
- Create: `tests/test_screenshot_review_dialog.py`
- Create: `src/syncopaid/screenshot_review_dialog.py`

**Context:** This creates the dialog window class that will display screenshots. The dialog will use tkinter Listbox to show screenshot metadata and thumbnail preview.

**Step 1 - RED:** Write failing test
```python
# tests/test_screenshot_review_dialog.py
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
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_screenshot_review_dialog.py::test_screenshot_review_dialog_instantiation -v
```
Expected output: `FAILED` (ModuleNotFoundError: No module named 'syncopaid.screenshot_review_dialog')

**Step 3 - GREEN:** Write minimal implementation
```python
# src/syncopaid/screenshot_review_dialog.py
"""Screenshot review dialog for discrete deletion of sensitive records."""
import tkinter as tk
from tkinter import ttk
from typing import Optional
from syncopaid.database import Database


class ScreenshotReviewDialog:
    """
    Dialog for reviewing and deleting screenshots.

    Provides a list of captured screenshots with the ability to
    select and securely delete sensitive content.
    """

    def __init__(self, parent: tk.Tk, db: Database):
        """
        Initialize the screenshot review dialog.

        Args:
            parent: Parent tkinter window
            db: Database instance for screenshot operations
        """
        self.parent = parent
        self.db = db
        self.window: Optional[tk.Toplevel] = None
        self.screenshots = []
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_screenshot_review_dialog.py::test_screenshot_review_dialog_instantiation -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add tests/test_screenshot_review_dialog.py src/syncopaid/screenshot_review_dialog.py && git commit -m "feat(5.5): add screenshot review dialog skeleton"
```

---

### Task 2: Add Dialog Window Creation Method (~5 min)

**Files:**
- Modify: `tests/test_screenshot_review_dialog.py`
- Modify: `src/syncopaid/screenshot_review_dialog.py`

**Context:** This adds the show() method that creates the actual dialog window with a listbox for screenshots and control buttons.

**Step 1 - RED:** Write failing test
```python
# tests/test_screenshot_review_dialog.py (add to existing file)
def test_show_creates_window():
    """Test that show() creates a Toplevel window."""
    from syncopaid.screenshot_review_dialog import ScreenshotReviewDialog

    mock_db = MagicMock()
    mock_db.get_screenshots.return_value = []

    root = tk.Tk()
    root.withdraw()

    try:
        dialog = ScreenshotReviewDialog(root, mock_db)
        dialog.show()

        assert dialog.window is not None
        assert isinstance(dialog.window, tk.Toplevel)
        assert dialog.window.winfo_exists()
    finally:
        if dialog.window:
            dialog.window.destroy()
        root.destroy()
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_screenshot_review_dialog.py::test_show_creates_window -v
```
Expected output: `FAILED` (AttributeError: 'ScreenshotReviewDialog' object has no attribute 'show')

**Step 3 - GREEN:** Add show() method
```python
# src/syncopaid/screenshot_review_dialog.py (add method to class)
    def show(self):
        """Show the screenshot review dialog."""
        self.window = tk.Toplevel(self.parent)
        self.window.title("Review Screenshots")
        self.window.geometry("800x600")
        self.window.transient(self.parent)

        # Load screenshots from database
        self.screenshots = self.db.get_screenshots(limit=100)

        # Create main frame
        main_frame = ttk.Frame(self.window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Listbox for screenshots
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        self.listbox = tk.Listbox(list_frame, selectmode=tk.EXTENDED, height=20)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scrollbar.set)

        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Populate listbox
        for screenshot in self.screenshots:
            display_text = f"{screenshot['captured_at'][:19]} - {screenshot.get('window_title', 'Unknown')}"
            self.listbox.insert(tk.END, display_text)

        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(button_frame, text="Delete Selected", command=self._delete_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Close", command=self.window.destroy).pack(side=tk.RIGHT, padx=5)

    def _delete_selected(self):
        """Delete selected screenshots."""
        pass  # Will implement in next task
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_screenshot_review_dialog.py::test_show_creates_window -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add tests/test_screenshot_review_dialog.py src/syncopaid/screenshot_review_dialog.py && git commit -m "feat(5.5): add show() method with screenshot listbox"
```

---

### Task 3: Implement Delete Selected with Confirmation (~5 min)

**Files:**
- Modify: `tests/test_screenshot_review_dialog.py`
- Modify: `src/syncopaid/screenshot_review_dialog.py`

**Context:** This implements the core deletion functionality - getting selected items, showing confirmation, and calling the secure delete method.

**Step 1 - RED:** Write failing test
```python
# tests/test_screenshot_review_dialog.py (add to existing file)
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

        # Select first item
        dialog.listbox.selection_set(0)

        # Mock the confirmation dialog to return True
        with patch('tkinter.messagebox.askyesno', return_value=True):
            dialog._delete_selected()

        # Verify secure delete was called with correct ID
        mock_db.delete_screenshots_securely.assert_called_once_with([1])
    finally:
        if dialog.window:
            dialog.window.destroy()
        root.destroy()
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_screenshot_review_dialog.py::test_delete_selected_calls_secure_delete -v
```
Expected output: `FAILED` (AssertionError: delete_screenshots_securely not called)

**Step 3 - GREEN:** Implement _delete_selected()
```python
# src/syncopaid/screenshot_review_dialog.py (replace _delete_selected method)
    def _delete_selected(self):
        """Delete selected screenshots with confirmation."""
        from tkinter import messagebox

        # Get selected indices
        selected_indices = self.listbox.curselection()
        if not selected_indices:
            messagebox.showinfo("No Selection", "Please select screenshots to delete.", parent=self.window)
            return

        # Get screenshot IDs for selected items
        selected_ids = [self.screenshots[i]['id'] for i in selected_indices]

        # Confirm deletion
        count = len(selected_ids)
        message = f"Permanently delete {count} screenshot{'s' if count > 1 else ''}?\n\nThis action cannot be undone."
        if not messagebox.askyesno("Confirm Deletion", message, parent=self.window):
            return

        # Perform secure deletion
        deleted = self.db.delete_screenshots_securely(selected_ids)

        # Remove from listbox (in reverse order to preserve indices)
        for i in reversed(selected_indices):
            self.listbox.delete(i)
            del self.screenshots[i]

        messagebox.showinfo("Deleted", f"Securely deleted {deleted} screenshot{'s' if deleted != 1 else ''}.", parent=self.window)
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_screenshot_review_dialog.py::test_delete_selected_calls_secure_delete -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add tests/test_screenshot_review_dialog.py src/syncopaid/screenshot_review_dialog.py && git commit -m "feat(5.5): implement secure deletion with confirmation"
```

---

### Task 4: Add Menu Integration (~3 min)

**Files:**
- Modify: `tests/test_screenshot_review_dialog.py`
- Modify: `src/syncopaid/main_ui_windows.py:92-110`

**Context:** Add "Review Screenshots" menu item to View menu that opens the dialog. This gives users access to the deletion functionality from the main window.

**Step 1 - RED:** Write failing test
```python
# tests/test_screenshot_review_dialog.py (add to existing file)
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
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_screenshot_review_dialog.py::test_show_screenshot_review_dialog_function -v
```
Expected output: `FAILED` (ImportError: cannot import name 'show_screenshot_review_dialog')

**Step 3 - GREEN:** Add convenience function and menu integration
```python
# src/syncopaid/screenshot_review_dialog.py (add at end of file)
def show_screenshot_review_dialog(parent: tk.Tk, db: Database) -> ScreenshotReviewDialog:
    """
    Show the screenshot review dialog.

    Args:
        parent: Parent tkinter window
        db: Database instance

    Returns:
        The dialog instance
    """
    dialog = ScreenshotReviewDialog(parent, db)
    dialog.show()
    return dialog
```

Then update `src/syncopaid/main_ui_windows.py` - add after line 110 (after view_screenshots command):

```python
# src/syncopaid/main_ui_windows.py (insert after line 110, before view_timeline definition)
            def review_screenshots():
                """Open screenshot review dialog for deletion."""
                from syncopaid.screenshot_review_dialog import show_screenshot_review_dialog
                show_screenshot_review_dialog(root, database)

            view_menu.add_command(label="Review && Delete Screenshots...", command=review_screenshots)
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_screenshot_review_dialog.py::test_show_screenshot_review_dialog_function -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add tests/test_screenshot_review_dialog.py src/syncopaid/screenshot_review_dialog.py src/syncopaid/main_ui_windows.py && git commit -m "feat(5.5): add Review & Delete Screenshots menu item"
```

---

### Task 5: Add Date Filter Controls (~4 min)

**Files:**
- Modify: `tests/test_screenshot_review_dialog.py`
- Modify: `src/syncopaid/screenshot_review_dialog.py`

**Context:** Add date filter to the dialog so users can narrow down screenshots to a specific date range. This makes it easier to find the sensitive screenshot they remember seeing.

**Step 1 - RED:** Write failing test
```python
# tests/test_screenshot_review_dialog.py (add to existing file)
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

        # Simulate date change and refresh
        dialog.date_var.set('2025-12-22')
        dialog._refresh()

        # Should have called get_screenshots again with date filter
        assert mock_db.get_screenshots.call_count == 2
        call_args = mock_db.get_screenshots.call_args
        assert call_args.kwargs.get('start_date') == '2025-12-22'
    finally:
        if dialog.window:
            dialog.window.destroy()
        root.destroy()
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_screenshot_review_dialog.py::test_date_filter_refreshes_list -v
```
Expected output: `FAILED` (AttributeError: 'ScreenshotReviewDialog' object has no attribute 'date_var')

**Step 3 - GREEN:** Add date filter to show() method
```python
# src/syncopaid/screenshot_review_dialog.py (update show() method)
    def show(self):
        """Show the screenshot review dialog."""
        from datetime import datetime

        self.window = tk.Toplevel(self.parent)
        self.window.title("Review Screenshots")
        self.window.geometry("800x600")
        self.window.transient(self.parent)

        # Create main frame
        main_frame = ttk.Frame(self.window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Date filter frame
        filter_frame = ttk.Frame(main_frame)
        filter_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(filter_frame, text="Date:").pack(side=tk.LEFT, padx=(0, 5))
        self.date_var = tk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))
        date_entry = ttk.Entry(filter_frame, textvariable=self.date_var, width=12)
        date_entry.pack(side=tk.LEFT, padx=(0, 10))
        date_entry.bind('<Return>', lambda e: self._refresh())

        ttk.Button(filter_frame, text="Refresh", command=self._refresh).pack(side=tk.LEFT)
        ttk.Button(filter_frame, text="All Dates", command=self._show_all).pack(side=tk.LEFT, padx=5)

        # Listbox for screenshots
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        self.listbox = tk.Listbox(list_frame, selectmode=tk.EXTENDED, height=20)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scrollbar.set)

        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(button_frame, text="Delete Selected", command=self._delete_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Close", command=self.window.destroy).pack(side=tk.RIGHT, padx=5)

        # Load initial data
        self._refresh()

    def _refresh(self):
        """Refresh the screenshot list based on current date filter."""
        date_filter = self.date_var.get().strip()
        if date_filter:
            self.screenshots = self.db.get_screenshots(start_date=date_filter, end_date=date_filter, limit=100)
        else:
            self.screenshots = self.db.get_screenshots(limit=100)

        self._populate_listbox()

    def _show_all(self):
        """Show all screenshots without date filter."""
        self.date_var.set('')
        self._refresh()

    def _populate_listbox(self):
        """Populate the listbox with current screenshots."""
        self.listbox.delete(0, tk.END)
        for screenshot in self.screenshots:
            display_text = f"{screenshot['captured_at'][:19]} - {screenshot.get('window_title', 'Unknown')}"
            self.listbox.insert(tk.END, display_text)
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_screenshot_review_dialog.py::test_date_filter_refreshes_list -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add tests/test_screenshot_review_dialog.py src/syncopaid/screenshot_review_dialog.py && git commit -m "feat(5.5): add date filter controls to screenshot review"
```

---

## Final Verification

Run after all tasks complete:
```bash
python -m pytest tests/test_screenshot_review_dialog.py -v    # New tests pass
python -m pytest -v                                            # All tests pass
python -m syncopaid                                            # App runs, View menu has new item
```

**Manual verification:**
1. Start SyncoPaid
2. Open main window (right-click tray → Open SyncoPaid)
3. View menu → "Review & Delete Screenshots..."
4. Dialog shows screenshots with date filter
5. Select a screenshot and click "Delete Selected"
6. Confirm deletion works and removes from list

## Rollback

If issues arise: `git log --oneline -10` to find commit, then `git revert <hash>`

## Notes

- The secure deletion infrastructure already exists in `database_screenshots.py:155-199`
- Files are overwritten with zeros before deletion via `secure_delete.py`
- SQLite `secure_delete` pragma is enabled in `database_connection.py`
- Existing tests in `test_secure_delete.py` verify the deletion behavior
