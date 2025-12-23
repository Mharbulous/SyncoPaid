# Secure Data Deletion - Pragma Setup

> **TDD Required:** Each task: Write test → RED → Write code → GREEN → Commit

**Goal:** Enable SQLite secure_delete pragma for forensic-proof data deletion

**Approach:** Add secure_delete pragma to database connection and verify it works

**Tech Stack:** SQLite secure_delete pragma

---

**Story ID:** 7.6 | **Created:** 2025-12-21 | **Status:** `planned`

**Parent Plan:** 028_secure-data-deletion.md

---

## Story Context

**Title:** Secure Data Deletion - Pragma Setup

**Description:** Enable SQLite secure_delete pragma on database connections to ensure deleted data is overwritten with zeros.

**Acceptance Criteria:**
- [x] secure_delete pragma is enabled on all database connections
- [x] Deleted data is overwritten and cannot be found in raw database file

## Prerequisites

- [x] venv activated: `venv\Scripts\activate`
- [x] Baseline tests pass: `python -m pytest -v`

## Files Affected

| File | Change | Purpose |
|------|--------|---------|
| `tests/test_secure_delete.py` | Create | Test secure deletion functionality |
| `src/syncopaid/database_connection.py:36` | Modify | Enable secure_delete pragma on connection |

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

## Verification

- [ ] All tests pass: `python -m pytest tests/test_secure_delete.py -v`
- [ ] Full test suite: `python -m pytest -v`

## Notes

**SQLite secure_delete Behavior:**
- When enabled, deleted content is overwritten with zeros
- Slight performance overhead (~5-10%) but acceptable for this use case
- Works at page level - entire 4KB pages are zeroed
- WAL mode: must checkpoint to ensure secure deletion in main database file
