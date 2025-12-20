# 033: Matter/Client Database - Schema Tables

## Task
Add `clients` and `matters` tables to the SQLite database schema.

## Context
First step for the Matter/Client Database feature. Creates the foundational tables that will store client and matter data for AI billing categorization.

## Scope
- Add `clients` table with: id, name, notes, created_at
- Add `matters` table with: id, matter_number, client_id (FK), description, status, created_at, updated_at
- Add index on matters.status

## Key Files

| File | Purpose |
|------|---------|
| `src/syncopaid/database.py` | Add table creation in _init_schema() |
| `tests/test_matter_client.py` | Create test file |

## Implementation

### Step 1: Create test file

```python
# tests/test_matter_client.py (CREATE)
"""Test matter and client database functionality."""
import sqlite3
import tempfile
from pathlib import Path
from syncopaid.database import Database

def test_clients_table_exists():
    """Verify clients table is created with correct schema."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='clients'")
        result = cursor.fetchone()
        conn.close()

        assert result is not None, "clients table should exist"

def test_matters_table_exists():
    """Verify matters table is created with correct schema."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='matters'")
        result = cursor.fetchone()
        conn.close()

        assert result is not None, "matters table should exist"

if __name__ == "__main__":
    test_clients_table_exists()
    test_matters_table_exists()
    print("All tests passed!")
```

### Step 2: Add clients table

```python
# src/syncopaid/database.py - in _init_schema() after screenshots table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        notes TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    )
""")
```

### Step 3: Add matters table

```python
# src/syncopaid/database.py - in _init_schema() after clients table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS matters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        matter_number TEXT NOT NULL UNIQUE,
        client_id INTEGER,
        description TEXT,
        status TEXT NOT NULL DEFAULT 'active',
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now')),
        FOREIGN KEY (client_id) REFERENCES clients(id)
    )
""")

cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_matters_status
    ON matters(status)
""")
```

## Verification

```bash
venv\Scripts\activate
python tests/test_matter_client.py
python -m syncopaid.database  # Verify module runs
```

## Dependencies
None - this is the first sub-plan.

## Next Task
After this: `034_matter-client-crud-methods.md`
