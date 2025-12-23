# Screenshot Menu Integration and Date Filter - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Story ID:** 5.5 | **Created:** 2025-12-23 | **Stage:** `planned`
**Parent Plan:** 032_discrete-deletion-sensitive-records.md
**Depends On:** 032B_screenshot-secure-deletion.md

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

---

**Goal:** Add menu integration and date filter controls to the screenshot review dialog.

**Approach:** Add View menu item and date filter entry with refresh functionality.

**Tech Stack:** tkinter (Entry, Menu), main_ui_windows.py integration

---

## Prerequisites

- [ ] venv activated: `venv\Scripts\activate`
- [ ] 032A and 032B plans executed (full dialog functionality exists)
- [ ] Baseline tests pass: `python -m pytest -v`

## TDD Tasks

### Task 1: Add Menu Integration (~3 min)

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

### Task 2: Add Date Filter Controls (~4 min)

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

- This is the final sub-plan for story 5.5
- Completes all acceptance criteria for the story
