# 045: Import Clients & Matters - Database Schema

## Task
Add `clients` and `matters` tables to the SQLite database with proper migration support.

## Context
SyncoPaid is adding a folder import feature for law firm client/matter data. This task creates the database foundation. The existing `state` field in `events` table already supports matter numbers like `1023.L213`.

## Scope
- Add `clients` table
- Add `matters` table with FK to clients
- Add migration logic in `database_schema.py`
- Follow existing migration pattern (check columns exist before adding)

## Key Files

| File | Purpose |
|------|---------|
| `src/syncopaid/database_schema.py` | Schema definitions, migration logic |
| `src/syncopaid/database.py` | Database class composes mixins |
| `ai_docs/Matter-Import/2025-12-20-Listbot-high-level-import-guide.md` | Reference for data structures |

## Schema Design

```sql
CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_no TEXT,
    client_name TEXT NOT NULL,
    folder_path TEXT,
    confidence TEXT DEFAULT 'medium',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(client_no, client_name)
);

CREATE TABLE IF NOT EXISTS matters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    matter_no TEXT,
    matter_name TEXT NOT NULL,
    folder_path TEXT,
    confidence TEXT DEFAULT 'medium',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(client_id) REFERENCES clients(id),
    UNIQUE(client_id, matter_no, matter_name)
);

CREATE INDEX IF NOT EXISTS idx_matters_client ON matters(client_id);
CREATE INDEX IF NOT EXISTS idx_clients_client_no ON clients(client_no);
```

## Implementation Steps

1. Add `_create_clients_table()` method to `SchemaMixin`
2. Add `_create_matters_table()` method to `SchemaMixin`
3. Call both from `_init_schema()` after screenshots table
4. Add indices for query performance

## Pattern to Follow

See `_create_screenshots_table()` at line 104-126 in `database_schema.py` for the pattern:
- Use `CREATE TABLE IF NOT EXISTS`
- Create indices after table
- No migration needed for new tables (only for altering existing)

## Verification

```bash
# Activate venv first
venv\Scripts\activate

# Test database module
python -m syncopaid.database

# Verify tables created
sqlite3 "%LOCALAPPDATA%\SyncoPaid\SyncoPaid.db" ".schema clients"
sqlite3 "%LOCALAPPDATA%\SyncoPaid\SyncoPaid.db" ".schema matters"
```

## Next Task
After this: `046_import-clients-matters-folder-parser.md`
