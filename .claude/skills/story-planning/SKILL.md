---
name: story-planning
description: Use when user says "plan story", "plan next feature", "create implementation plan", "what's ready to plan", or asks to plan an approved story - looks up approved story-nodes from story-tree database, prioritizes which to plan first, creates detailed TDD-focused implementation plan, and saves to ai_docs/Plans folder.
---

# Story Planning - TDD Implementation Plan Generator

Generate test-driven implementation plans for approved stories.

**Database:** `.claude/data/story-tree.db`
**Plans:** `ai_docs/Plans/`

**Critical:** Use Python sqlite3 module, NOT sqlite3 CLI.

## Workflow

### Step 1: Query Approved Stories

```python
python -c "
import sqlite3, json
conn = sqlite3.connect('.claude/data/story-tree.db')
conn.row_factory = sqlite3.Row
stories = [dict(row) for row in conn.execute('''
    SELECT s.id, s.title, s.description, s.notes, s.project_path,
        (SELECT MIN(depth) FROM story_paths WHERE descendant_id = s.id) as node_depth,
        (SELECT GROUP_CONCAT(ancestor_id) FROM story_paths
         WHERE descendant_id = s.id AND depth > 0) as ancestors,
        (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) as child_count
    FROM story_nodes s WHERE s.status = 'approved'
    ORDER BY node_depth ASC
''').fetchall()]
print(json.dumps(stories, indent=2))
conn.close()
"
```

### Step 2: Check Dependencies & Score

**Blocker keywords:** "requires", "depends on", "after", "needs", "once X is done"

**Scoring formula:**
```python
score = min(depth, 5) * 0.30 \
      + (1 if description else 0) * 0.25 \
      + (10 - min(len(criteria), 10)) / 10 * 0.20 \
      + (1 if not blocked else 0) * 0.25
```

**Tie-breaker:** Shallower depth → shorter title → alphabetical ID

### Step 3: Select Story

- If user specified ID: validate exists and `status = 'approved'`
- Otherwise: select highest-scoring non-blocked story

### Step 4: Research Codebase

1. Read full story description and notes
2. Locate files via `project_path` or keyword search
3. Review sibling implementations for patterns
4. Reference `ai_docs/technical-reference.md`

### Step 5: Create TDD Plan

**Filename:** `ai_docs/Plans/YYYY-MM-DD-[story-id]-[slug].md`
- `[slug]` = title in lowercase-kebab-case (max 40 chars)

**Plan structure:**
1. Header: Goal, Approach, Tech Stack, Story ID, Created date, Status
2. Story Context: Title, Description, Acceptance Criteria, Notes
3. Prerequisites: venv, dependencies, related stories, baseline tests
4. Files Affected: table with File, Change Type, Purpose
5. TDD Tasks: Each task has 3 checkpoints:
   - **RED:** Write failing test with exact code, run command, expect FAILED
   - **GREEN:** Write minimal implementation, run command, expect PASSED
   - **COMMIT:** git add + commit with descriptive message
6. Verification Checklist
7. Rollback Plan
8. Implementation Notes

**Quality requirements:**
- Exact file paths (never "somewhere in src/")
- Complete, copy-paste ready code examples
- Full commands with expected output
- Zero ambiguity - implementer makes no decisions

### Step 6: Update Status

```python
python -c "
import sqlite3
conn = sqlite3.connect('.claude/data/story-tree.db')
conn.execute('''
    UPDATE story_nodes
    SET status = 'planned',
        notes = COALESCE(notes || chr(10), '') || 'Plan: ai_docs/Plans/[FILENAME]',
        updated_at = datetime('now')
    WHERE id = '[STORY_ID]'
''')
conn.commit()
conn.close()
"
```

### Step 7: Execution Handoff

Present two options:

**Option 1: Continue in this session** - Implement with tight feedback loops, interactive course correction

**Option 2: Fresh session** - Open new Claude Code session, say "Execute plan: ai_docs/Plans/[filename]"

### CI Mode Output

When running in CI/automation (no interactive session):
```
✓ Planned story [STORY_ID]: [Title]
  Score: [score]/1.0
  Plan: ai_docs/Plans/[filename].md
  Tasks: [N] TDD cycles
  Status: approved → planned
```

Or: `✓ No approved stories available for planning`
