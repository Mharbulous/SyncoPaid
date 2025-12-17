# Handover: Remove Deprecated Status Column

## Task

Remove backward-compatibility `status` column from story_nodes table after confirming nothing depends on it.

## Context

**Migration Timeline:**
- Commit f45c6df: Added three-field system (stage/hold_reason/disposition/human_review)
- Kept `status` column with sync trigger for backward compatibility
- Trigger maintains `status` from three-field values (disposition > hold_reason > stage)

**Why Remove:**
- Reduces schema complexity (single source of truth)
- Eliminates maintenance burden of sync trigger
- Forces all code to use semantic three-field model
- Saves storage (~80 bytes per story at 80 stories = minimal)

**Risk Level:** MEDIUM - Breaking change for any external dependencies

## Prerequisites

⚠️ **Complete handover 035 first** (skill descriptions updated)

## Pre-Flight Checks

### 1. Search for Status Column Usage

```bash
# Check all Python scripts
grep -r "status" .claude/skills --include="*.py" | grep -v "# status"

# Check external tools (if any)
grep -r "status" ai_docs --include="*.py"
grep -r "status" scripts --include="*.py" 2>/dev/null || echo "No scripts dir"

# Check any GUI/visualization code
find . -name "*.py" -type f ! -path "*/venv/*" -exec grep -l "\.status" {} \;
```

Expected: Only references in already-updated vetting/verification scripts that also use three-field

### 2. Verify No External Database Connections

```bash
# Check for database connection strings in config files
grep -r "story-tree.db" . --include="*.json" --include="*.yaml" --include="*.toml"
```

Expected: Only `.claude/skills/*/SKILL.md` documentation

### 3. Check Git History for Status Dependencies

```bash
# Find commits that touch status column (last 30 days)
git log --since="30 days ago" --all -S "status" --oneline | head -20
```

Red flag: Recent commits outside skill migration work

## Key Files to Modify

| File | Lines | Change |
|------|-------|--------|
| `.claude\skills\story-tree\references\schema.sql` | 30-41 | Remove status column definition |
| `.claude\skills\story-tree\references\schema.sql` | 100 | Remove `idx_nodes_status` index |
| `.claude\skills\story-tree\references\schema.sql` | 123-136 | Remove `sync_status_from_fields` trigger |
| `.claude\skills\story-tree\scripts\migrate_to_three_field.py` | All | Delete entire file (migration complete) |

## Implementation

### Step 1: Backup Database

```bash
cp .claude/data/story-tree.db .claude/data/story-tree.db.backup-pre-status-drop
echo "Backup created: $(ls -lh .claude/data/story-tree.db.backup-pre-status-drop)"
```

### Step 2: Update Schema File

**Remove from schema.sql:**

```diff
-    -- Deprecated: 'status' kept for backward compatibility
-    -- Automatically synced via trigger from stage/hold_reason/disposition
-    status TEXT NOT NULL DEFAULT 'concept'
-        CHECK (status IN (
-            'infeasible', 'rejected', 'wishlist',
-            'concept', 'broken', 'blocked', 'refine',
-            'pending', 'approved', 'planned', 'queued', 'paused',
-            'active',
-            'reviewing', 'verifying', 'implemented',
-            'ready', 'polish', 'released',
-            'legacy', 'deprecated', 'archived'
-        )),
```

```diff
-CREATE INDEX IF NOT EXISTS idx_nodes_status ON story_nodes(status);  -- Deprecated, kept for compatibility
```

```diff
--- Sync deprecated 'status' column from three-field system
--- Priority: disposition > hold_reason > stage
-CREATE TRIGGER IF NOT EXISTS sync_status_from_fields
-AFTER UPDATE OF stage, hold_reason, disposition ON story_nodes
-FOR EACH ROW
-BEGIN
-    UPDATE story_nodes SET status =
-        CASE
-            WHEN NEW.disposition IS NOT NULL THEN NEW.disposition
-            WHEN NEW.hold_reason IS NOT NULL THEN NEW.hold_reason
-            ELSE NEW.stage
-        END
-    WHERE id = NEW.id;
-END;
```

### Step 3: Drop from Live Database

```python
python -c "
import sqlite3
conn = sqlite3.connect('.claude/data/story-tree.db')

# Drop trigger first
conn.execute('DROP TRIGGER IF EXISTS sync_status_from_fields')
print('✓ Trigger dropped')

# Drop index
conn.execute('DROP INDEX IF EXISTS idx_nodes_status')
print('✓ Index dropped')

# Drop column (SQLite requires table recreation)
conn.execute('BEGIN TRANSACTION')
conn.execute('''
    CREATE TABLE story_nodes_new (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        capacity INTEGER,
        stage TEXT NOT NULL DEFAULT 'concept'
            CHECK (stage IN (
                'concept', 'approved', 'planned', 'queued', 'active',
                'reviewing', 'verifying', 'implemented', 'ready', 'polish', 'released'
            )),
        hold_reason TEXT DEFAULT NULL
            CHECK (hold_reason IS NULL OR hold_reason IN (
                'pending', 'paused', 'blocked', 'broken', 'refine'
            )),
        disposition TEXT DEFAULT NULL
            CHECK (disposition IS NULL OR disposition IN (
                'rejected', 'infeasible', 'wishlist', 'legacy', 'deprecated', 'archived'
            )),
        human_review INTEGER DEFAULT 0
            CHECK (human_review IN (0, 1)),
        project_path TEXT,
        last_implemented TEXT,
        notes TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now')),
        version INTEGER DEFAULT 1
    )
''')

conn.execute('''
    INSERT INTO story_nodes_new
    SELECT id, title, description, capacity, stage, hold_reason, disposition,
           human_review, project_path, last_implemented, notes, created_at, updated_at, version
    FROM story_nodes
''')

conn.execute('DROP TABLE story_nodes')
conn.execute('ALTER TABLE story_nodes_new RENAME TO story_nodes')
conn.execute('COMMIT')
print('✓ Column dropped')

conn.close()
print('\\nMigration complete!')
"
```

### Step 4: Recreate Indexes/Triggers

```python
python -c "
import sqlite3
conn = sqlite3.connect('.claude/data/story-tree.db')

# Recreate only non-status indexes
indexes = [
    'CREATE INDEX IF NOT EXISTS idx_paths_descendant ON story_paths(descendant_id)',
    'CREATE INDEX IF NOT EXISTS idx_paths_depth ON story_paths(depth)',
    'CREATE INDEX IF NOT EXISTS idx_commits_hash ON story_commits(commit_hash)',
    'CREATE INDEX IF NOT EXISTS idx_vetting_story_a ON vetting_decisions(story_a_id)',
    'CREATE INDEX IF NOT EXISTS idx_vetting_story_b ON vetting_decisions(story_b_id)',
    'CREATE INDEX IF NOT EXISTS idx_active_pipeline ON story_nodes(stage) WHERE disposition IS NULL AND hold_reason IS NULL',
    'CREATE INDEX IF NOT EXISTS idx_held_stories ON story_nodes(hold_reason) WHERE hold_reason IS NOT NULL',
    'CREATE INDEX IF NOT EXISTS idx_disposed_stories ON story_nodes(disposition) WHERE disposition IS NOT NULL',
    'CREATE INDEX IF NOT EXISTS idx_needs_review ON story_nodes(human_review) WHERE human_review = 1',
]

for idx in indexes:
    conn.execute(idx)

# Recreate updated_at trigger
conn.execute('''
    CREATE TRIGGER IF NOT EXISTS story_nodes_updated_at
    AFTER UPDATE ON story_nodes
    FOR EACH ROW
    BEGIN
        UPDATE story_nodes SET updated_at = datetime('now') WHERE id = OLD.id;
    END
''')

conn.commit()
conn.close()
print('✓ Indexes and triggers recreated')
"
```

### Step 5: Delete Migration Script

```bash
rm ".claude/skills/story-tree/scripts/migrate_to_three_field.py"
echo "✓ Migration script deleted (no longer needed)"
```

## Verification

```bash
# Check schema has no status column
python -c "
import sqlite3
conn = sqlite3.connect('.claude/data/story-tree.db')
cursor = conn.cursor()
cursor.execute('PRAGMA table_info(story_nodes)')
columns = [row[1] for row in cursor.fetchall()]
assert 'status' not in columns, 'Status column still exists!'
assert 'stage' in columns, 'Stage column missing!'
print('✓ Schema verified')

# Check trigger removed
cursor.execute(\"SELECT name FROM sqlite_master WHERE type='trigger' AND name='sync_status_from_fields'\")
assert cursor.fetchone() is None, 'Sync trigger still exists!'
print('✓ Trigger removed')

# Check all stories still have stage
cursor.execute('SELECT COUNT(*) FROM story_nodes WHERE stage IS NULL')
assert cursor.fetchone()[0] == 0, 'Stories with NULL stage found!'
print('✓ All stories have valid stage')

conn.close()
print('\\n✅ Cleanup complete and verified')
"
```

## Rollback Plan

If issues discovered:

```bash
# Restore backup
cp .claude/data/story-tree.db.backup-pre-status-drop .claude/data/story-tree.db
echo "Database restored to pre-cleanup state"

# Restore schema.sql from git
git checkout HEAD -- .claude/skills/story-tree/references/schema.sql

# Restore migration script
git checkout HEAD -- .claude/skills/story-tree/scripts/migrate_to_three_field.py
```

## Red Herrings

**Don't touch:**
- Python scripts in skills (they use three-field, not status)
- Other schema tables (story_paths, story_commits, etc.)
- Any `.py` files that mention "status" in comments/docstrings

**Known safe status references:**
- `.claude/skills/story-verification/update_status.py` - Uses `stage`, filename misleading
- Git commit messages mentioning "status"
- Documentation explaining the migration

## Post-Cleanup Benefits

1. **Cleaner queries** - No more `WHERE status = X`, always semantic three-field
2. **Impossible states prevented** - Can't accidentally set status != computed value
3. **Schema simplicity** - 4 fields instead of 5, one less CHECK constraint
4. **Maintenance reduction** - No trigger logic to debug

## When NOT to Proceed

⛔ **Abort if:**
- Pre-flight checks show external dependencies on status column
- Any production system connects to this database
- Team members have local tools querying status
- Recent commits (outside migration) reference status column

In those cases, keep backward compatibility indefinitely or coordinate migration.
