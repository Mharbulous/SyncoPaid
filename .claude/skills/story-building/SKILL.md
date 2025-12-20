---
name: story-building
description: Use when user says "build stories", "generate stories", "create stories", or asks for new story ideas - combines story generation with duplicate detection in a single workflow. Generates stories, vets for conflicts, and retries up to 10 times if duplicates are detected. Does NOT commit - leaves that to the caller.
disable-model-invocation: true
---

# Story Building - Generate and Vet in One Pass

Generate user stories with built-in duplicate detection. Retries automatically when conflicts found.

**Database:** `.claude/data/story-tree.db`

**Critical:** Use Python sqlite3 module, NOT sqlite3 CLI.

**Key Difference from story-writing:** This skill validates each story against existing stories before accepting it. If a duplicate is detected, it tries again with a different idea (up to 10 attempts).

---

## Workflow Overview

```
┌─────────────────────────────────────┐
│ Step 0: Polish existing stories     │
└─────────────────┬───────────────────┘
                  ▼
┌─────────────────────────────────────┐
│ Step 1: Find target node            │
└─────────────────┬───────────────────┘
                  ▼
┌─────────────────────────────────────┐
│ Step 2: Gather context              │
│ (goals, commits, gaps)              │
└─────────────────┬───────────────────┘
                  ▼
         ┌───────────────┐
         │ attempt = 0   │
         │ avoided = []  │
         └───────┬───────┘
                 ▼
    ┌────────────────────────┐
    │ attempt < 10?          │──No──▶ ABORT: "Failed to think
    └────────┬───────────────┘         of any new story ideas"
             │ Yes
             ▼
    ┌────────────────────────┐
    │ Step 3: Generate story │
    │ (avoiding: avoided[])  │
    └────────┬───────────────┘
             ▼
    ┌────────────────────────┐
    │ Step 4: Insert story   │
    └────────┬───────────────┘
             ▼
    ┌────────────────────────┐
    │ Step 5: Vet new story  │
    └────────┬───────────────┘
             ▼
    ┌────────────────────────┐
    │ Conflict found?        │
    └────────┬───────────────┘
             │
      ┌──────┴──────┐
      │             │
      ▼             ▼
   No conflicts   Duplicate/Competing
      │           with non-concept
      ▼                │
   SUCCESS             ▼
                  Delete new story
                  Add to avoided[]
                  attempt++
                  Loop back ↑
```

---

## Step 0: Polish Existing Stories

Check for stories needing refinement before generating new ones:

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
3. Clear hold: `SET hold_reason = NULL, human_review = 0`

**Proceed to generation only after all polish stories are processed.**

---

## Step 1: Find Target Node with Capacity

Use the story_workflow.py script:

```bash
python .claude/scripts/story_workflow.py --ci
```

**If NO_CAPACITY:** Exit successfully with "All nodes at capacity"

**Otherwise:** Parse JSON output to get target node context.

---

## Step 2: Gather Context

### 2a: Check Goals Files

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

### 2b: Analyze Git Commits

```python
python -c "
import subprocess
result = subprocess.run(['git', 'log', '--since=30 days ago',
    '--pretty=format:%h|%ai|%s', '--no-merges'], capture_output=True, text=True)
print(result.stdout)
"
```

### 2c: Query Existing Children

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

---

## Step 3-5: Generate-Vet Loop (Max 10 Attempts)

Initialize tracking:
- `attempt = 0`
- `avoided_topics = []` (stories that were duplicates - don't regenerate similar ideas)

### For each attempt:

#### Step 3: Generate Story

Create a story that:
- Fits the parent node's scope
- Avoids topics in `avoided_topics`
- Follows user story format (As a / I want / So that)
- Has 3-5 testable acceptance criteria
- References commits or gaps as evidence

**Template:**
```markdown
### [ID]: [Title]

**As a** [specific user role]
**I want** [specific capability]
**So that** [specific benefit]

**Acceptance Criteria:**
- [ ] [Specific, testable criterion]
- [ ] [Specific, testable criterion]
- [ ] [Specific, testable criterion]

**Related context**: [Git commits or gaps]
```

#### Step 4: Insert Story

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

#### Step 5: Vet the New Story

Run candidate detection focused on the new story:

```bash
python .claude/skills/story-vetting/candidate_detector.py --story-id NEW_ID
```

**If no candidates:** SUCCESS - story is unique, exit loop.

**If candidates found:** Classify each conflict:

| Conflict Type | Other Story Status | Action |
|---------------|-------------------|--------|
| `duplicate` | concept | TRUE_MERGE (success) |
| `duplicate` | non-concept | DELETE new, add to avoided, retry |
| `scope_overlap` | concept | TRUE_MERGE (success) |
| `scope_overlap` | non-concept | DEFER_PENDING (success, needs human review later) |
| `competing` | concept | TRUE_MERGE (success) |
| `competing` | non-concept | DELETE new, add to avoided, retry |
| `incompatible` | concept | PICK_BETTER, delete loser (success) |
| `false_positive` | — | SKIP (success) |

**On retry:** Add the conflicting story's title/description to `avoided_topics` so the next generation doesn't repeat the same idea.

---

## Exit Conditions

### Success Cases
- Story generated with no conflicts
- Story merged with existing concept (TRUE_MERGE)
- Scope overlap deferred for human review (DEFER_PENDING)
- False positive (no action needed)

### Failure Case
- 10 attempts all produced duplicates/competing stories

**Failure Output:**
```
STORY BUILDING FAILED
=====================
Attempted to generate 10 unique stories but all were duplicates of existing work.

Avoided topics:
1. [Title of duplicate 1]
2. [Title of duplicate 2]
...

This may indicate:
- The target node is already well-covered
- Consider decomposing existing stories instead of adding new ones
- Try a different parent node

Failed to think of any new story ideas.
```

---

## Success Output

```
STORY BUILDING COMPLETE
=======================

Target node: [PARENT_ID] - [Parent Title]
Attempts: [N] of 10

Result: [SUCCESS_TYPE]
- Story ID: [NEW_ID]
- Title: [Title]
- Status: concept

[If merged:]
- Merged with: [OTHER_ID]
- Merged title: [New Title]

Ready for commit (handled by caller).
```

---

## CI Mode

In CI mode (GitHub Actions):
- No interactive prompts
- HUMAN_REVIEW → DEFER_PENDING automatically
- Max 10 attempts enforced
- Clear success/failure exit codes

---

## References

- **Story Writing:** `.claude/skills/story-writing/SKILL.md`
- **Story Vetting:** `.claude/skills/story-vetting/SKILL.md`
- **Candidate Detector:** `.claude/skills/story-vetting/candidate_detector.py`
- **Vetting Actions:** `.claude/skills/story-vetting/vetting_actions.py`
- **Goals:** `.claude/data/goals/goals.md`, `.claude/data/goals/non-goals.md`
- **Database:** `.claude/data/story-tree.db`
