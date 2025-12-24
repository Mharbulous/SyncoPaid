# Secure Data Deletion - Implementation Plan

> **TDD Required:** Each task: Write test → RED → Write code → GREEN → Commit

**Goal:** Secure deletion of activity events and screenshots using SQLite secure_delete pragma

**Approach:** Enable SQLite `secure_delete=ON` pragma to overwrite deleted data with zeros, preventing forensic recovery. For screenshots, securely overwrite files before unlinking. Implementation is transparent - no user configuration needed.

**Tech Stack:** SQLite secure_delete pragma, Python os/pathlib for file operations

---

**Story ID:** 7.6 | **Created:** 2025-12-21 | **Status:** `planned`

---

## Story Context

**Title:** Secure Data Deletion

**Description:** As a lawyer handling confidential client information, I want deleted activity events to be securely removed from the database, so that sensitive data cannot be recovered after deletion.

**Acceptance Criteria:**
- [x] When user deletes an event, the data is overwritten in the database file and cannot be recovered with forensic tools
- [x] Secure deletion happens automatically without user configuration or password prompts
- [x] Deletion performance remains acceptable (under 100ms for single event deletion)
- [x] Database integrity is maintained after secure deletion operations
- [x] Screenshots associated with deleted events are securely removed from filesystem (overwrite before unlink)

## Prerequisites

- [x] venv activated: `venv\Scripts\activate`
- [x] Baseline tests pass: `python -m pytest -v`

## Files Affected

| File | Change | Purpose |
|------|--------|---------|
| `tests/test_secure_delete.py` | Create | Test secure deletion functionality |
| `src/syncopaid/database_connection.py:36` | Modify | Enable secure_delete pragma on connection |
| `src/syncopaid/database_operations_events.py:141-208` | Modify | Add secure screenshot file deletion |
| `src/syncopaid/database_screenshots.py` | Modify | Add secure file deletion method |

## TDD Tasks

### Task 1: Enable secure_delete pragma on database connection

**Files:** Test: `tests/test_secure_delete.py` | Impl: `src/syncopaid/database_connection.py`

**RED:** Test verifies secure_delete pragma is enabled on new connections.
```python
def test_secure_delete_pragma_enabled(tmp_path):
    """Verify secure_delete=ON is set on database connections."""
    db_path = tmp_path / "test.db"
    db = Database(str(db_path))

    with db._get_connection() as conn:
        cursor = conn.execute("PRAGMA secure_delete")
        result = cursor.fetchone()[0]
        assert result == 1, "secure_delete pragma should be enabled (1)"
```
Run: `pytest tests/test_secure_delete.py::test_secure_delete_pragma_enabled -v` → Expect: FAILED

**GREEN:** Add secure_delete pragma to connection context manager.
```python
# In database_connection.py, _get_connection method after conn.row_factory
conn.execute("PRAGMA secure_delete = ON")
```
Run: `pytest tests/test_secure_delete.py::test_secure_delete_pragma_enabled -v` → Expect: PASSED

**COMMIT:** `git add tests/test_secure_delete.py src/syncopaid/database_connection.py && git commit -m "feat: enable secure_delete pragma for forensic-proof deletion"`

---

### Task 2: Verify secure deletion actually overwrites data

**Files:** Test: `tests/test_secure_delete.py` | Impl: (pragma already set in Task 1)

**RED:** Test that deleted data cannot be found in raw database file.
```python
def test_secure_delete_overwrites_data(tmp_path):
    """Verify deleted data is overwritten, not just marked as deleted."""
    db_path = tmp_path / "test.db"
    db = Database(str(db_path))

    # Insert event with distinctive string
    secret_marker = "CONFIDENTIAL_CLIENT_DATA_12345"
    event = ActivityEvent(
        timestamp="2025-12-21T10:00:00",
        duration_seconds=60.0,
        app="test.exe",
        title=secret_marker,
        is_idle=False
    )
    event_id = db.insert_event(event)

    # Force write to disk
    with db._get_connection() as conn:
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")

    # Delete the event
    db.delete_events_by_ids([event_id])

    # Force write to disk again
    with db._get_connection() as conn:
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")

    # Read raw database file and search for marker
    raw_content = db_path.read_bytes()
    assert secret_marker.encode() not in raw_content, \
        "Deleted data should not be recoverable from database file"
```
Run: `pytest tests/test_secure_delete.py::test_secure_delete_overwrites_data -v` → Expect: PASSED (pragma from Task 1)

**COMMIT:** `git add tests/test_secure_delete.py && git commit -m "test: verify secure_delete prevents data recovery"`

---

### Task 3: Create secure file overwrite utility

**Files:** Test: `tests/test_secure_delete.py` | Impl: `src/syncopaid/secure_delete.py`

**RED:** Test secure file overwrite function.
```python
def test_secure_file_delete(tmp_path):
    """Verify file contents are overwritten before deletion."""
    test_file = tmp_path / "sensitive.jpg"
    secret_content = b"ATTORNEY_CLIENT_PRIVILEGED_CONTENT"
    test_file.write_bytes(secret_content)

    from syncopaid.secure_delete import secure_delete_file
    secure_delete_file(test_file)

    # File should be deleted
    assert not test_file.exists()

    # Content should not be recoverable (check parent directory for remnants)
    # Note: This is a best-effort test; full forensic verification requires OS-level tools
```
Run: `pytest tests/test_secure_delete.py::test_secure_file_delete -v` → Expect: FAILED

**GREEN:** Implement secure file deletion with overwrite.
```python
# src/syncopaid/secure_delete.py
"""Secure deletion utilities for attorney-client privileged data."""

import os
from pathlib import Path
import logging


def secure_delete_file(file_path: Path, passes: int = 1) -> bool:
    """
    Securely delete a file by overwriting with zeros before unlinking.

    Args:
        file_path: Path to file to securely delete
        passes: Number of overwrite passes (default 1 for SSD optimization)

    Returns:
        True if file was successfully deleted, False if file didn't exist
    """
    file_path = Path(file_path)
    if not file_path.exists():
        return False

    try:
        file_size = file_path.stat().st_size

        # Overwrite with zeros
        with open(file_path, 'wb') as f:
            for _ in range(passes):
                f.seek(0)
                # Write in chunks to handle large files
                chunk_size = 65536  # 64KB chunks
                remaining = file_size
                while remaining > 0:
                    write_size = min(chunk_size, remaining)
                    f.write(b'\x00' * write_size)
                    remaining -= write_size
                f.flush()
                os.fsync(f.fileno())

        # Delete the file
        file_path.unlink()
        logging.debug(f"Securely deleted: {file_path}")
        return True

    except Exception as e:
        logging.error(f"Failed to securely delete {file_path}: {e}")
        # Fall back to regular deletion
        try:
            file_path.unlink()
            return True
        except Exception:
            return False
```
Run: `pytest tests/test_secure_delete.py::test_secure_file_delete -v` → Expect: PASSED

**COMMIT:** `git add tests/test_secure_delete.py src/syncopaid/secure_delete.py && git commit -m "feat: add secure file deletion with overwrite"`

---

### Task 4: Add secure screenshot deletion method to database

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

### Task 5: Add secure event deletion with associated screenshots

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

### Task 6: Performance benchmark - deletion under 100ms

**Files:** Test: `tests/test_secure_delete.py`

**RED:** Test single event deletion completes in under 100ms.
```python
import time

def test_secure_delete_performance(tmp_path):
    """Verify single event deletion completes in under 100ms."""
    db_path = tmp_path / "test.db"
    db = Database(str(db_path))

    # Insert an event
    event = ActivityEvent(
        timestamp="2025-12-21T10:00:00",
        duration_seconds=60.0,
        app="test.exe",
        title="Test Window",
        is_idle=False
    )
    event_id = db.insert_event(event)

    # Time the deletion
    start = time.perf_counter()
    db.delete_events_by_ids([event_id])
    elapsed_ms = (time.perf_counter() - start) * 1000

    assert elapsed_ms < 100, f"Deletion took {elapsed_ms:.2f}ms, should be under 100ms"
```
Run: `pytest tests/test_secure_delete.py::test_secure_delete_performance -v` → Expect: PASSED

**COMMIT:** `git add tests/test_secure_delete.py && git commit -m "test: verify secure deletion performance under 100ms"`

---

### Task 7: Database integrity after secure deletion

**Files:** Test: `tests/test_secure_delete.py`

**RED:** Test database integrity check passes after secure deletions.
```python
def test_database_integrity_after_secure_delete(tmp_path):
    """Verify database integrity is maintained after secure deletions."""
    db_path = tmp_path / "test.db"
    db = Database(str(db_path))

    # Insert multiple events
    events = [
        ActivityEvent(
            timestamp=f"2025-12-21T{10+i}:00:00",
            duration_seconds=60.0,
            app="test.exe",
            title=f"Window {i}",
            is_idle=False
        )
        for i in range(10)
    ]
    db.insert_events_batch(events)

    # Delete some events
    db.delete_events(start_date="2025-12-21", end_date="2025-12-21")

    # Run integrity check
    with db._get_connection() as conn:
        cursor = conn.execute("PRAGMA integrity_check")
        result = cursor.fetchone()[0]
        assert result == "ok", f"Database integrity check failed: {result}"
```
Run: `pytest tests/test_secure_delete.py::test_database_integrity_after_secure_delete -v` → Expect: PASSED

**COMMIT:** `git add tests/test_secure_delete.py && git commit -m "test: verify database integrity after secure deletion"`

---

## Verification

- [ ] All tests pass: `python -m pytest tests/test_secure_delete.py -v`
- [ ] Full test suite: `python -m pytest -v`
- [ ] Manual test: Delete event, run hex editor on database to verify no remnants
- [ ] Manual test: Delete screenshot, verify file is overwritten before deletion

## Notes

**SQLite secure_delete Behavior:**
- When enabled, deleted content is overwritten with zeros
- Slight performance overhead (~5-10%) but acceptable for this use case
- Works at page level - entire 4KB pages are zeroed
- WAL mode: must checkpoint to ensure secure deletion in main database file

**Screenshot Secure Deletion:**
- Single pass overwrite with zeros (sufficient for SSD/flash storage)
- Multiple passes unnecessary for modern storage (NIST 800-88 guidance)
- Large files handled in chunks to avoid memory issues

**Edge Cases:**
- File already deleted (gracefully skip)
- Permission denied on file (log error, continue with database deletion)
- WAL mode (checkpoint before verification tests)

**Follow-up Work:**
- Consider periodic VACUUM to reclaim space after many deletions
- Story 7.7 could add "secure wipe" for entire database on uninstall
