# CI Workflow - Automated Story Building

For GitHub Actions and automated pipelines. No user interaction.

## Trigger

Called by `.github/workflows/build-stories.yml` or similar automation.

## Constraints

- No interactive prompts
- All decisions must be automated
- HUMAN_REVIEW conflicts → DEFER_PENDING automatically
- Max 10 generation attempts enforced
- Clear exit codes required

---

## Workflow Steps

### Step 0: Polish Existing Stories

```python
python -c "
import sqlite3, json
conn = sqlite3.connect('.claude/data/story-tree.db')
conn.row_factory = sqlite3.Row
stories = [dict(row) for row in conn.execute('''
    SELECT s.id, s.title, s.description, s.stage, s.hold_reason, s.notes,
           (SELECT ancestor_id FROM story_paths WHERE descendant_id = s.id AND depth = 1) as parent_id
    FROM story_nodes s WHERE s.hold_reason = 'polish' ORDER BY s.created_at
''').fetchall()]
print(json.dumps({'count': len(stories), 'stories': stories}, indent=2))
conn.close()
"
```

**If polish stories exist:** Process each one before generating new stories.

### Step 1: Find Target Node

```bash
python .claude/scripts/story_workflow.py --ci
```

**If NO_CAPACITY:** Exit successfully with "All nodes at capacity"

### Step 2: Gather Context

#### 2a: Read Goals
```python
python -c "
import os, json
result = {}
for key, path in [('goals', '.claude/data/goals/goals.md'), ('non_goals', '.claude/data/goals/non-goals.md')]:
    if os.path.exists(path):
        with open(path) as f: result[key] = f.read()
print(json.dumps(result, indent=2))
"
```

#### 2b: Recent Commits
```python
python -c "
import subprocess
result = subprocess.run(['git', 'log', '--since=30 days ago',
    '--pretty=format:%h|%ai|%s', '--no-merges'], capture_output=True, text=True)
print(result.stdout)
"
```

#### 2c: Existing Children
```python
python -c "
import sqlite3, json
conn = sqlite3.connect('.claude/data/story-tree.db')
conn.row_factory = sqlite3.Row
children = [dict(row) for row in conn.execute('''
    SELECT s.id, s.title, s.description, COALESCE(s.disposition, s.hold_reason, s.stage) as status
    FROM story_nodes s
    JOIN story_paths p ON s.id = p.descendant_id
    WHERE p.ancestor_id = ? AND p.depth = 1
''', ('TARGET_PARENT_ID',)).fetchall()]
print(json.dumps(children, indent=2))
conn.close()
"
```

### Steps 3-5: Generate-Vet Loop

Initialize: `attempt = 0`, `avoided_topics = []`

#### Loop (max 10 attempts):

**Step 3: Generate Story**
- Fit parent scope
- Avoid topics in `avoided_topics`
- User story format with 3-5 acceptance criteria

**Step 4: Insert Story**
```python
python -c "
import sqlite3
conn = sqlite3.connect('.claude/data/story-tree.db')
conn.execute('''
    INSERT INTO story_nodes (id, title, description, stage, created_at, updated_at)
    VALUES (?, ?, ?, 'concept', datetime('now'), datetime('now'))
''', ('NEW_ID', 'TITLE', 'DESCRIPTION'))
conn.execute('''
    INSERT INTO story_paths (ancestor_id, descendant_id, depth)
    SELECT ancestor_id, ?, depth + 1 FROM story_paths WHERE descendant_id = ?
    UNION ALL SELECT ?, ?, 0
''', ('NEW_ID', 'PARENT_ID', 'NEW_ID', 'NEW_ID'))
conn.commit()
conn.close()
"
```

**Step 5: Vet Story**
```bash
python .claude/skills/story-vetting/candidate_detector.py --story-id NEW_ID
```

#### CI Conflict Resolution

| Conflict Type | Other Status | CI Action |
|---------------|--------------|-----------|
| `duplicate` | concept | TRUE_MERGE |
| `duplicate` | non-concept | DELETE, retry |
| `scope_overlap` | concept | TRUE_MERGE |
| `scope_overlap` | non-concept | DEFER_PENDING |
| `competing` | concept | TRUE_MERGE |
| `competing` | non-concept | DELETE, retry |
| `incompatible` | concept | DEFER_PENDING (can't pick in CI) |
| `false_positive` | — | SKIP |

---

## Exit Codes

- **0**: Success (story created, merged, or deferred)
- **0**: No capacity (normal completion)
- **1**: Failed after 10 attempts
- **1**: Database or script error

## Output Format

```
STORY BUILDING COMPLETE (CI)
============================
Target node: [PARENT_ID] - [Parent Title]
Attempts: [N] of 10
Result: [SUCCESS_TYPE]
Story ID: [NEW_ID]
```
