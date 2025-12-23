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
