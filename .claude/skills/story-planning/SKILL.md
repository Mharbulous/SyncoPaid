---
name: story-planning
description: Use when user says "plan story", "plan next feature", "create implementation plan", "what's ready to plan", or asks to plan an approved story - looks up approved story-nodes from story-tree database, prioritizes which to plan first, creates detailed implementation plan, and saves to ai_docs/Plans folder.
---

# Story Planning - Implementation Plan Generator

## Purpose

Generate **detailed implementation plans** for approved story-nodes by:
- Looking up all story-nodes with `status = 'approved'` from the story-tree database
- Analyzing and prioritizing which story should be planned first
- Creating a comprehensive implementation plan
- Saving the plan to `ai_docs/Plans/`
- Updating the story status from `approved` to `planned`

## When to Use

- "Plan a story"
- "Plan next feature"
- "Create implementation plan"
- "What's ready to plan?"
- "Plan [story-id]"
- When you have approved stories waiting to be planned
- Before starting implementation of a feature

## When NOT to Use

- Generating new story ideas (use `brainstorm-story` skill)
- Viewing the tree structure (use `story-tree` skill)
- General prioritization without plan creation (use `prioritize-story-notes` skill)
- Story already has `planned` status

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

### Step 1: Fetch All Approved Story-Nodes

Query all story-nodes with `status = 'approved'`:

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
         WHERE descendant_id = s.id AND depth > 0) as ancestors,
        (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) as child_count
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

For each approved story-node, check if it depends on other unimplemented stories.

**Dependency indicators:**
1. **Explicit mentions**: Description references another story ID
2. **Hierarchical**: Parent stories should be planned before deep children
3. **Technical**: Features requiring infrastructure not yet built
4. **Keywords**: "requires", "depends on", "after", "needs", "once X is done"

**Check for blockers:**
- References to other story IDs (e.g., "1.8.1", "1.2")
- References to features matching other story titles
- Technical prerequisites in acceptance criteria

### Step 3: Score and Prioritize

Score each non-blocked approved story by planning readiness:

| Factor | Weight | Scoring |
|--------|--------|---------|
| Node depth | 25% | Deeper = more specific = higher score (ready to implement) |
| Has description | 25% | More detail = easier to plan = higher score |
| Acceptance criteria | 20% | Fewer criteria = simpler = higher score |
| No dependencies | 30% | Independent = no blockers = higher score |

**Priority formula:**
```
score = min(depth, 5) * 0.25
      + (1 if has_description else 0) * 0.25
      + (10 - min(criteria_count, 10)) / 10 * 0.20
      + (1 if no_dependencies else 0) * 0.30
```

**Tie-breaker:** If scores are equal, prefer:
1. Shallower depth (affects more of the tree)
2. Shorter title (more focused scope)
3. Alphabetical by ID

### Step 4: Select Story to Plan

If user specified a story ID:
- Verify it exists and has `status = 'approved'`
- Use that story directly

If no story specified:
- Select the highest-scoring story from Step 3
- Report why this story was selected

### Step 5: Research Codebase for Plan

Before writing the plan, gather context:

1. **Read the story description and notes** from database
2. **Find related code files** using the project_path if set, or search:
   ```
   - Search for keywords from story title in codebase
   - Identify files that would need modification
   - Note existing patterns to follow
   ```
3. **Check existing implementations** of sibling stories for patterns
4. **Review technical-reference.md** for relevant architecture info

### Step 6: Create Implementation Plan

**Plan filename format:** `ai_docs/Plans/YYYY-MM-DD-[story-id]-[slug].md`

Where `[slug]` is the story title converted to lowercase-kebab-case (max 40 chars).

**Plan template:**

```markdown
# [Story Title] - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** [One sentence from story description]

**Architecture:** [2-3 sentences about implementation approach]

**Tech Stack:** [Key modules/libraries involved]

---

**Story ID:** [ID]
**Created:** [YYYY-MM-DD]
**Status:** planned

---

## Story

**Title:** [title]

**Description:**
[Full description from database]

**Notes:**
[Any notes from database]

## Overview

[2-3 sentences summarizing what will be implemented and the high-level approach]

## Prerequisites

- [ ] [Any required setup, dependencies, or prior knowledge]
- [ ] [Tools, libraries, or access needed]
- [ ] [Related stories that should be complete first]

## Files to Modify

| File | Purpose |
|------|---------|
| `path/to/file.py` | [What changes needed] |

## Implementation Tasks

### Task N: [Component Name]

**Files:**
- Create: `exact/path/to/file.py`
- Modify: `exact/path/to/existing.py:123-145`
- Test: `tests/exact/path/to/test.py`

**Step 1: Write the failing test**

```python
def test_specific_behavior():
    """Test that [behavior] works correctly."""
    result = function(input)
    assert result == expected
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/path/test.py::test_specific_behavior -v`
Expected: FAIL with "function not defined" or similar

**Step 3: Write minimal implementation**

```python
def function(input):
    """[Docstring]."""
    return expected
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/path/test.py::test_specific_behavior -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/path/test.py src/path/file.py
git commit -m "feat: add specific feature"
```

[Repeat Task N+1, N+2... for all implementation tasks]

## Testing Plan

- [ ] All unit tests pass: `python -m pytest -v`
- [ ] Module test passes: `python -m syncopaid.<module>`
- [ ] Manual verification of feature behavior
- [ ] No regressions in existing functionality

## Acceptance Criteria Checklist

- [ ] [Criterion 1 from story]
- [ ] [Criterion 2 from story]

## Rollback Plan

[What to do if implementation causes issues]

## Notes

[Any additional context, alternatives considered, edge cases, or caveats]
```

### Step 7: Save Plan and Update Status

1. **Write plan file** to `ai_docs/Plans/`:

```python
# Example: writing the plan file
plan_filename = f"ai_docs/Plans/2024-01-15-1.8.2-browser-url-extraction.md"
```

2. **Update story status** to `planned`:

```python
python -c "
import sqlite3

conn = sqlite3.connect('.claude/data/story-tree.db')
cursor = conn.cursor()

cursor.execute('''
    UPDATE story_nodes
    SET status = 'planned',
        notes = COALESCE(notes || chr(10), '') || 'Plan: ai_docs/Plans/[FILENAME]',
        updated_at = datetime('now')
    WHERE id = '[STORY_ID]'
''')

conn.commit()
conn.close()
print('Status updated to planned')
"
```

### Step 8: Output Report

```markdown
# Story Planning Report

**Generated:** [ISO timestamp]

## Approved Stories Analyzed

| ID | Title | Depth | Score | Selected |
|----|-------|-------|-------|----------|
| [id] | [title] | [depth] | [score] | ✓/- |

## Selected Story

**ID:** [id]
**Title:** [title]
**Priority Score:** [score]

### Why This Story?

- [Reason 1: e.g., "Deepest node - most specific and implementation-ready"]
- [Reason 2: e.g., "No dependencies on unimplemented features"]
- [Reason 3: e.g., "Clear description with actionable acceptance criteria"]

## Plan Created

**File:** `ai_docs/Plans/[filename]`

**Summary:**
[2-3 sentence summary of the plan]

## Execution Handoff

Plan complete and saved to `ai_docs/Plans/[filename]`.

**Two execution options:**

**1. Subagent-Driven (this session)**
- I dispatch fresh subagent per task
- Code review between tasks
- Fast iteration with quality gates
- **REQUIRED SUB-SKILL:** superpowers:subagent-driven-development

**2. Parallel Session (separate)**
- Open new Claude Code session in this directory
- Batch execution with checkpoints
- **REQUIRED SUB-SKILL:** superpowers:executing-plans

**Which approach?**
```

## Remember

When generating plans, always:
- **Exact file paths** - never "somewhere in src/"
- **Complete code** - not "add validation" but the actual validation code
- **Exact commands with expected output** - not just "run tests"
- **DRY, YAGNI, TDD** - test first, minimal code, frequent commits
- **One action per step** - each step takes 2-5 minutes max
- **Reference relevant skills** - use @ syntax for skill references

## Autonomous Operation

**Announce at start:** "I'm using the story-planning skill to create the implementation plan."

When user says "plan story" or "create implementation plan":
1. Announce you're using this skill
2. Run complete workflow (Steps 1-8) without asking permission
3. Only ask for clarification if:
   - Multiple stories have identical priority scores (offer top 3 choices)
   - No approved stories exist
   - Specified story ID doesn't exist or isn't approved

## Quality Checks

Before completing the workflow, verify:
- [ ] All approved stories were fetched and analyzed
- [ ] Priority scoring was applied correctly
- [ ] Selected story is truly the best candidate (or user-specified)
- [ ] Plan file contains all template sections
- [ ] Plan includes specific file paths and code examples
- [ ] Story status was updated to `planned`
- [ ] Notes field was updated with plan file path
- [ ] Each task has exactly 5 steps: test, verify fail, implement, verify pass, commit
- [ ] All code examples are complete and copy-paste ready
- [ ] All commands include expected output
- [ ] No vague instructions like "add validation" or "handle errors"
- [ ] Execution handoff options are presented at end

## Common Mistakes

| Mistake | What To Do Instead |
|---------|-------------------|
| Using `sqlite3` CLI | Use Python's sqlite3 module |
| Creating vague plans without code examples | Research codebase first, include specific file paths and pseudocode |
| Not updating story status | MUST update to `planned` after creating plan file |
| Planning already-planned stories | Check status is `approved` before proceeding |
| Skipping dependency analysis | Always check for blockers before selecting story |
| Writing multi-step tasks | Break into single-action steps (test/verify/implement/verify/commit) |
| Omitting expected output | Every command needs "Expected: [what success looks like]" |
| Vague code examples | Write complete, copy-paste ready code |
| Skipping execution handoff | Always offer subagent-driven vs parallel session choice |
| Large commits at end | Commit after each task (RED-GREEN-REFACTOR cycle) |

## References

- **Story Tree Database:** `.claude/data/story-tree.db`
- **Plans Folder:** `ai_docs/Plans/`
- **Story Tree Skill:** `.claude/skills/story-tree/SKILL.md`
- **Brainstorm Skill:** `.claude/skills/brainstorm-story/SKILL.md`
- **Technical Reference:** `ai_docs/technical-reference.md`
- **Status Values:** See story-tree skill for 21-status rainbow system
