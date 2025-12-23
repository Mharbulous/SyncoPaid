# Secure Data Deletion - Database Operations

> **TDD Required:** Each task: Write test → RED → Write code → GREEN → Commit

**Goal:** Add secure deletion methods for screenshots and events with file cleanup

**Approach:** Create database methods that use secure file deletion for associated files

**Tech Stack:** SQLite, secure_delete module from 028B

---

**Story ID:** 7.6 | **Created:** 2025-12-21 | **Status:** `planned`

**Parent Plan:** 028_secure-data-deletion.md

---

## Story Context

**Title:** Secure Data Deletion - Database Operations

**Description:** Add database methods for securely deleting screenshots and events, including secure file deletion for associated screenshot files.

**Acceptance Criteria:**
- [x] Screenshots associated with deleted events are securely removed from filesystem
- [x] Database records are deleted with secure_delete pragma
- [x] Event deletion cascades to associated screenshot deletion

## Prerequisites

- [x] venv activated: `venv\Scripts\activate`
- [x] Baseline tests pass: `python -m pytest -v`
- [x] Sub-plan 028A completed (secure_delete pragma enabled)
- [x] Sub-plan 028B completed (secure_delete_file utility)

## Files Affected

| File | Change | Purpose |
|------|--------|---------|
| `tests/test_secure_delete.py` | Modify | Add tests for database secure deletion |
| `src/syncopaid/database_screenshots.py` | Modify | Add secure screenshot deletion method |
| `src/syncopaid/database_operations_events.py` | Modify | Add secure event deletion with screenshot cascade |

## TDD Tasks

### Task 1: Add secure screenshot deletion method to database

**Files:** Test: `tests/test_secure_delete.py` | Impl: `src/syncopaid/database_screenshots.py`

**RED:** Test that deleting screenshots securely removes files.
```python
def test_delete_screenshots_securely(tmp_path):
    """Verify screenshot deletion removes both database record and file."""
    db_path = tmp_path / "test.db"
    db = Database(str(db_path))

    # Create test screenshot file
    screenshot_dir = tmp_path / "screenshots" / "2025-12-21"
    screenshot_dir.mkdir(parents=True)
    screenshot_file = screenshot_dir / "test_screenshot.jpg"
    screenshot_file.write_bytes(b"fake image content")

    # Insert screenshot record
    screenshot_id = db.insert_screenshot(
        captured_at="2025-12-21T10:00:00",
        file_path=str(screenshot_file),
        window_app="test.exe",
        window_title="Test Window"
    )

    # Delete screenshot securely
    deleted = db.delete_screenshots_securely([screenshot_id])

    assert deleted == 1
    assert not screenshot_file.exists(), "Screenshot file should be deleted"

    # Verify database record is gone
    screenshots = db.get_screenshots()
    assert len(screenshots) == 0
```
Run: `pytest tests/test_secure_delete.py::test_delete_screenshots_securely -v` → Expect: FAILED

**GREEN:** Add secure screenshot deletion method.
```python
# In database_screenshots.py, add method:
def delete_screenshots_securely(self, screenshot_ids: List[int]) -> int:
    """
    Securely delete screenshots by ID, removing both database records and files.

    Files are overwritten with zeros before deletion to prevent forensic recovery.

    Args:
        screenshot_ids: List of screenshot IDs to delete

    Returns:
        Number of screenshots deleted
    """
    from .secure_delete import secure_delete_file

    if not screenshot_ids:
        return 0

    deleted_count = 0

    with self._get_connection() as conn:
        cursor = conn.cursor()

        # Get file paths before deletion
        placeholders = ','.join('?' * len(screenshot_ids))
        cursor.execute(
            f"SELECT id, file_path FROM screenshots WHERE id IN ({placeholders})",
            screenshot_ids
        )
        screenshots = cursor.fetchall()

        # Securely delete each file
        for row in screenshots:
            file_path = Path(row['file_path'])
            secure_delete_file(file_path)

        # Delete database records
        cursor.execute(
            f"DELETE FROM screenshots WHERE id IN ({placeholders})",
            screenshot_ids
        )
        deleted_count = cursor.rowcount

    logging.info(f"Securely deleted {deleted_count} screenshots")
    return deleted_count
```
Run: `pytest tests/test_secure_delete.py::test_delete_screenshots_securely -v` → Expect: PASSED

**COMMIT:** `git add tests/test_secure_delete.py src/syncopaid/database_screenshots.py && git commit -m "feat: add secure screenshot deletion with file overwrite"`

---

### Task 2: Add secure event deletion with associated screenshots

**Files:** Test: `tests/test_secure_delete.py` | Impl: `src/syncopaid/database_operations_events.py`

**RED:** Test deleting events also securely deletes associated screenshots.
```python
def test_delete_events_securely_with_screenshots(tmp_path):
    """Verify event deletion cascades to secure screenshot deletion."""
    db_path = tmp_path / "test.db"
    db = Database(str(db_path))

    # Create event
    event = ActivityEvent(
        timestamp="2025-12-21T10:00:00",
        duration_seconds=60.0,
        app="test.exe",
        title="Test Window",
        is_idle=False
    )
    event_id = db.insert_event(event)

    # Create associated screenshot
    screenshot_dir = tmp_path / "screenshots" / "2025-12-21"
    screenshot_dir.mkdir(parents=True)
    screenshot_file = screenshot_dir / "100000.jpg"  # Timestamp-based name
    screenshot_file.write_bytes(b"fake image content")

    screenshot_id = db.insert_screenshot(
        captured_at="2025-12-21T10:00:00",
        file_path=str(screenshot_file),
        window_app="test.exe",
        window_title="Test Window"
    )

    # Delete events securely (should also delete screenshots in same time range)
    deleted = db.delete_events_securely(start_date="2025-12-21", end_date="2025-12-21")

    assert deleted > 0
    assert not screenshot_file.exists(), "Associated screenshot should be deleted"
```
Run: `pytest tests/test_secure_delete.py::test_delete_events_securely_with_screenshots -v` → Expect: FAILED

**GREEN:** Add secure event deletion method.
```python
# In database_operations_events.py, add method:
def delete_events_securely(
    self,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> int:
    """
    Securely delete events and associated screenshots.

    Uses secure_delete pragma for database records and overwrites
    screenshot files before deletion.

    Args:
        start_date: ISO date string (YYYY-MM-DD) for range start
        end_date: ISO date string (YYYY-MM-DD) for range end

    Returns:
        Number of events deleted
    """
    if not start_date and not end_date:
        raise ValueError("Must specify at least start_date or end_date")

    # First, find and delete associated screenshots
    # Screenshots are associated by timestamp overlap
    screenshots = self.get_screenshots(start_date=start_date, end_date=end_date)
    if screenshots:
        screenshot_ids = [s['id'] for s in screenshots]
        self.delete_screenshots_securely(screenshot_ids)

    # Then delete events (secure_delete pragma handles secure deletion)
    return self.delete_events(start_date=start_date, end_date=end_date)
```
Run: `pytest tests/test_secure_delete.py::test_delete_events_securely_with_screenshots -v` → Expect: PASSED

**COMMIT:** `git add tests/test_secure_delete.py src/syncopaid/database_operations_events.py && git commit -m "feat: add secure event deletion with screenshot cascade"`

---

## Verification

- [ ] All tests pass: `python -m pytest tests/test_secure_delete.py -v`
- [ ] Full test suite: `python -m pytest -v`

## Notes

**Screenshot Association:**
- Screenshots are associated with events by timestamp overlap
- When deleting events in a date range, all screenshots in that range are also deleted
- This ensures no orphaned screenshots remain after event deletion
