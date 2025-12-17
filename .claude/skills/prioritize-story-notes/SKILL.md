---
name: prioritize-story-notes
description: Use when user says "prioritize stories", "what should I work on next", "find next story", "review approved stories", "plan next feature" - reviews all approved story notes, analyzes dependencies, identifies blocked stories, prioritizes low-hanging fruit, creates implementation plan for the best candidate, and updates status to planned.
---

# Prioritize Story Notes

Analyze approved stories to select the best candidate for implementation.

**Database:** `.claude/data/story-tree.db`
**Plans:** `.claude/data/plans/`

**Critical:** Use Python sqlite3 module, NOT sqlite3 CLI.

## Workflow

### Step 1: Fetch Approved Stories

```python
python -c "
import sqlite3, json
conn = sqlite3.connect('.claude/data/story-tree.db')
conn.row_factory = sqlite3.Row
stories = [dict(row) for row in conn.execute('''
    SELECT s.id, s.title, s.description, s.notes, s.project_path,
        (SELECT MIN(depth) FROM story_paths WHERE descendant_id = s.id) as node_depth,
        (SELECT GROUP_CONCAT(ancestor_id) FROM story_paths
         WHERE descendant_id = s.id AND depth > 0) as ancestors
    FROM story_nodes s WHERE s.status = 'approved'
    ORDER BY node_depth ASC
''').fetchall()]
print(json.dumps(stories, indent=2))
conn.close()
"
```

### Step 2: Analyze Dependencies

**Dependency indicators:**
- Explicit mentions: Story IDs in description (e.g., "1.8.1", "after 1.2")
- Keywords: "requires", "depends on", "after", "needs", "once X is done"
- Technical prerequisites mentioned in acceptance criteria

Mark blocked stories:
```python
python -c "
import sqlite3
conn = sqlite3.connect('.claude/data/story-tree.db')
conn.execute('''
    UPDATE story_nodes
    SET status = 'blocked',
        notes = COALESCE(notes || '\n', '') || 'Blocked by: [BLOCKER_ID] - [REASON]',
        updated_at = datetime('now')
    WHERE id = '[STORY_ID]'
''')
conn.commit()
conn.close()
"
```

### Step 3: Score Non-Blocked Stories

| Factor | Weight | Scoring |
|--------|--------|---------|
| Acceptance criteria count | 30% | Fewer = higher score |
| Description length | 20% | Shorter = higher score |
| Node depth | 20% | Deeper = higher score |
| Technical complexity | 30% | Fewer complex keywords = higher |

**Complexity keywords** (lower score): "integration", "API", "database schema", "migration", "refactor", "architecture", "security", "authentication", "performance", "real-time", "async"

**Simplicity keywords** (higher score): "add", "display", "show", "simple", "button", "field", "config", "setting", "update"

```
score = (10 - min(criteria_count, 10)) * 0.3
      + (1000 - min(desc_length, 1000)) / 100 * 0.2
      + min(depth, 5) * 0.2
      + (10 - complexity_count + simplicity_count) * 0.3
```

### Step 4: Create Implementation Plan

**Filename:** `.claude/data/plans/YYYY-MM-DD-[story-id]-[slug].md`

Include: Story Context, Overview, Prerequisites, Implementation Tasks (with file paths and code examples), Testing Plan, Rollback Plan, Notes.

### Step 5: Update Status

```python
python -c "
import sqlite3
conn = sqlite3.connect('.claude/data/story-tree.db')
conn.execute('''
    UPDATE story_nodes
    SET status = 'planned',
        notes = COALESCE(notes || '\n', '') || 'Plan created: .claude/data/plans/[FILENAME]',
        updated_at = datetime('now')
    WHERE id = '[STORY_ID]'
''')
conn.commit()
conn.close()
"
```

### Step 6: Output Report

Include: analyzed stories table, blocked stories with reasons, selected story with score breakdown and rationale, plan file location, next steps.

## Key Rules

- Plan file MUST exist before status change to `planned`
- Analyze ALL approved stories for dependencies first
- Only ask for clarification if: multiple identical scores, ambiguous dependencies, or no approved stories exist
