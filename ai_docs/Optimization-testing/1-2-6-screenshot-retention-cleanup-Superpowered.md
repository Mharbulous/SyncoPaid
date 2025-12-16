# Screenshot Retention & Cleanup Policy - Implementation Plan

> **For Claude:** Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Automatic monthly archiving of old screenshots to zip files

**Architecture:** `ArchiveWorker` class runs on startup and monthly to compress completed month folders. Archive runs after one clear month (e.g., Dec 1 archives October). On failure, tkinter dialog with retry options.

---

**Story ID:** 1.2.6 | **Status:** `planned`

---

## Acceptance Criteria

- Automatic monthly archiving after one clear month has passed
- Zip naming: `YYYY-MM_screenshots.zip` in `screenshots/archives/`
- Runs on startup and once per calendar month
- Original folders removed after successful archiving
- On failure: retry options (Now / 5 minutes / 1 hour / Tomorrow / Next startup)

## Files Affected

| File | Change |
|------|--------|
| `tests/test_archiver.py` | Create |
| `src/syncopaid/archiver.py` | Create |
| `src/syncopaid/__main__.py` | Modify - init archiver |
| `src/syncopaid/config.py` | Modify - add archive config |

## TDD Tasks

### Task 1: Detect archivable months

```python
# Test
def test_detect_archivable_months(tmp_path):
    # Given: today is 2025-12-16, folders: 2025-09-15, 2025-10-20, 2025-11-05
    # Then: only 2025-09-* and 2025-10-* are archivable (Nov not complete)

# Implementation
def get_archivable_folders(self, reference_date: datetime) -> List[str]:
    cutoff = (reference_date.replace(day=1) - timedelta(days=1)).replace(day=1)
    return [f for f in os.listdir(self.screenshot_dir) if parse_date(f) < cutoff]
```

---

### Task 2: Group folders by month

```python
# Test
def test_group_folders_by_month():
    folders = ["2025-10-01", "2025-10-15", "2025-10-31", "2025-09-20"]
    # Expected: {"2025-10": [...], "2025-09": [...]}

# Implementation
@staticmethod
def group_by_month(folders: List[str]) -> Dict[str, List[str]]:
    groups = {}
    for folder in folders:
        groups.setdefault(folder[:7], []).append(folder)
    return groups
```

---

### Task 3: Create zip archive

```python
# Test
def test_create_archive(tmp_path):
    # Setup folders with screenshots, call create_archive
    # Verify zip exists with correct contents

# Implementation
def create_archive(self, month_key: str, folders: List[str]) -> Path:
    zip_path = self.archive_dir / f"{month_key}_screenshots.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for folder in folders:
            for file in (self.screenshot_dir / folder).rglob("*"):
                zf.write(file, f"{folder}/{file.name}")
    return zip_path
```

---

### Task 4: Delete folders after successful archiving

```python
# Test
def test_cleanup_after_archive(tmp_path):
    # Call archive_month, verify folders deleted, zip exists

# Implementation
def archive_month(self, month_key: str, folders: List[str]):
    zip_path = self.create_archive(month_key, folders)
    if zip_path.exists() and zip_path.stat().st_size > 0:
        for folder in folders:
            shutil.rmtree(self.screenshot_dir / folder)
```

---

### Task 5: Archive worker with startup and monthly schedule

```python
# Implementation
class ArchiveWorker:
    def __init__(self, screenshot_dir: Path, archive_dir: Path):
        self.screenshot_dir = screenshot_dir
        self.archive_dir = archive_dir
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        self.last_run_date = None

    def run_once(self):
        archivable = self.get_archivable_folders(datetime.now())
        for month_key, folders in self.group_by_month(archivable).items():
            try:
                self.archive_month(month_key, folders)
            except Exception as e:
                self._handle_error(month_key, e)
        self.last_run_date = datetime.now().date()

    def start_background(self):
        threading.Thread(target=self._background_loop, daemon=True).start()

    def _background_loop(self):
        while True:
            time.sleep(86400)
            if self.last_run_date is None or datetime.now().date().month != self.last_run_date.month:
                self.run_once()
```

---

### Task 6: Error handling UI with retry options

```python
# Implementation - tkinter dialog with retry options per acceptance criteria
def _handle_error(self, month_key: str, error: Exception):
    # Show dialog: "Failed to archive {month_key}: {error}"
    # Options: Retry Now / 5 min / 1 hour / Tomorrow / Next startup
    # Schedule retry based on selection
```

---

### Task 7: Integration with __main__.py

```python
# In SyncoPaidApp.__init__ after screenshot worker
from syncopaid.archiver import ArchiveWorker

screenshot_base_dir = get_screenshot_directory().parent
self.archiver = ArchiveWorker(screenshot_base_dir, screenshot_base_dir / "archives")
self.archiver.run_once()
self.archiver.start_background()
```

---

### Task 8: Add config options

```python
# Add to DEFAULT_CONFIG
"archive_enabled": True,
"archive_check_interval_hours": 24,
```

---

## Edge Cases

- Empty folders: skip
- Malformed folder names: ignore
- Archives folder missing: create on init
