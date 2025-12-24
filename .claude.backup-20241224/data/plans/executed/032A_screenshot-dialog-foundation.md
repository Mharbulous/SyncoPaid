# Screenshot Review Dialog Foundation - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Story ID:** 5.5 | **Created:** 2025-12-23 | **Stage:** `planned`
**Parent Plan:** 032_discrete-deletion-sensitive-records.md

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

---

**Goal:** Create the screenshot review dialog skeleton and window creation method.

**Approach:** Build the foundational dialog class with instantiation and show() method that displays screenshots in a listbox.

**Tech Stack:** tkinter (dialogs), Database.get_screenshots()

---

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

## Final Verification

Run after all tasks complete:
```bash
python -m pytest tests/test_screenshot_review_dialog.py -v    # New tests pass
python -m pytest -v                                            # All tests pass
```

## Notes

- This sub-plan creates the foundation for subsequent plans (032B, 032C)
- The _delete_selected() is a stub that will be implemented in 032B
