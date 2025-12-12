# Story Tree Migration Guide: JSON to SQLite

This guide provides instructions for migrating from the v1.x JSON-based story tree to the v2.0 SQLite-based storage.

## Overview

**v1.x Storage:** `.claude/skills/story-tree/story-tree.json`
**v2.0 Storage:** `.claude/data/story-tree.db`

**Why separate locations:** The skill definition files (SKILL.md, schema.sql, lib/, docs/) are meant to be copied between projects. The database contains project-specific story data and should never be copied.

The migration process:
1. Parse the JSON file
2. Create SQLite database with schema
3. Insert all stories into `story_nodes` table
4. Populate `story_paths` closure table
5. Copy commit data to `story_node_commits` table
6. Copy metadata to `metadata` table
7. Verify migration
8. Delete JSON file (optional)

## Prerequisites

- SQLite3 CLI installed (`sqlite3 --version`)
- Existing `story-tree.json` file
- Write access to skill directory

## Migration Steps

### Step 1: Backup Existing JSON

```bash
cp .claude/skills/story-tree/story-tree.json .claude/skills/story-tree/story-tree.json.backup
```

### Step 2: Create SQLite Database

```bash
# Create data directory if it doesn't exist
mkdir -p .claude/data

# Create database with schema
sqlite3 .claude/data/story-tree.db < .claude/skills/story-tree/schema.sql
```

### Step 3: Run Migration

Claude will execute this migration by reading the JSON and executing SQL commands:

```bash
# Claude reads story-tree.json and executes:

# For each node in the tree (recursive walk):
sqlite3 stories.db "
INSERT INTO story_nodes (id, title, description, capacity, status, project_path, last_implemented, created_at, updated_at)
VALUES ('NODE_ID', 'NODE_TITLE', 'NODE_DESC', CAPACITY, 'STATUS', 'PATH', 'LAST_IMPL', datetime('now'), datetime('now'));
"

# For each node, populate closure table (self + all ancestors):
sqlite3 stories.db "
INSERT INTO story_paths (ancestor_id, descendant_id, depth)
SELECT ancestor_id, 'NEW_ID', depth + 1
FROM story_paths WHERE descendant_id = 'PARENT_ID'
UNION ALL SELECT 'NEW_ID', 'NEW_ID', 0;
"

# For each implementedCommits array entry:
sqlite3 stories.db "
INSERT INTO story_node_commits (story_id, commit_hash, commit_message)
VALUES ('STORY_ID', 'COMMIT_HASH', NULL);
"

# Copy metadata:
sqlite3 stories.db "
INSERT INTO metadata (key, value) VALUES ('version', '2.0.0');
INSERT INTO metadata (key, value) VALUES ('lastUpdated', 'FROM_JSON');
INSERT INTO metadata (key, value) VALUES ('lastAnalyzedCommit', 'FROM_JSON');
"
```

### Step 4: Verify Migration

```bash
# Count stories
sqlite3 .claude/data/story-tree.db "SELECT COUNT(*) as story_count FROM story_nodes;"

# Verify closure table integrity
sqlite3 .claude/data/story-tree.db "
SELECT COUNT(*) as orphaned FROM story_nodes s
WHERE NOT EXISTS (
    SELECT 1 FROM story_paths st
    WHERE st.descendant_id = s.id AND st.ancestor_id = s.id AND st.depth = 0
);
"
# Should return 0

# Compare node counts
JSON_COUNT=$(cat .claude/skills/story-tree/story-tree.json | grep -o '"id":' | wc -l)
DB_COUNT=$(sqlite3 .claude/data/story-tree.db "SELECT COUNT(*) FROM story_nodes;")
echo "JSON nodes: $JSON_COUNT, DB nodes: $DB_COUNT"
# Should match

# Verify tree structure
sqlite3 .claude/data/story-tree.db "
SELECT s.id, s.title,
    (SELECT MIN(depth) FROM story_paths WHERE descendant_id = s.id) as depth,
    (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) as children
FROM story_nodes s
ORDER BY s.id
LIMIT 10;
"
```

### Step 5: Delete JSON File (After Verification)

```bash
rm .claude/skills/story-tree/story-tree.json
```

## Migration Algorithm Detail

### JSON Structure (v1.x)

```json
{
  "version": "1.0.0",
  "lastUpdated": "2025-12-11T00:00:00Z",
  "lastAnalyzedCommit": "abc123",
  "root": {
    "id": "root",
    "story": "Title",
    "description": "Description",
    "capacity": 10,
    "status": "active",
    "implementedCommits": ["abc123", "def456"],
    "children": [
      {
        "id": "1.1",
        "story": "Child",
        ...
        "children": [...]
      }
    ]
  }
}
```

### Recursive Walk Algorithm

```python
def migrate_node(node, parent_id=None):
    # Insert story
    db.execute("""
        INSERT INTO story_nodes (id, title, description, capacity, status,
                           project_path, last_implemented, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
    """, (node['id'], node['story'], node['description'], node['capacity'],
          node['status'], node.get('projectPath'), node.get('lastImplemented')))

    # Populate closure table
    if parent_id:
        # Copy all ancestor relationships from parent, incrementing depth
        db.execute("""
            INSERT INTO story_paths (ancestor_id, descendant_id, depth)
            SELECT ancestor_id, ?, depth + 1
            FROM story_paths WHERE descendant_id = ?
        """, (node['id'], parent_id))

    # Add self-reference
    db.execute("""
        INSERT INTO story_paths (ancestor_id, descendant_id, depth)
        VALUES (?, ?, 0)
    """, (node['id'], node['id']))

    # Copy commits
    for commit in node.get('implementedCommits', []):
        db.execute("""
            INSERT INTO story_node_commits (story_id, commit_hash)
            VALUES (?, ?)
        """, (node['id'], commit))

    # Recurse to children
    for child in node.get('children', []):
        migrate_node(child, node['id'])

# Start migration
migrate_node(json_data['root'])

# Copy metadata
db.execute("INSERT INTO metadata (key, value) VALUES (?, ?)",
           ('version', '2.0.0'))
db.execute("INSERT INTO metadata (key, value) VALUES (?, ?)",
           ('lastUpdated', json_data['lastUpdated']))
db.execute("INSERT INTO metadata (key, value) VALUES (?, ?)",
           ('lastAnalyzedCommit', json_data.get('lastAnalyzedCommit', '')))
```

## Closure Table Population Example

For a simple tree: `root → 1.1 → 1.1.1`

**Step 1: Insert root**
```sql
INSERT INTO story_nodes (id, ...) VALUES ('root', ...);
INSERT INTO story_paths VALUES ('root', 'root', 0);
```

Closure table:
| ancestor_id | descendant_id | depth |
|-------------|---------------|-------|
| root | root | 0 |

**Step 2: Insert 1.1 (parent=root)**
```sql
INSERT INTO story_nodes (id, ...) VALUES ('1.1', ...);

-- Copy ancestors from parent, increment depth
INSERT INTO story_paths (ancestor_id, descendant_id, depth)
SELECT ancestor_id, '1.1', depth + 1
FROM story_paths WHERE descendant_id = 'root';

-- Add self-reference
INSERT INTO story_paths VALUES ('1.1', '1.1', 0);
```

Closure table:
| ancestor_id | descendant_id | depth |
|-------------|---------------|-------|
| root | root | 0 |
| root | 1.1 | 1 |
| 1.1 | 1.1 | 0 |

**Step 3: Insert 1.1.1 (parent=1.1)**
```sql
INSERT INTO story_nodes (id, ...) VALUES ('1.1.1', ...);

-- Copy ancestors from parent, increment depth
INSERT INTO story_paths (ancestor_id, descendant_id, depth)
SELECT ancestor_id, '1.1.1', depth + 1
FROM story_paths WHERE descendant_id = '1.1';

-- Add self-reference
INSERT INTO story_paths VALUES ('1.1.1', '1.1.1', 0);
```

Final closure table:
| ancestor_id | descendant_id | depth |
|-------------|---------------|-------|
| root | root | 0 |
| root | 1.1 | 1 |
| root | 1.1.1 | 2 |
| 1.1 | 1.1 | 0 |
| 1.1 | 1.1.1 | 1 |
| 1.1.1 | 1.1.1 | 0 |

## Troubleshooting

### Problem: Foreign Key Constraint Failed

```
Error: FOREIGN KEY constraint failed
```

**Cause:** Trying to insert a child before its parent exists.
**Solution:** Always insert parent nodes before children (depth-first or breadth-first traversal).

### Problem: Duplicate Primary Key

```
Error: UNIQUE constraint failed: stories.id
```

**Cause:** Duplicate node IDs in JSON file.
**Solution:** Check JSON for duplicate IDs before migration.

### Problem: Missing Self-Reference

```sql
SELECT id FROM story_nodes WHERE id NOT IN (
    SELECT descendant_id FROM story_paths WHERE depth = 0
);
```

**Solution:** Re-run migration or manually add:
```sql
INSERT INTO story_paths VALUES ('missing_id', 'missing_id', 0);
```

### Problem: Broken Ancestor Chain

```sql
-- Find nodes with incomplete ancestor chains
SELECT s.id FROM story_nodes s
WHERE NOT EXISTS (
    SELECT 1 FROM story_paths st
    WHERE st.descendant_id = s.id AND st.ancestor_id = 'root'
) AND s.id != 'root';
```

**Solution:** Re-run migration from scratch.

## Rollback

If migration fails and you need to rollback:

```bash
# Remove database
rm .claude/data/story-tree.db

# Restore backup
mv .claude/skills/story-tree/story-tree.json.backup .claude/skills/story-tree/story-tree.json
```

## Post-Migration

After successful migration:

1. **Update skill invocations** to use SQLite commands instead of JSON file operations
2. **Test story generation** - run "Update story tree" to verify
3. **Verify export** - run "Export story tree to JSON" to confirm data integrity
4. **Remove backup** after confirming everything works:
   ```bash
   rm .claude/skills/story-tree/story-tree.json.backup
   ```

## Version History

- v1.0.0 (2025-12-11): Initial migration guide for JSON to SQLite transition
