---
name: story-planning
description: Use when user says "plan story", "plan next feature", "create implementation plan", "what's ready to plan", or asks to plan an approved story - looks up approved story-nodes from story-tree database, prioritizes which to plan first, creates detailed TDD-focused implementation plan, and saves to ai_docs/Plans folder.
---

# Story Planning - TDD Implementation Plan Generator

## Purpose

Generate **test-driven implementation plans** for approved stories:
1. Query approved story-nodes from story-tree database
2. Prioritize stories based on readiness and dependencies
3. Create comprehensive TDD-focused implementation plan
4. Save plan to `ai_docs/Plans/` with execution handoff
5. Update story status: `approved` → `planned`

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

### Step 1: Query Approved Stories

Fetch all approved story-nodes with metadata:

```python
python -c "
import sqlite3, json

conn = sqlite3.connect('.claude/data/story-tree.db')
conn.row_factory = sqlite3.Row

stories = [dict(row) for row in conn.execute('''
    SELECT
        s.id, s.title, s.description, s.notes, s.project_path,
        (SELECT MIN(depth) FROM story_paths WHERE descendant_id = s.id) as node_depth,
        (SELECT GROUP_CONCAT(ancestor_id) FROM story_paths
         WHERE descendant_id = s.id AND depth > 0) as ancestors,
        (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) as child_count
    FROM story_nodes s
    WHERE s.status = 'approved'
    ORDER BY node_depth ASC
''').fetchall()]

print(json.dumps(stories, indent=2))
conn.close()
"
```

### Step 2: Check Dependencies

Identify blocking dependencies for each story:

**Blocker types:**
- **Explicit**: Story IDs mentioned in description (e.g., "1.8.1", "after 1.2")
- **Keyword**: "requires", "depends on", "after", "needs", "once X is done"
- **Technical**: Infrastructure/features not yet implemented
- **Hierarchical**: Deep children may need parent context

**Action:** Mark stories as blocked if they reference unimplemented dependencies.

### Step 3: Score and Prioritize

Calculate readiness score for each non-blocked story:

| Factor | Weight | Logic |
|--------|--------|-------|
| Depth | 30% | Deeper = more specific = easier to plan |
| Has description | 25% | More detail = clearer scope |
| Simplicity | 20% | Fewer acceptance criteria = faster delivery |
| Independence | 25% | No dependencies = ready now |

**Formula:**
```python
score = min(depth, 5) * 0.30 \
      + (1 if description else 0) * 0.25 \
      + (10 - min(len(criteria), 10)) / 10 * 0.20 \
      + (1 if not blocked else 0) * 0.25
```

**Tie-breaker:** Prefer shallower depth → shorter title → alphabetical ID

### Step 4: Select Story

**If user specified story ID:**
- Validate: exists and `status = 'approved'`
- Use that story (skip scoring)

**If no ID specified:**
- Select highest-scoring story from Step 3
- Document selection rationale

### Step 5: Research Codebase

Gather implementation context:

1. **Read story**: Full description, notes, acceptance criteria
2. **Locate files**: Use `project_path` or search by story title keywords
3. **Study patterns**: Review sibling story implementations
4. **Check architecture**: Reference `ai_docs/technical-reference.md`

**Goal:** Understand enough to write specific file paths and code examples.

### Step 6: Create Implementation Plan

**Plan filename format:** `ai_docs/Plans/YYYY-MM-DD-[story-id]-[slug].md`

Where `[slug]` is the story title converted to lowercase-kebab-case (max 40 chars).

**Plan template with strict TDD structure:**

```markdown
# [Story Title] - Implementation Plan

> **For Claude:** This plan follows strict TDD (Test-Driven Development). Each task MUST complete all 5 steps in order: Write test → Verify RED → Write code → Verify GREEN → Commit.

**Goal:** [One sentence from story description]

**Approach:** [2-3 sentences: architectural decisions, patterns used, key trade-offs]

**Tech Stack:** [Modules/libraries: `syncopaid.module`, `pytest`, etc.]

---

**Story ID:** [ID]
**Created:** [YYYY-MM-DD]
**Status:** `planned`

---

## Story Context

**Title:** [title]

**Description:**
[Full description from database]

**Acceptance Criteria:**
- [ ] [Criterion 1]
- [ ] [Criterion 2]

**Notes:**
[Any notes from database]

## Prerequisites

- [ ] Python 3.11+ with venv activated: `venv\Scripts\activate`
- [ ] Dependencies installed: [list any new packages needed]
- [ ] Related stories complete: [story IDs if any]
- [ ] Baseline tests passing: `python -m pytest -v`

## Files Affected

| File | Change Type | Purpose |
|------|-------------|---------|
| `tests/test_module.py` | Create | Test new feature behavior |
| `src/syncopaid/module.py:45-60` | Modify | Add new feature implementation |

## TDD Implementation Tasks

### Task 1: [Specific Feature Component]

**Objective:** [One sentence describing what this task accomplishes]

**Files:**
- Test: `tests/exact/path/test_module.py`
- Implementation: `src/exact/path/module.py:123-145`

---

**⚠️ TDD CHECKPOINT 1: RED - Write Failing Test**

Create test that specifies the expected behavior:

```python
# tests/exact/path/test_module.py
def test_feature_behavior():
    """Test that [specific behavior] works correctly when [condition]."""
    # Arrange
    input_data = expected_input

    # Act
    result = module.new_function(input_data)

    # Assert
    assert result == expected_output
    assert result.property == expected_value
```

**Verify RED:**
```bash
python -m pytest tests/exact/path/test_module.py::test_feature_behavior -v
```
**Expected output:** `FAILED` - ImportError, AttributeError, or NameError (function doesn't exist)

---

**⚠️ TDD CHECKPOINT 2: GREEN - Minimal Implementation**

Write simplest code that makes the test pass:

```python
# src/exact/path/module.py:123-145
def new_function(input_data):
    """[Docstring explaining purpose and parameters]."""
    # Minimal implementation
    result = process(input_data)
    return result
```

**Verify GREEN:**
```bash
python -m pytest tests/exact/path/test_module.py::test_feature_behavior -v
```
**Expected output:** `PASSED` - Test succeeds

---

**⚠️ TDD CHECKPOINT 3: COMMIT**

Commit working test + implementation:

```bash
git add tests/exact/path/test_module.py src/exact/path/module.py
git commit -m "feat: add [specific feature]

- Add test for [behavior]
- Implement minimal [component]
- [Acceptance criteria] verified"
```

**Expected output:** Commit created with hash

---

[Repeat for Task 2, Task 3, etc.]

## Verification Checklist

**Before marking story complete:**

- [ ] All tests pass: `python -m pytest -v`
- [ ] Module test works: `python -m syncopaid.[module]`
- [ ] Each acceptance criterion verified
- [ ] No regressions in existing features
- [ ] All tasks committed (one commit per task minimum)

## Rollback Plan

**If issues occur:**
1. Identify last known good commit: `git log --oneline`
2. Revert problematic commit: `git revert [hash]`
3. Document issue in story notes
4. Re-plan if fundamental approach flawed

## Implementation Notes

[Any edge cases, alternatives considered, technical debt, or follow-up work]
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

### Step 8: Output Report and Execution Handoff

Present planning results and offer implementation options:

```markdown
# Story Planning Complete

**Timestamp:** [ISO 8601 timestamp]

## Selection Summary

**Analyzed:** [N] approved stories
**Selected:** [story-id] - [title]
**Priority Score:** [score]/1.0

### Why This Story?

- ✓ [Primary reason: depth/simplicity/no blockers]
- ✓ [Secondary reason]
- ✓ [Tertiary reason]

## Plan Location

**File:** `ai_docs/Plans/[YYYY-MM-DD-story-id-slug].md`

**Summary:** [One sentence describing what will be implemented]

**Tasks:** [N] TDD tasks with [M] total checkpoints (RED/GREEN/COMMIT cycles)

---

## 🚀 Ready to Implement?

**Choose execution mode:**

### Option 1: Continue in This Session (Recommended)

**Process:**
1. I implement each task following strict TDD (RED → GREEN → COMMIT)
2. You review progress after each commit
3. We iterate quickly with tight feedback loops

**Advantage:** Fast, interactive, immediate course correction
**Disadvantage:** Uses this session's context

**To proceed:** Say **"implement the plan"** or **"let's build it"**

---

### Option 2: Fresh Session (Advanced)

**Process:**
1. Open new Claude Code session in same directory
2. Say: "Execute plan: ai_docs/Plans/[filename]"
3. Fresh agent implements independently

**Advantage:** Preserves this session, parallel work possible
**Disadvantage:** Slower feedback, less interactive

**To proceed:** Open new session, reference plan file

---

**Which would you prefer?**
```

## Quality Standards

**Every plan MUST include:**

| Element | Requirement |
|---------|-------------|
| File paths | Exact paths, never "somewhere in src/" |
| Code examples | Complete, copy-paste ready (not "add validation") |
| Commands | Full command + expected output format |
| Tasks | Each task = 3 TDD checkpoints (RED/GREEN/COMMIT) |
| Duration | Each checkpoint takes 2-5 minutes max |
| Specificity | Zero ambiguity - implementer should not need to decide anything |

## Autonomous Operation

**Trigger phrases:** "plan story", "create implementation plan", "plan next feature", "what's ready to plan"

**Workflow:**
1. Announce: "Using story-planning skill"
2. Execute Steps 1-8 autonomously
3. Only pause for clarification if:
   - Multiple stories tied for highest score (show top 3)
   - No approved stories found
   - Specified story ID missing or not approved

## Pre-Completion Checklist

**Before presenting final report, verify:**

- [ ] All approved stories queried and scored
- [ ] Dependencies checked, blocked stories excluded
- [ ] Selection rationale documented
- [ ] Plan has all template sections (Story Context, Prerequisites, Files Affected, TDD Tasks, Verification, Rollback, Notes)
- [ ] Every task follows TDD structure: ⚠️ RED → ⚠️ GREEN → ⚠️ COMMIT
- [ ] All code examples complete and runnable
- [ ] All commands show expected output
- [ ] Zero vague instructions ("add validation" → actual validation code)
- [ ] Story status updated: `approved` → `planned`
- [ ] Story notes updated with plan file path
- [ ] Execution handoff options presented (continue session vs fresh session)

## Common Mistakes to Avoid

| ❌ Don't | ✅ Do |
|----------|-------|
| Use `sqlite3` CLI | Use Python's `sqlite3` module with `-c` flag |
| Vague plans ("add validation") | Complete code examples ready to copy-paste |
| Skip status update | Always update `approved` → `planned` after plan creation |
| Plan already-planned stories | Verify `status = 'approved'` before starting |
| Ignore dependencies | Check for blockers, exclude blocked stories from selection |
| Multi-step tasks | Single TDD checkpoint per step (RED or GREEN or COMMIT) |
| Commands without output | Include "Expected: PASSED" or "Expected: commit abc123" |
| Ambiguous instructions | Zero decisions for implementer - be explicit |
| Skip execution handoff | Always present Option 1 (this session) vs Option 2 (fresh session) |
| Big bang commits | Commit after each task completes GREEN checkpoint |

## References

- **Story Tree Database:** `.claude/data/story-tree.db`
- **Plans Folder:** `ai_docs/Plans/`
- **Story Tree Skill:** `.claude/skills/story-tree/SKILL.md`
- **Brainstorm Skill:** `.claude/skills/brainstorm-story/SKILL.md`
- **Technical Reference:** `ai_docs/technical-reference.md`
- **Status Values:** See story-tree skill for 21-status rainbow system
