# 029A: Screenshot Analysis Database Schema
Story ID: 15.1

## Task
Add database schema support for screenshot analysis results.

## Context
This is the first sub-plan of 029 (Automatic Screenshot Analysis). Adds the necessary database columns to store AI analysis results for screenshots.

## Scope
- Add `analysis_data` column to screenshots table (TEXT for JSON storage)
- Add `analysis_status` column to screenshots table (pending/completed/failed)
- Implement migration logic in database_schema.py

## Key Files

| File | Purpose |
|------|---------|
| `src/syncopaid/database_schema.py` | Add migration method |
| `tests/test_database_schema.py` | Add migration tests |

## TDD Tasks

### Task 1: Add migration method for analysis columns

**Test first:**
```python
# tests/test_database_schema.py
def test_migrate_screenshots_analysis_columns(db_path, temp_db):
    """Test that analysis columns are added to screenshots table."""
    # First verify columns don't exist
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(screenshots)")
        columns = [row[1] for row in cursor.fetchall()]

    # Run migration
    from syncopaid.database_schema import DatabaseSchema
    schema = DatabaseSchema(db_path)
    schema._migrate_screenshots_table()

    # Verify columns now exist
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(screenshots)")
        columns = [row[1] for row in cursor.fetchall()]

    assert 'analysis_data' in columns
    assert 'analysis_status' in columns
```

**Implementation:**
```python
# src/syncopaid/database_schema.py - Add method to DatabaseSchema class
def _migrate_screenshots_table(self):
    """Apply migrations to screenshots table for analysis support."""
    with self._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(screenshots)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'analysis_data' not in columns:
            cursor.execute("ALTER TABLE screenshots ADD COLUMN analysis_data TEXT")
            logging.info("Migration: Added analysis_data column to screenshots")

        if 'analysis_status' not in columns:
            cursor.execute("ALTER TABLE screenshots ADD COLUMN analysis_status TEXT DEFAULT 'pending'")
            logging.info("Migration: Added analysis_status column to screenshots")

        conn.commit()
```

### Task 2: Call migration during database initialization

**Test first:**
```python
def test_schema_init_runs_migrations(tmp_path):
    """Test that schema initialization runs migrations automatically."""
    db_path = tmp_path / "test.db"

    # Create initial schema
    schema = DatabaseSchema(db_path)
    schema.initialize()

    # Verify analysis columns exist after initialization
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(screenshots)")
        columns = [row[1] for row in cursor.fetchall()]

    assert 'analysis_data' in columns
    assert 'analysis_status' in columns
```

**Implementation:**
- Call `_migrate_screenshots_table()` at the end of `initialize()` method

## Verification

```bash
venv\Scripts\activate
pytest tests/test_database_schema.py -v -k "analysis"
python -m syncopaid.database  # Verify migration runs on existing DB
```

## Notes
- Migration is idempotent - safe to run multiple times
- Uses ALTER TABLE which is SQLite-compatible
- Default status is 'pending' for new screenshots
