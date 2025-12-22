# 022A1: Create Clients & Matters Tables
Story ID: 8.1.2

## Task
Add `clients` and `matters` tables to the database schema.

## Context
This is sub-plan 1 of 2 for story 8.1.2. Creates the new tables that will store imported client/matter data.

## Key Files

| File | Purpose |
|------|---------|
| `src/syncopaid/database_schema.py` | Schema definitions (add new table methods) |

## TDD Implementation

### TDD Task 1: Create clients and matters tables

**Test (RED)**:
```python
# tests/test_database_schema.py
def test_clients_table_exists(db_connection):
    """Verify clients table is created with correct schema."""
    cursor = db_connection.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='clients'"
    )
    schema = cursor.fetchone()
    assert schema is not None
    assert 'display_name TEXT NOT NULL' in schema[0]
    assert 'folder_path TEXT' in schema[0]
    assert 'created_at TEXT' in schema[0]
    assert 'UNIQUE(display_name)' in schema[0]

def test_matters_table_exists(db_connection):
    """Verify matters table is created with correct schema."""
    cursor = db_connection.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='matters'"
    )
    schema = cursor.fetchone()
    assert schema is not None
    assert 'client_id INTEGER NOT NULL' in schema[0]
    assert 'display_name TEXT NOT NULL' in schema[0]
    assert 'FOREIGN KEY(client_id) REFERENCES clients(id)' in schema[0]
    assert 'UNIQUE(client_id, display_name)' in schema[0]
```

**Implementation (GREEN)**:
1. Add `_create_clients_table()` method to `SchemaMixin`:
```python
def _create_clients_table(self) -> None:
    """Create clients table for imported client folder names."""
    cursor = self._conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            display_name TEXT NOT NULL,
            folder_path TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(display_name)
        )
    """)
    self._conn.commit()
    logging.debug("Ensured clients table exists")
```

2. Add `_create_matters_table()` method to `SchemaMixin`:
```python
def _create_matters_table(self) -> None:
    """Create matters table for imported matter folder names."""
    cursor = self._conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS matters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            display_name TEXT NOT NULL,
            folder_path TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(client_id) REFERENCES clients(id),
            UNIQUE(client_id, display_name)
        )
    """)
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_matters_client ON matters(client_id)"
    )
    self._conn.commit()
    logging.debug("Ensured matters table exists")
```

3. Update `_init_schema()` to call new methods after screenshots table.

## Verification
```bash
pytest tests/test_database_schema.py -v -k "clients or matters"
```

## Next
After this: `022A2_migrate-events-client-matter-columns.md`
