# Screenshot Retention - Core Archiving Logic

> **TDD Required:** Each task: Write test → RED → Write code → GREEN → Commit

**Goal:** Implement core archiving functionality - detection, grouping, zip creation, and cleanup

**Story ID:** 2.6 | **Created:** 2025-12-22 | **Status:** `planned`

---

## Story Context

**Title:** Screenshot Retention & Cleanup Policy (Part A - Core Logic)

**Description:** Core archiving functionality for compressing old screenshots into monthly zip files.

**Scope:** This sub-plan covers the foundational archiving logic:
- Detecting which folders are eligible for archiving
- Grouping folders by month
- Creating zip archives
- Cleaning up folders after archiving

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

## TDD Tasks

### Task 1: Detect archivable months

**Files:** Test: `tests/test_archiver.py` | Impl: `src/syncopaid/archiver.py`

**RED:** Test identifies folders eligible for archiving (one clear month passed).
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
Run: `pytest tests/test_archiver.py::test_detect_archivable_months -v` → Expect: FAILED

**GREEN:** Implement folder detection with one-clear-month logic.
```python
def get_archivable_folders(self, reference_date: datetime) -> List[str]:
    # Folders with date < first day of previous month
    cutoff = (reference_date.replace(day=1) - timedelta(days=1)).replace(day=1)
    return [f for f in os.listdir(screenshot_dir) if parse_date(f) < cutoff]
```
Run: `pytest tests/test_archiver.py::test_detect_archivable_months -v` → Expect: PASSED

**COMMIT:** `git add tests/test_archiver.py src/syncopaid/archiver.py && git commit -m "feat: detect archivable screenshot folders"`

---

### Task 2: Group folders by month for zipping

**Files:** Test: `tests/test_archiver.py` | Impl: `src/syncopaid/archiver.py`

**RED:** Test groups folders by YYYY-MM for zip creation.
```python
def test_group_folders_by_month():
    folders = ["2025-10-01", "2025-10-15", "2025-10-31", "2025-09-20"]
    grouped = ArchiveWorker.group_by_month(folders)
    assert grouped == {
        "2025-10": ["2025-10-01", "2025-10-15", "2025-10-31"],
        "2025-09": ["2025-09-20"]
    }
```
Run: `pytest tests/test_archiver.py::test_group_folders_by_month -v` → Expect: FAILED

**GREEN:** Implement month grouping.
```python
@staticmethod
def group_by_month(folders: List[str]) -> Dict[str, List[str]]:
    groups = {}
    for folder in folders:
        month_key = folder[:7]  # "2025-10"
        groups.setdefault(month_key, []).append(folder)
    return groups
```
Run: `pytest tests/test_archiver.py::test_group_folders_by_month -v` → Expect: PASSED

**COMMIT:** `git add tests/test_archiver.py src/syncopaid/archiver.py && git commit -m "feat: group folders by month for archiving"`

---

### Task 3: Create zip archive from folders

**Files:** Test: `tests/test_archiver.py` | Impl: `src/syncopaid/archiver.py`

**RED:** Test creates zip file with correct naming and contents.
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
Run: `pytest tests/test_archiver.py::test_create_archive -v` → Expect: FAILED

**GREEN:** Implement zip creation.
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
Run: `pytest tests/test_archiver.py::test_create_archive -v` → Expect: PASSED

**COMMIT:** `git add tests/test_archiver.py src/syncopaid/archiver.py && git commit -m "feat: create monthly zip archives"`

---

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

## Verification

- [ ] All tests pass: `python -m pytest tests/test_archiver.py -v`
- [ ] Core archiving logic complete

## Next Steps

After this sub-plan completes, proceed to `017B_screenshot-retention-operations.md` for:
- Archive worker with startup and monthly scheduling
- Error handling UI with retry options
- Integration with __main__.py
- Config options for archiving
