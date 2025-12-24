# Interactive Workflow - Human-Initiated Story Building

For conversational sessions where a user requests story creation.

---

## Critical Rule

> **A story is NOT complete until vetted.**
>
> This applies whether the story is AI-generated OR user-provided.
> Never commit after insertion alone. Always complete the full workflow.

---

## Entry Points

This workflow has two entry points depending on user input:

| User Says | Entry Point |
|-----------|-------------|
| "Build a story for X" | **Path A**: AI generates story |
| "Add this story: As a..." | **Path B**: User provides story |

Both paths converge at vetting. Neither is complete without it.

---

## Path A: AI-Generated Story

When the user asks for a story to be generated.

### A1: Find Target Node

If user specifies a parent node, use that. Otherwise, find capacity:

```bash
python .claude/scripts/story_workflow.py --ci
```

**If NO_CAPACITY:** Inform user "All nodes at capacity" and stop.

### A2: Gather Context

#### Goals
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

#### Recent Commits
```python
python -c "
import subprocess
result = subprocess.run(['git', 'log', '--since=30 days ago',
    '--pretty=format:%h|%ai|%s', '--no-merges'], capture_output=True, text=True)
print(result.stdout)
"
```

#### Existing Children of Target
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

### A3: Generate Story

Create story following template:
```markdown
**As a** [specific user role]
**I want** [specific capability]
**So that** [specific benefit]

**Acceptance Criteria:**
- [ ] [Specific, testable criterion]
- [ ] [Specific, testable criterion]
- [ ] [Specific, testable criterion]

**Related context:** [Evidence from commits or gaps]
```

### A4: Proceed to Shared Steps

Continue to **Insert → Vet → Classify → Complete** below.

---

## Path B: User-Provided Story

When the user provides a complete story to add.

> **Warning:** User-provided stories still require vetting.
> The fact that a human wrote it does not exempt it from duplicate detection.

### B1: Identify Parent Node

Analyze the story content to find the appropriate parent:

```python
python -c "
import sqlite3
conn = sqlite3.connect('.claude/data/story-tree.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()
cursor.execute('''
    SELECT s.id, s.title, s.stage,
        (SELECT MIN(depth) FROM story_paths WHERE descendant_id = s.id) as node_depth
    FROM story_nodes s
    WHERE s.disposition IS NULL
    ORDER BY s.id
''')
for row in cursor.fetchall():
    print(f\"{'  ' * (row['node_depth'] or 0)}{row['id']}: {row['title']} [{row['stage']}]\")
conn.close()
"
```

Select the most appropriate parent based on story scope.

### B2: Determine Next ID

```python
python -c "
import sqlite3
conn = sqlite3.connect('.claude/data/story-tree.db')
cursor = conn.cursor()
# Get existing children of parent to determine next ID
cursor.execute('''
    SELECT s.id FROM story_nodes s
    JOIN story_paths p ON s.id = p.descendant_id
    WHERE p.ancestor_id = ? AND p.depth = 1
    ORDER BY s.id
''', ('PARENT_ID',))
children = [row[0] for row in cursor.fetchall()]
print(f'Existing children: {children}')
conn.close()
"
```

### B3: Proceed to Shared Steps

Continue to **Insert → Vet → Classify → Complete** below.

---

## Shared Steps (Both Paths)

These steps are required regardless of how the story was created.

### Step 1: Insert Story

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
print('Story inserted - proceeding to vetting')
"
```

> **Do not commit yet.** The story is inserted but not validated.

### Step 2: Vet Story

```bash
python .claude/skills/story-vetting/candidate_detector.py --story-id NEW_ID
```

### Step 3: Classify Conflicts

If candidates are found, classify each:

| Conflict Type | Other Status | Action |
|---------------|--------------|--------|
| `duplicate` | concept | TRUE_MERGE |
| `duplicate` | non-concept | DELETE new, retry (Path A) or inform user (Path B) |
| `scope_overlap` | concept | TRUE_MERGE |
| `scope_overlap` | non-concept | DEFER_PENDING |
| `competing` | concept | TRUE_MERGE |
| `competing` | non-concept | DELETE new, retry (Path A) or inform user (Path B) |
| `incompatible` | concept | Ask user which to keep |
| `false_positive` | — | Record in vetting_decisions and SKIP |

#### Recording Decisions

```python
python -c "
import sqlite3
conn = sqlite3.connect('.claude/data/story-tree.db')
cursor = conn.cursor()
cursor.execute('SELECT id, COALESCE(LENGTH(description), 0) as version FROM story_nodes WHERE id IN (?, ?)', ('STORY_A', 'STORY_B'))
versions = {row[0]: row[1] for row in cursor.fetchall()}
pair_key = 'STORY_A|STORY_B'
cursor.execute('''
    INSERT OR REPLACE INTO vetting_decisions
    (pair_key, story_a_id, story_a_version, story_b_id, story_b_version, classification, action_taken, decided_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
''', (pair_key, 'STORY_A', versions.get('STORY_A', 0), 'STORY_B', versions.get('STORY_B', 0), 'CLASSIFICATION', 'ACTION'))
conn.commit()
conn.close()
"
```

### Step 4: Complete

Only after vetting passes (no conflicts, or all conflicts resolved):

1. Commit the database changes
2. Push to remote
3. Report success to user

---

## Retry Logic (Path A Only)

If a generated story conflicts with a non-concept story:

1. Delete the new story
2. Add conflicting story to `avoided_topics`
3. Generate a new story avoiding those topics
4. Maximum 10 attempts

```python
# Delete conflicting story
python -c "
import sqlite3
conn = sqlite3.connect('.claude/data/story-tree.db')
conn.execute('DELETE FROM story_paths WHERE descendant_id = ?', ('CONFLICTING_ID',))
conn.execute('DELETE FROM story_nodes WHERE id = ?', ('CONFLICTING_ID',))
conn.commit()
conn.close()
"
```

---

## Workflow Checklist

Use this to verify completion:

- [ ] Story inserted into database
- [ ] Candidate detector run on new story
- [ ] All candidates classified
- [ ] Vetting decisions recorded
- [ ] Changes committed
- [ ] Changes pushed

Only check all boxes when truly complete.

---

## Common Mistakes

| Mistake | Why It Happens | Prevention |
|---------|----------------|------------|
| Commit after insert | Treating insertion as completion | Follow checklist above |
| Skip vetting for user stories | Assuming human input is validated | Both paths require vetting |
| Not recording false positives | Seems unnecessary | Future runs will re-flag same pairs |
