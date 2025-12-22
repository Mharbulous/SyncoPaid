# 022A2: Migrate Events Table - Add Client/Matter Columns
Story ID: 8.1.2

## Task
Add `client` and `matter` columns to the existing `events` table via migration.

## Context
This is sub-plan 2 of 2 for story 8.1.2. Adds columns to the events table so tracked time can be assigned to clients/matters.

## Key Files

| File | Purpose |
|------|---------|
| `src/syncopaid/database_schema.py` | Migration logic in `_migrate_events_table()` |

## TDD Implementation

### TDD Task 1: Migrate events table with client/matter columns

**Test (RED)**:
```python
# tests/test_database_schema.py
def test_events_table_has_client_column(db_connection):
    """Verify events table has client column after migration."""
    cursor = db_connection.execute("PRAGMA table_info(events)")
    columns = {row[1] for row in cursor.fetchall()}
    assert 'client' in columns

def test_events_table_has_matter_column(db_connection):
    """Verify events table has matter column after migration."""
    cursor = db_connection.execute("PRAGMA table_info(events)")
    columns = {row[1] for row in cursor.fetchall()}
    assert 'matter' in columns

def test_events_client_matter_columns_nullable(db_connection):
    """Verify client/matter columns allow NULL (user assigns later)."""
    # Insert event without client/matter
    cursor = db_connection.cursor()
    cursor.execute("""
        INSERT INTO events (window_title, process_name, timestamp, state)
        VALUES ('Test', 'test.exe', datetime('now'), 'Active')
    """)
    db_connection.commit()

    # Verify NULL values accepted
    cursor.execute("SELECT client, matter FROM events WHERE window_title='Test'")
    row = cursor.fetchone()
    assert row[0] is None  # client is NULL
    assert row[1] is None  # matter is NULL
```

**Implementation (GREEN)**:
Add to `_migrate_events_table()` in `database_schema.py`:
```python
# Migration: Add client column for time assignment
if 'client' not in columns:
    cursor.execute("ALTER TABLE events ADD COLUMN client TEXT")
    logging.info("Database migration: Added client column to events table")

# Migration: Add matter column for time assignment
if 'matter' not in columns:
    cursor.execute("ALTER TABLE events ADD COLUMN matter TEXT")
    logging.info("Database migration: Added matter column to events table")
```

## Verification
```bash
pytest tests/test_database_schema.py -v -k "events"
python -m syncopaid.database
```

## Schema After Migration

The `events` table will have:
- `state`: System states only (`Active`, `Inactive`, `Paused`, `On-break`, etc.)
- `client`: Display name from imported clients (nullable, user assigns)
- `matter`: Display name from imported matters (nullable, user assigns)

## Next Story
After this plan completes, proceed to `022B_import-clients-matters-folder-parser.md`
