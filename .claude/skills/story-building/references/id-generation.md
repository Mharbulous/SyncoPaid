# ID Generation - Story Identifier Format and Assignment

Consistent ID format ensures tree integrity and navigation.

---

## ID Format Rules

| Level | Format | Examples |
|-------|--------|----------|
| **Root children** (primary epics) | Plain integer `[N]` | `1`, `2`, `16`, `17` |
| **All other levels** | `[parent-id].[N]` | `1.1`, `1.2`, `8.4.2` |

**Critical:**
- Root children are **never** formatted as `root.1` or `0.1`
- Always use plain integers for direct children of root
- Nested IDs always include full parent path

---

## Finding Next Available ID

### For Root Children (Primary Epics)

```python
python -c "
import sqlite3
conn = sqlite3.connect('.claude/data/story-tree.db')
# Find all integer IDs that are direct children of root
existing = conn.execute('''
    SELECT CAST(sn.id AS INTEGER) FROM story_nodes sn
    JOIN story_paths sp ON sn.id = sp.descendant_id
    WHERE sp.ancestor_id = 'root' AND sp.depth = 1
    AND sn.id GLOB '[0-9]*' AND sn.id NOT LIKE '%.%'
''').fetchall()
existing_ints = sorted([r[0] for r in existing])
# Find next available (may fill gaps or extend)
next_id = 1
for e in existing_ints:
    if e == next_id: next_id = e + 1
print(next_id)
conn.close()
"
```

**Logic:**
- Finds all existing integer IDs at depth 1 from root
- Fills gaps first (if 1, 2, 4 exist → returns 3)
- Extends if no gaps (if 1, 2, 3 exist → returns 4)

### For Non-Root Parents

```python
python -c "
import sqlite3
conn = sqlite3.connect('.claude/data/story-tree.db')
parent_id = 'PARENT_ID'  # Replace with actual parent ID
cursor = conn.execute('''
    SELECT sn.id FROM story_nodes sn
    JOIN story_paths sp ON sn.id = sp.descendant_id
    WHERE sp.ancestor_id = ? AND sp.depth = 1
''', (parent_id,))
existing = [r[0] for r in cursor.fetchall()]
# Extract child numbers (after last dot)
child_nums = []
for eid in existing:
    if '.' in eid:
        parts = eid.rsplit('.', 1)
        if parts[0] == parent_id and parts[1].isdigit():
            child_nums.append(int(parts[1]))
next_child = max(child_nums, default=0) + 1
print(f'{parent_id}.{next_child}')
conn.close()
"
```

**Logic:**
- Finds all children of the specified parent
- Extracts the numeric suffix after the last dot
- Returns `parent_id.N` where N is max + 1

---

## ID Assignment Workflow

### Step 1: Determine Parent

Either from user request or capacity finder:
```bash
python .claude/scripts/story_workflow.py --ci
```

### Step 2: Check Parent Type

```python
python -c "
import sqlite3
conn = sqlite3.connect('.claude/data/story-tree.db')
parent_id = 'PARENT_ID'
if parent_id == 'root':
    print('ROOT_CHILD')
else:
    print('NESTED_CHILD')
conn.close()
"
```

### Step 3: Generate ID

Use appropriate script based on parent type (see above).

### Step 4: Verify Uniqueness

Before insertion, confirm ID doesn't exist:
```python
python -c "
import sqlite3
conn = sqlite3.connect('.claude/data/story-tree.db')
new_id = 'NEW_ID'
exists = conn.execute('SELECT 1 FROM story_nodes WHERE id = ?', (new_id,)).fetchone()
print('EXISTS' if exists else 'AVAILABLE')
conn.close()
"
```

---

## Common Mistakes

| Mistake | Correct Approach |
|---------|------------------|
| Using `root.1` for root children | Use plain `1` |
| Hardcoding next ID without checking | Always query existing IDs |
| Not handling gaps in ID sequence | Use gap-filling logic |
| Using string comparison for ID ordering | Cast to integer for root children |

---

## Multi-Node Batching

When generating stories for multiple nodes:

```python
# Process each node, but generate IDs sequentially
for parent_id in ['1.2', '1.3']:
    next_id = get_next_child_id(parent_id)  # Use appropriate query
    # Generate story with next_id
    # Insert story
    # next_id is now taken, subsequent queries will skip it
```

**Important:** Generate and insert one story at a time to avoid ID collisions.
