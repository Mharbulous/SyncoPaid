# Screenshot Secure Deletion - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Story ID:** 5.5 | **Created:** 2025-12-23 | **Stage:** `planned`
**Parent Plan:** 032_discrete-deletion-sensitive-records.md
**Depends On:** 032A_screenshot-dialog-foundation.md

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

---

**Goal:** Implement the secure deletion functionality with confirmation dialog.

**Approach:** Implement _delete_selected() to get selected items, show confirmation, and call database secure delete.

**Tech Stack:** tkinter (messagebox), Database.delete_screenshots_securely()

---

## Prerequisites

- [ ] venv activated: `venv\Scripts\activate`
- [ ] 032A plan executed (screenshot_review_dialog.py exists with show() method)
- [ ] Baseline tests pass: `python -m pytest -v`

## TDD Tasks

### Task 1: Implement Delete Selected with Confirmation (~5 min)

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

## Final Verification

Run after all tasks complete:
```bash
python -m pytest tests/test_screenshot_review_dialog.py -v    # New tests pass
python -m pytest -v                                            # All tests pass
```

## Notes

- The secure deletion infrastructure already exists in `database_screenshots.py:155-199`
- Files are overwritten with zeros before deletion via `secure_delete.py`
- SQLite `secure_delete` pragma is enabled in `database_connection.py`
- Existing tests in `test_secure_delete.py` verify the deletion behavior
