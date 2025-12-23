# Common Mistakes

## 1. Ignoring Priority Algorithm

**Wrong:** "Node 1.3.2.1 is empty (0/3), so highest priority."

**Right:** Depth takes precedence over fill rate. Shallowest node wins.

## 2. Not Matching Commits First

Always run git analysis before generation. Update stage from 'active' or 'reviewing' → 'implemented' if match found.

## 3. Uniform Capacity

| Story Type | Capacity |
|------------|----------|
| Simple UI component | 2-3 |
| Feature with workflow | 5-8 |
| Major feature area | 8-12 |
| Cross-cutting concern | 10-15 |

## 4. Wrong SQL Table Names

**Correct names:**
- `story_nodes` (not `stories`)
- `story_paths` (not `story_tree`)
- `story_commits` (not `story_node_commits`)
- Column: `title` (not `story` or `name`)

## 5. Using sqlite3 CLI Command

**sqlite3 CLI is NOT available.** Use Python's sqlite3 module:
```python
python -c "
import sqlite3
conn = sqlite3.connect('.claude/data/story-tree.db')
cursor = conn.cursor()
cursor.execute('SELECT * FROM story_nodes')
print(cursor.fetchall())
conn.close()
"
```

## 6. Wrong Script Paths

Scripts are in the skill directory:
```bash
python .claude/skills/story-tree/scripts/tree-view.py
```

## 7. Wrong Story ID Format for Root Children

**Wrong:** Creating root-level epics with decimal IDs like `8.6`, `8.7`, `root.1`

**Right:** Root children (primary epics) MUST have plain integer IDs.

| Level | Parent | Correct ID | Wrong ID |
|-------|--------|------------|----------|
| Root | None | `root` | - |
| Level 1 | `root` | `16`, `17`, `18` | `8.6`, `root.16` |
| Level 2+ | Non-root | `16.1`, `8.4.2` | - |

**To find next available root child ID:**
```python
python -c "
import sqlite3
conn = sqlite3.connect('.claude/data/story-tree.db')
existing = conn.execute('''
    SELECT CAST(sn.id AS INTEGER) FROM story_nodes sn
    JOIN story_paths sp ON sn.id = sp.descendant_id
    WHERE sp.ancestor_id = 'root' AND sp.depth = 1
    AND sn.id GLOB '[0-9]*' AND sn.id NOT LIKE '%.%'
''').fetchall()
existing_ints = sorted([r[0] for r in existing])
next_id = 1
for e in existing_ints:
    if e == next_id: next_id = e + 1
print(next_id)
conn.close()
"
```

## 8. Creating Orphaned Nodes

**Wrong:** Inserting into `story_nodes` without adding `story_paths` entries

**Right:** Always insert both:
1. The node into `story_nodes`
2. Self-path (depth=0) into `story_paths`
3. All ancestor paths into `story_paths`

```python
# Correct insertion pattern
conn.execute('''
    INSERT INTO story_nodes (id, title, description, stage, created_at, updated_at)
    VALUES (?, ?, ?, 'concept', datetime('now'), datetime('now'))
''', (new_id, title, description))

# Self-path + ancestor paths
conn.execute('''
    INSERT INTO story_paths (ancestor_id, descendant_id, depth)
    SELECT ancestor_id, ?, depth + 1 FROM story_paths WHERE descendant_id = ?
    UNION ALL SELECT ?, ?, 0
''', (new_id, parent_id, new_id, new_id))
```

## 9. Parent-ID Mismatch

**Wrong:** Story `3.5` as child of `8` in `story_paths`

**Right:** Story ID prefix MUST match parent. If moving a story, use `move_story()` to properly rename.

| Story ID | Must Have Parent |
|----------|------------------|
| `5` | `root` |
| `5.2` | `5` |
| `5.2.3` | `5.2` |

**Detection:** Run `validate_tree_structure()` to find mismatches.

## 10. Missing Self-Paths

**Wrong:** Node exists in `story_nodes` but has no `depth=0` entry in `story_paths`

**Right:** Every node MUST have a self-referencing path with `depth=0`.

```python
# Fix missing self-path
conn.execute('''
    INSERT OR IGNORE INTO story_paths (ancestor_id, descendant_id, depth)
    VALUES (?, ?, 0)
''', (node_id, node_id))
```

## 11. Manual ID Renaming Without Path Updates

**Wrong:** Directly updating `story_nodes.id` without updating `story_paths`

**Right:** Use `rename_story()` which updates all references:
- `story_nodes.id`
- `story_paths.ancestor_id` and `descendant_id`
- `story_commits.story_id`
- `vetting_decisions.story_a_id` and `story_b_id`

```python
import sys
sys.path.insert(0, '.claude/skills/story-tree/utility')
from story_db_common import get_connection, rename_story

conn = get_connection()
conn.execute('PRAGMA foreign_keys = OFF')
renames = rename_story(conn, '8.6', '16')
conn.execute('PRAGMA foreign_keys = ON')
conn.commit()
```

## 12. Circular Move Attempts

**Wrong:** Trying to move a story under its own descendant

**Right:** `move_story()` validates this automatically:
```
Cannot move story to its own descendant 'X.Y.Z'
```

Always verify the target parent is NOT a descendant of the story being moved.
