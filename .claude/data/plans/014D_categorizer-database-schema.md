# 014D: Activity-to-Matter Matching - Database Schema

**Story ID:** 8.4.1

## Task
Add categorization columns to events table and update insert/query methods.

## Context
Events need to store their matter assignment, confidence score, and whether they're flagged for review. This requires schema migration and updated database methods.

## Scope
- Add matter_id, confidence, flagged_for_review columns
- Update insert_event() to accept categorization params
- Update get_events() to return categorization fields

## Key Files

| File | Purpose |
|------|---------|
| `src/syncopaid/database.py` | Schema migration and methods |
| `tests/test_categorizer.py` | Add tests |

## Implementation

### Schema Migration

```python
# src/syncopaid/database.py - in _init_schema()
# Add after existing migrations:

cursor.execute("PRAGMA table_info(events)")
columns = [row[1] for row in cursor.fetchall()]

if 'matter_id' not in columns:
    cursor.execute("ALTER TABLE events ADD COLUMN matter_id INTEGER")
    logging.info("Migration: Added matter_id column")

if 'confidence' not in columns:
    cursor.execute("ALTER TABLE events ADD COLUMN confidence INTEGER DEFAULT 0")
    logging.info("Migration: Added confidence column")

if 'flagged_for_review' not in columns:
    cursor.execute("ALTER TABLE events ADD COLUMN flagged_for_review INTEGER DEFAULT 0")
    logging.info("Migration: Added flagged_for_review column")
```

### Update insert_event

```python
def insert_event(
    self,
    event: ActivityEvent,
    matter_id: Optional[int] = None,
    confidence: int = 0,
    flagged_for_review: bool = False
) -> int:
    # ... existing code ...
    cursor.execute("""
        INSERT INTO events (timestamp, duration_seconds, end_time, app, title, url,
                          is_idle, state, matter_id, confidence, flagged_for_review)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (event.timestamp, event.duration_seconds, end_time,
          event.app, event.title, event.url,
          1 if event.is_idle else 0, state,
          matter_id, confidence, 1 if flagged_for_review else 0))
```

### Update get_events

```python
# In get_events(), add to the events.append() dict:
'matter_id': row['matter_id'] if 'matter_id' in row.keys() else None,
'confidence': row['confidence'] if 'confidence' in row.keys() else 0,
'flagged_for_review': bool(row['flagged_for_review']) if 'flagged_for_review' in row.keys() else False,
```

### Tests

```python
# tests/test_categorizer.py (add)
def test_events_table_has_categorization_columns():
    import sqlite3
    with tempfile.TemporaryDirectory() as tmpdir:
        db = Database(str(Path(tmpdir) / "test.db"))

        conn = sqlite3.connect(Path(tmpdir) / "test.db")
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(events)")
        columns = {row[1] for row in cursor.fetchall()}
        conn.close()

        assert 'matter_id' in columns
        assert 'confidence' in columns
        assert 'flagged_for_review' in columns


def test_insert_event_with_categorization():
    with tempfile.TemporaryDirectory() as tmpdir:
        db = Database(str(Path(tmpdir) / "test.db"))
        from syncopaid.tracker import ActivityEvent

        matter_id = db.insert_matter(matter_number="TEST", description="Test")
        event = ActivityEvent(
            timestamp="2025-12-19T10:00:00",
            duration_seconds=60.0,
            app="test.exe", title="Test"
        )

        db.insert_event(event, matter_id=matter_id, confidence=85)
        events = db.get_events()

        assert events[0]['matter_id'] == matter_id
        assert events[0]['confidence'] == 85
```

## Verification

```bash
pytest tests/test_categorizer.py -v
python -m syncopaid.database
```

## Dependencies
- Task 014C (matching strategies)

## Next Task
After this: `014E_categorizer-flagged-events-methods.md`
