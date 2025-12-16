# Screenshot Retention & Cleanup Policy - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

> **TDD Required:** Each task: Write test → RED → Write code → GREEN → Commit

**Goal:** Automatic monthly archiving of old screenshots to zip files

**Architecture:** Create an `ArchiveWorker` class that runs on startup and monthly to compress completed month folders into zip archives. Archive runs after one clear month has passed (e.g., on Dec 1, archive October). On failure, display tkinter dialog with retry options.

**Tech Stack:** Python zipfile, threading, tkinter for error UI, existing database/config modules

---

**Story ID:** 1.2.6 | **Created:** 2025-12-16 | **Status:** `planned`

---

## Story Context

**Title:** Screenshot Retention & Cleanup Policy

**Description:** Automatic archiving of old screenshots into monthly zip files for disk space management while preserving all screenshot history.

**Acceptance Criteria:**
- [x] Automatic monthly archiving (compress screenshots to zip by calendar month)
- [x] Archiving triggers after one clear month has passed (e.g., on Dec 1, archive October)
- [x] Zip file naming format: `YYYY-MM_screenshots.zip` (e.g., `2025-10_screenshots.zip`)
- [x] Archive stored in `archives/` subfolder within screenshots directory
- [x] Archive runs on startup and once per calendar month thereafter
- [x] Original screenshots removed from folder after successful archiving
- [x] No automatic deletion - all screenshots preserved in archives
- [x] On archive failure: alert user with retry options (Now / 5 minutes / 1 hour / Tomorrow / Next startup)

**Storage locations:**
- Screenshots: `%LOCALAPPDATA%/SyncoPaid/screenshots/YYYY-MM-DD/`
- Archives: `%LOCALAPPDATA%/SyncoPaid/screenshots/archives/`

## Prerequisites

- [x] venv activated: `venv\Scripts\activate`
- [x] Baseline tests pass: `python -m pytest -v`

## Files Affected

| File | Change | Purpose |
|------|--------|---------|
| `tests/test_archiver.py` | Create | Test archiving logic |
| `src/syncopaid/archiver.py` | Create | Archive worker implementation |
| `src/syncopaid/__main__.py:147-160` | Modify | Initialize archiver on startup |
| `src/syncopaid/config.py:16-37` | Modify | Add archive config options |

## TDD Tasks

### Task 1: Detect archivable months

**Files:**
- Create: `tests/test_archiver.py`
- Create: `src/syncopaid/archiver.py`

**Step 1: Write the failing test**

```python
def test_detect_archivable_months():
    # Given: today is 2025-12-16, folders: 2025-09-15, 2025-10-20, 2025-11-05
    # When: checking archivable folders
    # Then: only 2025-09-* and 2025-10-* are archivable (Nov is not complete)
    archiver = ArchiveWorker(screenshot_dir, archive_dir)
    folders = archiver.get_archivable_folders(reference_date=datetime(2025, 12, 16))
    assert "2025-09-15" in folders
    assert "2025-10-20" in folders
    assert "2025-11-05" not in folders
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_archiver.py::test_detect_archivable_months -v`
Expected: FAIL with "NameError: name 'ArchiveWorker' is not defined"

**Step 3: Write minimal implementation**

```python
def get_archivable_folders(self, reference_date: datetime) -> List[str]:
    # Folders with date < first day of previous month
    cutoff = (reference_date.replace(day=1) - timedelta(days=1)).replace(day=1)
    return [f for f in os.listdir(screenshot_dir) if parse_date(f) < cutoff]
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_archiver.py::test_detect_archivable_months -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_archiver.py src/syncopaid/archiver.py
git commit -m "feat: detect archivable screenshot folders"
```

---

### Task 2: Group folders by month for zipping

**Files:**
- Modify: `tests/test_archiver.py`
- Modify: `src/syncopaid/archiver.py`

**Step 1: Write the failing test**

```python
def test_group_folders_by_month():
    folders = ["2025-10-01", "2025-10-15", "2025-10-31", "2025-09-20"]
    grouped = ArchiveWorker.group_by_month(folders)
    assert grouped == {
        "2025-10": ["2025-10-01", "2025-10-15", "2025-10-31"],
        "2025-09": ["2025-09-20"]
    }
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_archiver.py::test_group_folders_by_month -v`
Expected: FAIL with "AttributeError: type object 'ArchiveWorker' has no attribute 'group_by_month'"

**Step 3: Write minimal implementation**

```python
@staticmethod
def group_by_month(folders: List[str]) -> Dict[str, List[str]]:
    groups = {}
    for folder in folders:
        month_key = folder[:7]  # "2025-10"
        groups.setdefault(month_key, []).append(folder)
    return groups
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_archiver.py::test_group_folders_by_month -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_archiver.py src/syncopaid/archiver.py
git commit -m "feat: group folders by month for archiving"
```

---

### Task 3: Create zip archive from folders

**Files:**
- Modify: `tests/test_archiver.py`
- Modify: `src/syncopaid/archiver.py`

**Step 1: Write the failing test**

```python
def test_create_archive(tmp_path):
    # Setup test folders with screenshots
    screenshot_dir = tmp_path / "screenshots"
    (screenshot_dir / "2025-10-01").mkdir(parents=True)
    (screenshot_dir / "2025-10-15").mkdir(parents=True)
    (screenshot_dir / "2025-10-01" / "test1.jpg").write_text("img1")
    (screenshot_dir / "2025-10-15" / "test2.jpg").write_text("img2")

    archive_dir = tmp_path / "archives"
    archiver = ArchiveWorker(screenshot_dir, archive_dir)

    zip_path = archiver.create_archive("2025-10", ["2025-10-01", "2025-10-15"])

    assert zip_path.exists()
    assert zip_path.name == "2025-10_screenshots.zip"
    # Verify zip contents
    with zipfile.ZipFile(zip_path) as zf:
        assert "2025-10-01/test1.jpg" in zf.namelist()
        assert "2025-10-15/test2.jpg" in zf.namelist()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_archiver.py::test_create_archive -v`
Expected: FAIL with "AttributeError: 'ArchiveWorker' object has no attribute 'create_archive'"

**Step 3: Write minimal implementation**

```python
def create_archive(self, month_key: str, folders: List[str]) -> Path:
    zip_path = self.archive_dir / f"{month_key}_screenshots.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for folder in folders:
            folder_path = self.screenshot_dir / folder
            for file in folder_path.rglob("*.jpg"):
                arcname = f"{folder}/{file.name}"
                zf.write(file, arcname)
    return zip_path
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_archiver.py::test_create_archive -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_archiver.py src/syncopaid/archiver.py
git commit -m "feat: create monthly zip archives"
```

---

### Task 4: Delete folders after successful archiving

**Files:**
- Modify: `tests/test_archiver.py`
- Modify: `src/syncopaid/archiver.py`

**Step 1: Write the failing test**

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

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_archiver.py::test_cleanup_after_archive -v`
Expected: FAIL with "AttributeError: 'ArchiveWorker' object has no attribute 'archive_month'"

**Step 3: Write minimal implementation**

```python
def archive_month(self, month_key: str, folders: List[str]):
    zip_path = self.create_archive(month_key, folders)
    # Verify zip created successfully before deleting
    if zip_path.exists() and zip_path.stat().st_size > 0:
        for folder in folders:
            shutil.rmtree(self.screenshot_dir / folder)
        logging.info(f"Archived and cleaned up {len(folders)} folders for {month_key}")
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_archiver.py::test_cleanup_after_archive -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_archiver.py src/syncopaid/archiver.py
git commit -m "feat: cleanup folders after successful archiving"
```

---

### Task 5: Archive worker with startup and monthly schedule

**Files:**
- Modify: `tests/test_archiver.py`
- Modify: `src/syncopaid/archiver.py`

**Step 1: Write the failing test**

```python
def test_archive_worker_startup():
    archiver = ArchiveWorker(screenshot_dir, archive_dir)
    archiver.run_once()  # Synchronous run for testing
    # Verify archivable months were processed
    assert mock_archive_month.called
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_archiver.py::test_archive_worker_startup -v`
Expected: FAIL with "AttributeError: 'ArchiveWorker' object has no attribute 'run_once'"

**Step 3: Write minimal implementation**

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

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_archiver.py::test_archive_worker_startup -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_archiver.py src/syncopaid/archiver.py
git commit -m "feat: archive worker with startup and monthly scheduling"
```

---

### Task 6: Error handling UI with retry options

**Files:**
- Modify: `tests/test_archiver.py`
- Modify: `src/syncopaid/archiver.py`

**Step 1: Write the failing test**

```python
def test_error_dialog(mocker):
    mock_messagebox = mocker.patch('tkinter.messagebox.askyesnocancel')
    mock_messagebox.return_value = True  # Retry now

    archiver = ArchiveWorker(screenshot_dir, archive_dir)
    archiver._handle_error("2025-10", Exception("Disk full"))

    assert mock_messagebox.called
    # Verify retry scheduled
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_archiver.py::test_error_dialog -v`
Expected: FAIL with "AttributeError: 'ArchiveWorker' object has no attribute '_handle_error'"

**Step 3: Write minimal implementation**

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
        logging.warning(f"Archive deferred for {month_key}")

    root.destroy()
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_archiver.py::test_error_dialog -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_archiver.py src/syncopaid/archiver.py
git commit -m "feat: error handling with retry dialog"
```

---

### Task 7: Integration with __main__.py

**Files:**
- Create: `tests/test_integration.py`
- Modify: `src/syncopaid/__main__.py:147-160`

**Step 1: Write the failing test**

```python
def test_app_initializes_archiver(mocker):
    mock_archiver = mocker.patch('syncopaid.archiver.ArchiveWorker')
    app = SyncoPaidApp()
    assert mock_archiver.called
    mock_archiver.return_value.run_once.assert_called_once()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_integration.py::test_app_initializes_archiver -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'syncopaid.archiver'"

**Step 3: Write minimal implementation**

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

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_integration.py::test_app_initializes_archiver -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_integration.py src/syncopaid/__main__.py
git commit -m "feat: integrate archiver into app startup"
```

---

### Task 8: Add config options for archiving

**Files:**
- Modify: `tests/test_config.py`
- Modify: `src/syncopaid/config.py:16-37`

**Step 1: Write the failing test**

```python
def test_archive_config_defaults():
    config = Config()
    assert config.archive_enabled == True
    assert config.archive_check_interval_hours == 24
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_config.py::test_archive_config_defaults -v`
Expected: FAIL with "AttributeError: 'Config' object has no attribute 'archive_enabled'"

**Step 3: Write minimal implementation**

```python
# In config.py DEFAULT_CONFIG
"archive_enabled": True,
"archive_check_interval_hours": 24,
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_config.py::test_archive_config_defaults -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_config.py src/syncopaid/config.py
git commit -m "feat: add archive configuration options"
```

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
- Story 1.8.4.3 will use archives for screenshot retrieval in AI review UI
- Consider compression level tuning for disk space vs. CPU tradeoff
