# 022A: Import Clients & Matters - Database Schema

## Task
Add `clients` and `matters` tables, plus migrate `events` table to have separate `client` and `matter` columns.

## Context
SyncoPaid adapts to the user's existing folder naming conventions. When a lawyer imports their client folders, SyncoPaid will display those exact names when assigning time. This requires:

1. Tables to store imported clients/matters
2. New columns on `events` to assign tracked time to client/matter (separate from system `state`)

**Design principle**: Mirror the user's folder structure exactly—don't impose a naming scheme.

## Scope
- Add `clients` table
- Add `matters` table with FK to clients
- Add `client` and `matter` columns to `events` table (migration)
- Keep existing `state` column for system states only (`Active`, `Inactive`, etc.)

## Key Files

| File | Purpose |
|------|---------|
| `src/syncopaid/database_schema.py` | Schema definitions, migration logic |
| `src/syncopaid/database.py` | Database class composes mixins |
| `ai_docs/Matter-Import/2025-12-20-Listbot-high-level-import-guide.md` | Reference for data structures |

## Schema Design

### New Tables

```sql
-- Clients table: stores imported client folder names
CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    display_name TEXT NOT NULL,      -- Exact folder name (user's naming)
    folder_path TEXT,                 -- Original import path
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(display_name)
);

-- Matters table: stores imported matter folder names
CREATE TABLE IF NOT EXISTS matters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    display_name TEXT NOT NULL,       -- Exact folder name (user's naming)
    folder_path TEXT,                  -- Original import path
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(client_id) REFERENCES clients(id),
    UNIQUE(client_id, display_name)
);

CREATE INDEX IF NOT EXISTS idx_matters_client ON matters(client_id);
```

### Events Table Migration

Add two new columns to assign time:

```sql
-- Migration: Add client column
ALTER TABLE events ADD COLUMN client TEXT;

-- Migration: Add matter column
ALTER TABLE events ADD COLUMN matter TEXT;
```

After migration, `events` will have:
- `state`: System states only (`Active`, `Inactive`, `Paused`, `On-break`, etc.)
- `client`: Display name from imported clients (nullable, user assigns)
- `matter`: Display name from imported matters (nullable, user assigns)

## Implementation Steps

1. Add `_create_clients_table()` method to `SchemaMixin`
2. Add `_create_matters_table()` method to `SchemaMixin`
3. Call both from `_init_schema()` after screenshots table
4. Add `client` and `matter` migration in `_migrate_events_table()`

## Migration Logic

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

## Pattern to Follow

See `_create_screenshots_table()` at line 104-126 in `database_schema.py` for new table pattern.
See `_migrate_events_table()` at lines 58-85 for migration pattern (check column exists before adding).

## Data Flow

```
User's Folders          Import Dialog         Database
─────────────          ─────────────         ────────
Clients/                                      clients table
├── Smith, John/   →   Preview Table   →     id=1, display_name="Smith, John"
│   ├── Real Estate/                         matters table
│   └── Divorce/                             id=1, client_id=1, display_name="Real Estate"
└── Johnson Corp/                            id=2, client_id=1, display_name="Divorce"
    └── Contract/                            ...

                    Time Assignment UI
                    ─────────────────
                    Event #123
                    Client: [Smith, John    ▼]  ← populated from clients table
                    Matter: [Real Estate    ▼]  ← filtered by selected client
```

## Verification

```bash
# Activate venv first
venv\Scripts\activate

# Test database module
python -m syncopaid.database

# Verify tables created
sqlite3 "%LOCALAPPDATA%\SyncoPaid\SyncoPaid.db" ".schema clients"
sqlite3 "%LOCALAPPDATA%\SyncoPaid\SyncoPaid.db" ".schema matters"

# Verify events migration
sqlite3 "%LOCALAPPDATA%\SyncoPaid\SyncoPaid.db" "PRAGMA table_info(events);"
# Should show: client TEXT, matter TEXT columns
```

## Next Task
After this: `022B_import-clients-matters-folder-parser.md`
