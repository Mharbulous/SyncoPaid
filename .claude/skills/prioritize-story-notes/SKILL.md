---
name: prioritize-story-notes
description: Use when user says "prioritize stories", "what should I work on next", "find next story", "review approved stories", "plan next feature" - reviews all approved story notes, analyzes dependencies, identifies blocked stories, prioritizes low-hanging fruit, creates implementation plan for the best candidate, and updates status to planned.
---

# Prioritize Story Notes - Next Story Selector & Planner

## Purpose

Analyze all **approved** story notes to determine which one to work on next by:
- Identifying dependencies between stories
- Marking blocked stories as `blocked`
- Prioritizing low-hanging fruit (simpler tasks first)
- Creating an implementation plan for the best candidate
- Updating that story's status from `approved` to `planned`

## When to Use

- "What should I work on next?"
- "Prioritize stories"
- "Find next story"
- "Review approved stories"
- "Plan next feature"
- When you have multiple approved stories and need to choose one

## When NOT to Use

- Generating new story ideas (use `story-tree`)
- Viewing the tree structure (use `story-tree` with "show story tree")
- Manually setting status (use SQL directly)

## Storage

**Database:** `.claude/data/story-tree.db`
**Plans folder:** `ai_docs/Plans/`

## Environment Requirements

**CRITICAL:** Always use Python's sqlite3 module, NOT the sqlite3 CLI:

```python
python -c "
import sqlite3
conn = sqlite3.connect('.claude/data/story-tree.db')
cursor = conn.cursor()
cursor.execute('YOUR SQL HERE')
print(cursor.fetchall())
conn.close()
"
```

## Workflow Steps

### Step 1: Fetch All Approved Stories

Query all stories with `status = 'approved'`:

```python
python -c "
import sqlite3
import json

conn = sqlite3.connect('.claude/data/story-tree.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute('''
    SELECT
        s.id,
        s.title,
        s.description,
        s.notes,
        s.project_path,
        (SELECT MIN(depth) FROM story_paths WHERE descendant_id = s.id) as node_depth,
        (SELECT GROUP_CONCAT(ancestor_id) FROM story_paths
         WHERE descendant_id = s.id AND depth > 0) as ancestors
    FROM story_nodes s
    WHERE s.status = 'approved'
    ORDER BY node_depth ASC
''')

stories = [dict(row) for row in cursor.fetchall()]
print(json.dumps(stories, indent=2))
conn.close()
"
```

### Step 2: Analyze Dependencies

For each approved story, determine if it depends on other stories that aren't yet implemented.

**Dependency indicators to look for:**
1. **Explicit mentions**: Story description mentions another story ID or feature
2. **Hierarchical dependencies**: Parent stories should be implemented before deep children
3. **Technical dependencies**: Features that require infrastructure not yet built
4. **Keywords**: "requires", "depends on", "after", "needs", "once X is done"

**Analyze each story's description and notes for:**
- References to other story IDs (e.g., "1.8.1", "1.2")
- References to features by name that match other story titles
- Technical prerequisites mentioned in acceptance criteria

### Step 3: Identify Blocked Stories

A story is **blocked** if:
1. It explicitly depends on another approved/concept story
2. Its parent node is not yet implemented (and is a prerequisite)
3. It requires a feature described in another unimplemented story

For each blocked story, update status and note the blocker:

```python
python -c "
import sqlite3

conn = sqlite3.connect('.claude/data/story-tree.db')
cursor = conn.cursor()

# Update status to blocked with reason in notes
cursor.execute('''
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

### Step 4: Prioritize Low-Hanging Fruit

From remaining non-blocked approved stories, score each by:

| Factor | Weight | Scoring |
|--------|--------|---------|
| Acceptance criteria count | 30% | Fewer = simpler = higher score |
| Description length | 20% | Shorter = clearer scope = higher score |
| Node depth | 20% | Deeper = more specific = higher score |
| Technical complexity keywords | 30% | Fewer complex keywords = higher score |

**Complexity keywords** (lower score if present):
- "integration", "API", "database schema", "migration"
- "refactor", "architecture", "multi-step", "complex"
- "security", "authentication", "encryption"
- "performance", "optimization", "caching"
- "real-time", "async", "concurrent"

**Simplicity keywords** (higher score if present):
- "add", "display", "show", "simple"
- "button", "field", "label", "text"
- "config", "setting", "option"
- "update", "modify", "change"

**Priority formula:**
```
score = (10 - min(criteria_count, 10)) * 0.3
      + (1000 - min(desc_length, 1000)) / 100 * 0.2
      + min(depth, 5) * 0.2
      + (10 - complexity_keyword_count + simplicity_keyword_count) * 0.3
```

Select the story with the highest score.

### Step 5: Create Implementation Plan

For the selected story, create a detailed implementation plan:

**Plan filename format:** `ai_docs/Plans/YYYY-MM-DD-[story-id]-[slug].md`

**Plan template:**

```markdown
# [Story Title] - Implementation Plan

**Story ID:** [ID]
**Created:** [ISO Date]
**Status:** planned

## Story

[Full story description from database]

## Overview

[2-3 sentence summary of what will be implemented and the approach]

## Prerequisites

- [List any required setup, dependencies, or prior knowledge]
- [Tools, libraries, or access needed]

## Implementation Tasks

### Task 1: [First task title]

**Files:** `path/to/file.py`

[Description of what to do]

```python
# Example code or pseudocode
```

**Verification:** [How to verify this task is complete]

### Task 2: [Second task title]

[Continue for all tasks...]

## Testing Plan

- [ ] [Manual test step 1]
- [ ] [Manual test step 2]
- [ ] [Run: `python -m syncopaid.<module>`]

## Rollback Plan

[What to do if something goes wrong]

## Notes

[Any additional context, alternatives considered, or caveats]
```

### Step 6: Update Story Status to Planned

```python
python -c "
import sqlite3

conn = sqlite3.connect('.claude/data/story-tree.db')
cursor = conn.cursor()

cursor.execute('''
    UPDATE story_nodes
    SET status = 'planned',
        notes = COALESCE(notes || '\n', '') || 'Plan created: ai_docs/Plans/[FILENAME]',
        updated_at = datetime('now')
    WHERE id = '[STORY_ID]'
''')

conn.commit()
conn.close()
print('Status updated to planned')
"
```

### Step 7: Output Report

```markdown
# Story Prioritization Report

**Generated:** [ISO timestamp]

## Approved Stories Analyzed

| ID | Title | Depth | Status After Analysis |
|----|-------|-------|----------------------|
| [id] | [title] | [depth] | [approved/blocked/planned] |

## Blocked Stories

| ID | Title | Blocked By | Reason |
|----|-------|------------|--------|
| [id] | [title] | [blocker_id] | [reason] |

## Selected Story

**ID:** [id]
**Title:** [title]
**Priority Score:** [score]

### Why This Story?
- [Reason 1: e.g., "No dependencies on other stories"]
- [Reason 2: e.g., "Simple scope with 3 acceptance criteria"]
- [Reason 3: e.g., "Builds on existing implemented infrastructure"]

### Selection Factors
- Acceptance criteria: [N] (simple/moderate/complex)
- Description length: [N] chars
- Depth: [N]
- Complexity score: [N]

## Plan Created

**File:** `ai_docs/Plans/[filename]`

## Next Steps

1. Review the implementation plan
2. When ready, say "implement [story-id]" or manually begin work
3. Update status to `active` when starting implementation
```

## Autonomous Operation

When user says "prioritize stories" or "what should I work on next":
1. Run complete workflow (Steps 1-7) without asking permission
2. Only ask for clarification if:
   - Multiple stories have identical priority scores
   - A dependency relationship is ambiguous
   - No approved stories exist

## Common Mistakes

| Mistake | What To Do Instead |
|---------|-------------------|
| Using `sqlite3` CLI | Use Python's sqlite3 module |
| Creating plan without reading story | Always fetch full story details first |
| Marking story planned without creating plan file | Plan file MUST exist before status change |
| Ignoring blocked dependencies | Always analyze ALL approved stories for dependencies first |

## References

- **Story Tree Database:** `.claude/data/story-tree.db`
- **Plans Folder:** `ai_docs/Plans/`
- **Story Tree Skill:** `.claude/skills/story-tree/SKILL.md`
- **Status Values:** See story-tree skill for 21-status rainbow system
