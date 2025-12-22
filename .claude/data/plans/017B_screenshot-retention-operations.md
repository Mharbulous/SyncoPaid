# Screenshot Retention & Cleanup - Archive Operations

> **TDD Required:** Each task: Write test → RED → Write code → GREEN → Commit

**Goal:** Implement folder cleanup, background scheduling, and error handling for archiver

**Approach:** Extend `ArchiveWorker` with cleanup after archiving, background scheduling thread, and tkinter error dialogs.

**Tech Stack:** Python shutil, threading, tkinter

---

**Story ID:** 2.6 | **Created:** 2025-12-22 | **Status:** `planned`

**Parent Plan:** 017_screenshot-retention-cleanup.md (Tasks 4-6 of 8)

**Depends On:** 017A_screenshot-retention-core.md

---

## Prerequisites

- [x] venv activated: `venv\Scripts\activate`
- [x] Sub-plan A completed (core archive logic exists)
- [x] Baseline tests pass: `python -m pytest -v`

## Files Affected

| File | Change | Purpose |
|------|--------|---------|
| `tests/test_archiver.py` | Modify | Add cleanup and scheduling tests |
| `src/syncopaid/archiver.py` | Modify | Add cleanup, scheduling, error UI |

## TDD Tasks

### Task 4: Delete folders after successful archiving

**Files:** Test: `tests/test_archiver.py` | Impl: `src/syncopaid/archiver.py`

**RED:** Test verifies folders are removed after archiving.
```python
def test_cleanup_after_archive(tmp_path):
    screenshot_dir = tmp_path / "screenshots"
    (screenshot_dir / "2025-10-01").mkdir(parents=True)
    (screenshot_dir / "2025-10-01" / "test.jpg").write_text("img")

    archive_dir = tmp_path / "archives"
    archiver = ArchiveWorker(screenshot_dir, archive_dir)

    archiver.archive_month("2025-10", ["2025-10-01"])

    assert not (screenshot_dir / "2025-10-01").exists()
    assert (archive_dir / "2025-10_screenshots.zip").exists()
```
Run: `pytest tests/test_archiver.py::test_cleanup_after_archive -v` → Expect: FAILED

**GREEN:** Implement folder cleanup after archiving.
```python
def archive_month(self, month_key: str, folders: List[str]):
    zip_path = self.create_archive(month_key, folders)
    # Verify zip created successfully before deleting
    if zip_path.exists() and zip_path.stat().st_size > 0:
        for folder in folders:
            shutil.rmtree(self.screenshot_dir / folder)
        logging.info(f"Archived and cleaned up {len(folders)} folders for {month_key}")
```
Run: `pytest tests/test_archiver.py::test_cleanup_after_archive -v` → Expect: PASSED

**COMMIT:** `git add tests/test_archiver.py src/syncopaid/archiver.py && git commit -m "feat: cleanup folders after successful archiving"`

---

### Task 5: Archive worker with startup and monthly schedule

**Files:** Test: `tests/test_archiver.py` | Impl: `src/syncopaid/archiver.py`

**RED:** Test archiver runs on startup and schedules monthly checks.
```python
def test_archive_worker_startup():
    archiver = ArchiveWorker(screenshot_dir, archive_dir)
    archiver.run_once()  # Synchronous run for testing
    # Verify archivable months were processed
    assert mock_archive_month.called
```
Run: `pytest tests/test_archiver.py::test_archive_worker_startup -v` → Expect: FAILED

**GREEN:** Implement worker with run_once and background scheduling.
```python
class ArchiveWorker:
    def __init__(self, screenshot_dir: Path, archive_dir: Path):
        self.screenshot_dir = screenshot_dir
        self.archive_dir = archive_dir
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        self.last_run_date = None

    def run_once(self):
        """Run archiving process synchronously."""
        today = datetime.now().date()
        archivable = self.get_archivable_folders(datetime.now())
        grouped = self.group_by_month(archivable)
        for month_key, folders in grouped.items():
            try:
                self.archive_month(month_key, folders)
            except Exception as e:
                self._handle_error(month_key, e)
        self.last_run_date = today

    def start_background(self):
        """Start background thread for monthly checks."""
        threading.Thread(target=self._background_loop, daemon=True).start()

    def _background_loop(self):
        while True:
            time.sleep(86400)  # Check daily
            today = datetime.now().date()
            if self.last_run_date is None or today.month != self.last_run_date.month:
                self.run_once()
```
Run: `pytest tests/test_archiver.py::test_archive_worker_startup -v` → Expect: PASSED

**COMMIT:** `git add tests/test_archiver.py src/syncopaid/archiver.py && git commit -m "feat: archive worker with startup and monthly scheduling"`

---

### Task 6: Error handling UI with retry options

**Files:** Test: `tests/test_archiver.py` | Impl: `src/syncopaid/archiver.py`

**RED:** Test error handler shows tkinter dialog with retry options.
```python
def test_error_dialog(mocker):
    mock_messagebox = mocker.patch('tkinter.messagebox.askyesnocancel')
    mock_messagebox.return_value = True  # Retry now

    archiver = ArchiveWorker(screenshot_dir, archive_dir)
    archiver._handle_error("2025-10", Exception("Disk full"))

    assert mock_messagebox.called
    # Verify retry scheduled
```
Run: `pytest tests/test_archiver.py::test_error_dialog -v` → Expect: FAILED

**GREEN:** Implement error dialog with retry logic.
```python
def _handle_error(self, month_key: str, error: Exception):
    import tkinter as tk
    from tkinter import messagebox

    root = tk.Tk()
    root.withdraw()

    message = f"Failed to archive {month_key}: {error}\n\nRetry options:"
    response = messagebox.askretrycancel(
        "Archive Failed",
        message,
        detail="Choose Retry to try again now, or Cancel to retry on next startup"
    )

    if response:  # Retry now
        self.archive_month(month_key, self.get_archivable_folders())
    else:  # Cancel - will retry on next startup
        logging.warning(f"Archive pending for {month_key}")

    root.destroy()
```
Run: `pytest tests/test_archiver.py::test_error_dialog -v` → Expect: PASSED

**COMMIT:** `git add tests/test_archiver.py src/syncopaid/archiver.py && git commit -m "feat: error handling with retry dialog"`

---

## Verification

- [ ] All tests pass: `python -m pytest tests/test_archiver.py -v`
- [ ] Manual test: Trigger archive error (simulate failure), verify dialog appears

## Notes

This sub-plan completes the archiver module functionality. Sub-plan C will integrate with the main app and add configuration options.
