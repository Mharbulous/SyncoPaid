Generate new user story concepts or refine existing stories needing rework.

## Arguments

$Arguments

- **With arguments**: Pass directly to `story-writing` skill
- **Without arguments**: Auto-discover capacity nodes + refine stories

## Default Behavior (No Arguments)

### Discover Nodes Needing Attention

**Limits (token efficiency):** 1 capacity node, 2 refine stories

```python
python -c "
import sqlite3
import json

conn = sqlite3.connect('.claude/data/story-tree.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

result = {'capacity_nodes': [], 'refine_nodes': []}

# Under-capacity nodes, shallower first (limit 1)
cursor.execute('''
    SELECT s.id, s.title, s.status,
        (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) as child_count,
        (SELECT MIN(depth) FROM story_paths WHERE descendant_id = s.id) as node_depth,
        COALESCE(s.capacity, 3 + (SELECT COUNT(*) FROM story_paths sp
             JOIN story_nodes child ON sp.descendant_id = child.id
             WHERE sp.ancestor_id = s.id AND sp.depth = 1
             AND child.status IN ('implemented', 'ready'))) as effective_capacity
    FROM story_nodes s
    WHERE s.status NOT IN ('concept', 'rejected', 'deprecated', 'infeasible', 'bugged')
      AND (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) <
          COALESCE(s.capacity, 3 + (SELECT COUNT(*) FROM story_paths sp
               JOIN story_nodes child ON sp.descendant_id = child.id
               WHERE sp.ancestor_id = s.id AND sp.depth = 1
               AND child.status IN ('implemented', 'ready')))
    ORDER BY node_depth ASC
    LIMIT 1
''')
result['capacity_nodes'] = [dict(row) for row in cursor.fetchall()]

# Stories with 'refine' status (limit 2)
cursor.execute('''
    SELECT s.id, s.title, s.description, s.notes,
        (SELECT MIN(depth) FROM story_paths WHERE descendant_id = s.id) as node_depth
    FROM story_nodes s
    WHERE s.status = 'refine'
    ORDER BY s.updated_at ASC
    LIMIT 2
''')
result['refine_nodes'] = [dict(row) for row in cursor.fetchall()]

print(json.dumps(result, indent=2))
conn.close()
"
```

### New Story Generation

If `capacity_nodes` found, invoke `story-writing` skill for 1 story.

### Refine Stories

For each `refine_nodes` story:

1. **Archive to notes** with timestamp:
```python
python -c "
import sqlite3
from datetime import datetime

conn = sqlite3.connect('.claude/data/story-tree.db')
cursor = conn.cursor()

cursor.execute('SELECT description, notes FROM story_nodes WHERE id = ?', ('STORY_ID',))
row = cursor.fetchone()
current_description = row[0]
current_notes = row[1] or ''

timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
archive_entry = f'''

---
**Previous Version ({timestamp}):**
{current_description}
---
'''

cursor.execute('UPDATE story_nodes SET notes = ? WHERE id = ?', (current_notes + archive_entry, 'STORY_ID'))
conn.commit()
conn.close()
"
```

2. **Generate refined story** addressing feedback in notes

3. **Update with refined version**:
```python
python -c "
import sqlite3

conn = sqlite3.connect('.claude/data/story-tree.db')
cursor = conn.cursor()
cursor.execute('''
    UPDATE story_nodes
    SET description = ?, status = 'concept', updated_at = datetime('now')
    WHERE id = ?
''', ('''REFINED_STORY''', 'STORY_ID'))
conn.commit()
conn.close()
"
```

## Story Format

```markdown
**As a** [role]
**I want** [capability]
**So that** [benefit]

**Acceptance Criteria:**
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

**Refinement Notes:** [What changed from previous version]
```

## With Arguments

Maximum 10 stories. Examples:
- `/write-story for node 1.2`
- `/write-story 3 stories for export module`
- `/write-story refine 1.3.2`

## Status Flow

```
concept → approved → planned → active → implemented → released
    ↓         ↓
 refine  →  (refines back to concept)
    ↓
 rejected
```
