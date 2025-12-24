---
name: story-writing
description: Use when user says "brainstorm stories", "generate story ideas", "brainstorm features", "create stories for [node]", or asks for new story ideas - FIRST polishes any existing stories with hold_reason='polish' before generating new stories. Then generates evidence-based user stories for nodes with capacity based on git commit analysis, existing children, and gap analysis. Works with story-tree database to create concept stories with proper user story format and acceptance criteria.
disable-model-invocation: true
---

# Story Writing - Evidence-Based Story Generator

Generate user stories grounded in git commits and gap analysis.

**Database:** `.claude/data/story-tree.db`

**Critical:** Use Python sqlite3 module, NOT sqlite3 CLI.

## Priority Order

1. **FIRST:** Polish any stories with `hold_reason='polish'`
2. **THEN:** Generate new stories for target node

## Multi-Node Batching

When given multiple node IDs (e.g., "Generate stories for nodes: 1.2, 1.3"):
- Perform goals check and git analysis ONCE (shared context)
- Loop through nodes for context/gap/generation
- Max 1 story per node when batching, total max 2 stories
- Single combined output

Token savings: ~2,800 tokens per additional node.

## Workflow

### Step 0: Check for Stories Needing Refinement

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

**If stories with `hold_reason='polish'` exist:** Process each one:
1. Identify issues (vague criteria, missing evidence, too broad, unclear role)
2. Rework with quality standards
3. Clear hold: `SET hold_reason = NULL, human_review = 0` (stage remains 'concept')

**Only proceed to new story generation AFTER all held-for-polish stories are processed.**

### Step 0a: Check Goals Files

```python
python -c "
import os, json
result = {}
for key, path in [('goals', '.claude/data/goals/goals.md'), ('non_goals', '.claude/data/goals/non-goals.md')]:
    result[f'has_{key}'] = os.path.exists(path)
    if result[f'has_{key}']:
        with open(path) as f: result[key] = f.read()
print(json.dumps(result, indent=2))
"
```

If goals files exist, internalize:
- What the product IS (target user, core capabilities, guiding principles)
- What the product is NOT (explicit exclusions, anti-patterns)

If goals files don't exist, generate stories based purely on git commits and gaps.

### Step 1: Gather Parent Node Context

Query parent node and existing children using closure table joins.

### Step 2: Analyze Git Commits

```python
python -c "
import subprocess
result = subprocess.run(['git', 'log', '--since=30 days ago',
    '--pretty=format:%h|%ai|%s', '--no-merges'], capture_output=True, text=True)
print(result.stdout)
"
```

Match commits to parent node scope using keyword similarity.

### Step 3: Identify Gaps

**Gap types:** Functional, Pattern (commits without stories), User journey, Technical

**Goals-aware filtering (if files exist):**
- Cross-check against goals.md core capabilities
- Cross-check against non-goals.md exclusions
- Reject speculative features not grounded in goals OR commits

**Max 3 stories per invocation.**

### Step 4: Generate Stories

**Story ID format:**
- **Root children (primary epics):** Plain integer `[N]` where N is the next available integer
- **All other levels:** `[parent-id].[N]` (next available child number)

**Finding next available ID for root children:**
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

**Finding next available child number for non-root parents:**
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

**Template:**
```markdown
### [ID]: [Title]

**As a** [specific user role from goals or codebase context]
**I want** [specific capability]
**So that** [specific benefit]

**Acceptance Criteria:**
- [ ] [Specific, testable criterion]
- [ ] [Specific, testable criterion]
- [ ] [Specific, testable criterion]

**Related context**: [Git commits or gaps that inform this story]
```

**Quality requirements:**
- Specific user role (not generic "user")
- Concrete, measurable capability
- Testable acceptance criteria
- Evidence from commits or clear functional gap
- Stories decompose parent scope (don't expand it)

### Step 5: Validate

**Check:**
- Each story has evidence (commits or gaps)
- User story format complete (As a/I want/So that)
- 3+ testable acceptance criteria
- No duplicates with existing children
- IDs follow hierarchy format
- Scope within parent description

**If goals files exist, also check:**
- Aligns with core capabilities
- No conflicts with non-goals exclusions
- Follows guiding principles

### Step 6: Insert Stories

Default `stage: 'concept'`. Use `approved` only if user explicitly requested.

```python
python -c "
import sqlite3
conn = sqlite3.connect('.claude/data/story-tree.db')

# Insert story
conn.execute('''
    INSERT INTO story_nodes (id, title, description, stage, created_at, updated_at)
    VALUES (?, ?, ?, 'concept', datetime('now'), datetime('now'))
''', ('NEW_ID', 'TITLE', 'DESCRIPTION'))

# Populate closure table
conn.execute('''
    INSERT INTO story_paths (ancestor_id, descendant_id, depth)
    SELECT ancestor_id, ?, depth + 1 FROM story_paths WHERE descendant_id = ?
    UNION ALL SELECT ?, ?, 0
''', ('NEW_ID', 'PARENT_ID', 'NEW_ID', 'NEW_ID'))

conn.commit()
conn.close()
"
```

### Step 7: Output Report

Include: Goals status, context analysis, commits analyzed, gaps identified (with goals alignment), gaps rejected (with reasons), generated stories, next steps.

**CI mode output:**
```
✓ Generated [N] stories for node [PARENT_ID]:
  - [STORY_ID_1]: [Title 1]
  - [STORY_ID_2]: [Title 2]
```

## Key Rules

- **Always check `hold_reason='polish'` first** before generating new stories
- **Always check goals files** before generating (if they exist)
- **ID format is critical:**
  - Root children (primary epics): plain integer IDs like `16`, `17`, `18` (NOT `root.1` or decimal formats)
  - All other levels: `[parent-id].[N]` format like `1.1`, `8.4.2`
- Max 3 stories per invocation (max 1 per node when batching)
- Every story must reference commits OR specific gap
- Stories decompose parent scope, don't expand it
- Use specific user role from goals file or codebase context (not generic "user")

## References

- **Goals:** `.claude/data/goals/goals.md`, `.claude/data/goals/non-goals.md` (if they exist)
- **Database:** `.claude/data/story-tree.db`
- **Story Tree:** `.claude/skills/story-tree/SKILL.md`
- **Goal Synthesis:** `.claude/skills/goal-synthesis/SKILL.md`
