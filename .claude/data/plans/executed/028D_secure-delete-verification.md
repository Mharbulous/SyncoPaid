# Secure Data Deletion - Performance & Integrity Verification

> **TDD Required:** Each task: Write test → RED → Write code → GREEN → Commit

**Goal:** Verify secure deletion meets performance requirements and maintains database integrity

**Approach:** Add performance benchmark and integrity tests

**Tech Stack:** SQLite, Python time module

---

**Story ID:** 7.6 | **Created:** 2025-12-21 | **Status:** `planned`

**Parent Plan:** 028_secure-data-deletion.md

---

## Story Context

**Title:** Secure Data Deletion - Performance & Integrity Verification

**Description:** Verify that secure deletion operations complete within acceptable time limits and maintain database integrity.

**Acceptance Criteria:**
- [x] Deletion performance remains acceptable (under 100ms for single event deletion)
- [x] Database integrity is maintained after secure deletion operations

## Prerequisites

- [x] venv activated: `venv\Scripts\activate`
- [x] Baseline tests pass: `python -m pytest -v`
- [x] Sub-plan 028A completed (secure_delete pragma enabled)
- [x] Sub-plan 028B completed (secure_delete_file utility)
- [x] Sub-plan 028C completed (database operations)

## Files Affected

| File | Change | Purpose |
|------|--------|---------|
| `tests/test_secure_delete.py` | Modify | Add performance and integrity tests |

## TDD Tasks

### Task 1: Performance benchmark - deletion under 100ms

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

### Task 2: Database integrity after secure deletion

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

**Performance Considerations:**
- secure_delete pragma adds ~5-10% overhead which is acceptable
- Single event deletion with file overwrite should complete well under 100ms
- For bulk deletions, performance may vary based on number of associated files

**Integrity Verification:**
- PRAGMA integrity_check verifies database structure is valid
- WAL checkpointing ensures all changes are persisted to main database file
