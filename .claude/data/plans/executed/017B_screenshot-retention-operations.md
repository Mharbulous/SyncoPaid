# Screenshot Retention - Worker Operations & Integration

> **TDD Required:** Each task: Write test → RED → Write code → GREEN → Commit

**Goal:** Implement archive worker scheduling, error handling, and app integration

**Story ID:** 2.6 | **Created:** 2025-12-22 | **Status:** `planned`

---

## Story Context

**Title:** Screenshot Retention & Cleanup Policy (Part B - Operations)

**Description:** Worker scheduling, error handling UI, and integration with the main application.

**Prerequisites:** `017A_screenshot-retention-core.md` must be completed first.

**Scope:** This sub-plan covers:
- Archive worker with startup and monthly scheduling
- Error handling UI with retry dialog
- Integration with __main__.py
- Configuration options for archiving

## Prerequisites

- [x] venv activated: `venv\Scripts\activate`
- [x] Baseline tests pass: `python -m pytest -v`
- [x] Core archiving logic complete (017A)

## Files Affected

| File | Change | Purpose |
|------|--------|---------|
| `tests/test_archiver.py` | Modify | Add worker and error tests |
| `src/syncopaid/archiver.py` | Modify | Add worker and error handling |
| `tests/test_integration.py` | Modify | Test app integration |
| `src/syncopaid/__main__.py:147-160` | Modify | Initialize archiver on startup |
| `tests/test_config.py` | Modify | Test archive config |
| `src/syncopaid/config.py:16-37` | Modify | Add archive config options |

## TDD Tasks

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

### Task 7: Integration with __main__.py

**Files:** Test: `tests/test_integration.py` | Impl: `src/syncopaid/__main__.py:147-160`

**RED:** Test app initializes archiver on startup.
```python
def test_app_initializes_archiver(mocker):
    mock_archiver = mocker.patch('syncopaid.archiver.ArchiveWorker')
    app = SyncoPaidApp()
    assert mock_archiver.called
    mock_archiver.return_value.run_once.assert_called_once()
```
Run: `pytest tests/test_integration.py::test_app_initializes_archiver -v` → Expect: FAILED

**GREEN:** Add archiver initialization to __main__.py.
```python
# In __main__.py after screenshot worker init
from syncopaid.archiver import ArchiveWorker

# Initialize archiver
screenshot_base_dir = get_screenshot_directory().parent
archive_dir = screenshot_base_dir / "archives"
self.archiver = ArchiveWorker(screenshot_base_dir, archive_dir)
self.archiver.run_once()  # Run on startup
self.archiver.start_background()  # Schedule monthly checks
```
Run: `pytest tests/test_integration.py::test_app_initializes_archiver -v` → Expect: PASSED

**COMMIT:** `git add tests/test_integration.py src/syncopaid/__main__.py && git commit -m "feat: integrate archiver into app startup"`

---

### Task 8: Add config options for archiving

**Files:** Test: `tests/test_config.py` | Impl: `src/syncopaid/config.py:16-37`

**RED:** Test config includes archive settings.
```python
def test_archive_config_defaults():
    config = Config()
    assert config.archive_enabled == True
    assert config.archive_check_interval_hours == 24
```
Run: `pytest tests/test_config.py::test_archive_config_defaults -v` → Expect: FAILED

**GREEN:** Add archive config to DEFAULT_CONFIG.
```python
# In config.py DEFAULT_CONFIG
"archive_enabled": True,
"archive_check_interval_hours": 24,
```
Run: `pytest tests/test_config.py::test_archive_config_defaults -v` → Expect: PASSED

**COMMIT:** `git add tests/test_config.py src/syncopaid/config.py && git commit -m "feat: add archive configuration options"`

---

## Verification

- [ ] All tests pass: `python -m pytest -v`
- [ ] Manual test: Create old folders, run app, verify archiving
- [ ] Manual test: Trigger archive error (disk full), verify dialog
- [ ] Check zip contents match original screenshots
- [ ] Verify monthly scheduling (mock system date)

## Notes

**Edge Cases:**
- Empty folders (skip archiving)
- Malformed folder names (ignore)
- Archives folder doesn't exist (create on init)
- Partial month at month boundary (excluded correctly)

**Follow-up Work:**
- Story 8.4.3 will use archives for screenshot retrieval in AI review UI
- Consider compression level tuning for disk space vs. CPU tradeoff
