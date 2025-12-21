# 012E: Command Line Tracking - Database Schema
Story ID: 1.1.2


## Task
Add `cmdline` column to events table with migration support, update insert and query methods.

## Context
Final step for command line tracking. Stores cmdline as JSON string in SQLite, with automatic migration for existing databases.

## Scope
- Add cmdline column to events table schema
- Add migration for existing databases
- Update insert_event() to serialize cmdline as JSON
- Update insert_events_batch() for cmdline
- Update get_events() to return cmdline

## Key Files

| File | Purpose |
|------|---------|
| `src/syncopaid/database.py` | Schema and methods |
| `tests/test_cmdline_tracking.py` | Add tests |

## Implementation

### Schema Migration

```python
# src/syncopaid/database.py - in _init_schema()
# After existing migrations, add:
cursor.execute("PRAGMA table_info(events)")
columns = [row[1] for row in cursor.fetchall()]
if 'cmdline' not in columns:
    cursor.execute("ALTER TABLE events ADD COLUMN cmdline TEXT")
    logging.info("Database migration: Added cmdline column to events table")
```

### Update insert_event

```python
# src/syncopaid/database.py - in insert_event()
import json

# Serialize cmdline to JSON
cmdline = getattr(event, 'cmdline', None)
cmdline_json = json.dumps(cmdline) if cmdline else None

# Include in INSERT (add cmdline to VALUES)
cursor.execute("""
    INSERT INTO events (timestamp, duration_seconds, end_time, app, title, url, cmdline, is_idle, state)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (event.timestamp, event.duration_seconds, end_time,
      event.app, event.title, event.url, cmdline_json,
      1 if event.is_idle else 0, state))
```

### Update insert_events_batch

```python
# src/syncopaid/database.py - in insert_events_batch()
import json

cursor.executemany("""
    INSERT INTO events (timestamp, duration_seconds, end_time, app, title, url, cmdline, is_idle, state)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
""", [
    (e.timestamp, e.duration_seconds, getattr(e, 'end_time', None),
     e.app, e.title, e.url,
     json.dumps(getattr(e, 'cmdline', None)) if getattr(e, 'cmdline', None) else None,
     1 if e.is_idle else 0, getattr(e, 'state', 'Active'))
    for e in events
])
```

### Update get_events

```python
# src/syncopaid/database.py - in get_events() results loop
cmdline = row['cmdline'] if 'cmdline' in row.keys() else None

events.append({
    # ... existing fields ...
    'cmdline': cmdline,
    # ... rest of fields ...
})
```

### Tests

```python
# tests/test_cmdline_tracking.py (add)
import tempfile
import os

def test_database_cmdline_column_exists():
    from syncopaid.database import Database
    import sqlite3

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        db = Database(db_path)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(events)")
        columns = [row[1] for row in cursor.fetchall()]
        conn.close()

        assert 'cmdline' in columns


def test_database_insert_event_with_cmdline():
    from syncopaid.database import Database
    from syncopaid.tracker import ActivityEvent

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        db = Database(db_path)

        event = ActivityEvent(
            timestamp="2025-12-19T10:00:00+00:00",
            duration_seconds=60.0,
            app="chrome.exe",
            title="Test",
            cmdline=["chrome.exe", "--profile-directory=Work"]
        )

        db.insert_event(event)
        events = db.get_events()

        assert len(events) == 1
        assert 'cmdline' in events[0]
        assert '"--profile-directory=Work"' in events[0]['cmdline']
```

## Verification

```bash
venv\Scripts\activate
pytest tests/test_cmdline_tracking.py -v
python -m syncopaid.database  # Verify module runs
```

## Final Verification

After all cmdline sub-plans complete:

```bash
python -m pytest -v
python -m syncopaid.tracker  # 30s test
python -m syncopaid.database
```

## Dependencies
- Task 012D (TrackerLoop integration)

## Notes
This completes the Process Command Line Tracking feature (original story 1.1.2).

All acceptance criteria should now be met:
- get_active_window() captures cmdline
- ActivityEvent includes cmdline field
- Database schema has cmdline column with migration
- Sensitive paths are redacted
- Multiple app instances are distinguishable
