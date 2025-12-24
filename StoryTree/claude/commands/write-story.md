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
# Three-field system: exclude concept stage, held, and disposed stories
cursor.execute('''
    SELECT s.id, s.title, s.stage,
        (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) as child_count,
        (SELECT MIN(depth) FROM story_paths WHERE descendant_id = s.id) as node_depth,
        COALESCE(s.capacity, 3 + (SELECT COUNT(*) FROM story_paths sp
             JOIN story_nodes child ON sp.descendant_id = child.id
             WHERE sp.ancestor_id = s.id AND sp.depth = 1
             AND child.stage IN ('implemented', 'ready', 'released'))) as effective_capacity
    FROM story_nodes s
    WHERE s.stage != 'concept'
      AND s.hold_reason IS NULL
      AND s.disposition IS NULL
      AND (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) <
          COALESCE(s.capacity, 3 + (SELECT COUNT(*) FROM story_paths sp
               JOIN story_nodes child ON sp.descendant_id = child.id
               WHERE sp.ancestor_id = s.id AND sp.depth = 1
               AND child.stage IN ('implemented', 'ready', 'released')))
    ORDER BY node_depth ASC
    LIMIT 1
''')
result['capacity_nodes'] = [dict(row) for row in cursor.fetchall()]

# Stories with 'polish' hold_reason (limit 2)
cursor.execute('''
    SELECT s.id, s.title, s.description, s.notes,
        (SELECT MIN(depth) FROM story_paths WHERE descendant_id = s.id) as node_depth
    FROM story_nodes s
    WHERE s.hold_reason = 'polish'
    ORDER BY s.updated_at ASC
    LIMIT 2
''')
result['polish_nodes'] = [dict(row) for row in cursor.fetchall()]

print(json.dumps(result, indent=2))
conn.close()
"
```

### New Story Generation

If `capacity_nodes` found, invoke `story-writing` skill for 1 story.

### Polish Stories

For each `polish_nodes` story:

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
    SET description = ?, stage = 'concept', hold_reason = NULL, updated_at = datetime('now')
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

## Three-Field Workflow

```
Stage:       concept → approved → planned → active → implemented → ready → released
                 ↑                    ↑         ↑
Hold:         refine | wishlist ─────────────────┘
                                  (clears hold, returns to stage)

Disposition: rejected | infeasible | deprecated | archived | legacy
             (terminal states - story is done/removed)
```
