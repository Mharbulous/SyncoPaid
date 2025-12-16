# Common Mistakes

## 1. Ignoring Priority Algorithm

**Wrong:** "Node 1.3.2.1 is empty (0/3), so highest priority."

**Right:** Depth takes precedence over fill rate. Shallowest node wins.

## 2. Not Matching Commits First

Always run git analysis before generation. Update status from in-progress → implemented if match found.

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
