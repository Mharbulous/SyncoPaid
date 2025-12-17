---
name: story-planning
description: Use when user says "plan story", "plan next feature", "create implementation plan", "what's ready to plan", or asks to plan an approved story - looks up approved story-nodes from story-tree database, prioritizes which to plan first, creates detailed TDD-focused implementation plan, and saves to .claude/data/plans folder.
---

# Story Planning - TDD Implementation Plan Generator

Generate test-driven implementation plans for approved stories.

**Database:** `.claude/data/story-tree.db`
**Plans:** `.claude/data/plans/`

**Critical:** Use Python sqlite3 module, NOT sqlite3 CLI.

## Mode Detection

**CI Mode** activates when:
- Environment variable `CI=true` is set, OR
- Trigger phrase includes "(ci)" like "plan story (ci)"

**CI Mode behavior:**
- No confirmation prompts - use reasonable defaults
- Compact plan template (shorter explanations)
- Skip execution handoff options
- Structured summary output

**Interactive Mode** (default):
- Pause for confirmation at key decisions
- Verbose plan template with full explanations
- Present execution handoff options

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

**Tie-breaker:** Shallower depth -> shorter title -> alphabetical ID

### Step 3: Select Story

- If user specified ID: validate exists and `status = 'approved'`
- Otherwise: select highest-scoring non-blocked story
- **Interactive only:** Confirm selection with user before proceeding

### Step 4: Research Codebase

1. Read full story description and notes
2. Locate files via `project_path` or keyword search
3. Review sibling implementations for patterns
4. Reference `ai_docs/technical-reference.md`

**Code Landmarks** (for targeted reads):
- `src/syncopaid/tracker.py:88-130` - ActivityEvent dataclass
- `src/syncopaid/tracker.py:204-260` - TrackerLoop init
- `src/syncopaid/database.py:1-50` - Schema and imports
- `src/syncopaid/config.py:15-45` - DEFAULT_CONFIG dict

### Step 5: Create TDD Plan

**Filename:** `.claude/data/plans/YYYY-MM-DD-[story-id]-[slug].md`
- `[slug]` = title in lowercase-kebab-case (max 40 chars)

#### Interactive Mode Template

```markdown
# [Story Title] - Implementation Plan

**Goal:** [One-sentence summary of what this achieves]
**Approach:** [2-3 sentences on technical approach]
**Tech Stack:** [Key modules/libraries involved]

---

**Story ID:** [ID]
**Created:** [YYYY-MM-DD]
**Status:** `planned`

---

## Story Context

**Title:** [title]
**Description:** [description]

**Acceptance Criteria:**
- [ ] [Criterion 1]
- [ ] [Criterion 2]

**Notes:** [Any notes from story]

## Prerequisites

- [ ] Virtual environment activated: `venv\Scripts\activate`
- [ ] Dependencies installed
- [ ] Related stories completed: [list or "None"]
- [ ] Baseline tests pass: `python -m pytest -v`

## Files Affected

| File | Change Type | Purpose |
|------|-------------|---------|
| `tests/test_x.py` | Create | Unit tests for feature |
| `src/syncopaid/x.py` | Modify | Core implementation |

## TDD Tasks

### Task 1: [Descriptive Name]

**RED:** Write failing test
```python
# tests/test_x.py
def test_behavior():
    result = module.func(input)
    assert result == expected
```
**Run:** `pytest tests/test_x.py::test_behavior -v`
**Expect:** FAILED

**GREEN:** Write minimal implementation
```python
# src/syncopaid/x.py
def func(input):
    return result
```
**Run:** `pytest tests/test_x.py::test_behavior -v`
**Expect:** PASSED

**COMMIT:** `git add tests/test_x.py src/syncopaid/x.py && git commit -m "feat: add behavior"`

---

[Repeat for additional tasks...]

## Verification Checklist

- [ ] All new tests pass
- [ ] All existing tests pass: `python -m pytest -v`
- [ ] Module runs without error: `python -m syncopaid.[module]`
- [ ] Manual verification: [specific checks]

## Rollback Plan

If issues arise:
1. `git revert HEAD~N` (where N = number of commits)
2. [Any cleanup steps]

## Implementation Notes

[Edge cases, gotchas, future considerations]
```

#### CI Mode Template (Compact)

```markdown
# [Story Title] - Implementation Plan

> **TDD Required:** Each task: Write test -> RED -> Write code -> GREEN -> Commit

**Goal:** [One sentence]
**Approach:** [2-3 sentences]
**Tech Stack:** [Modules/libraries]

---

**Story ID:** [ID] | **Created:** [YYYY-MM-DD] | **Status:** `planned`

---

## Story Context

**Title:** [title]
**Description:** [description]

**Acceptance Criteria:**
- [ ] [Criterion 1]
- [ ] [Criterion 2]

## Prerequisites

- [ ] venv activated: `venv\Scripts\activate`
- [ ] Baseline tests pass: `python -m pytest -v`

## Files Affected

| File | Change | Purpose |
|------|--------|---------|
| `tests/test_x.py` | Create | Test behavior |
| `src/syncopaid/x.py:45-60` | Modify | Implementation |

## TDD Tasks

### Task 1: [Name]

**Files:** Test: `tests/path/test_x.py` | Impl: `src/path/x.py:123-145`

**RED:** Create test for [behavior].
```python
def test_behavior():
    result = module.func(input)
    assert result == expected
```
Run: `pytest tests/path/test_x.py::test_behavior -v` -> Expect: FAILED

**GREEN:** Implement [minimal solution].
```python
def func(input):
    return result
```
Run: `pytest tests/path/test_x.py::test_behavior -v` -> Expect: PASSED

**COMMIT:** `git add tests/path/test_x.py src/path/x.py && git commit -m "feat: [message]"`

---

## Verification

- [ ] All tests pass: `python -m pytest -v`
- [ ] Module test: `python -m syncopaid.[module]`

## Notes

[Edge cases, follow-up work]
```

**Quality requirements (both modes):**
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
        notes = COALESCE(notes || chr(10), '') || 'Plan: .claude/data/plans/[FILENAME]',
        updated_at = datetime('now')
    WHERE id = '[STORY_ID]'
''')
conn.commit()
conn.close()
"
```

### Step 7: Execution Handoff (Interactive Only)

**Skip this step in CI mode.**

Present two options:

**Option 1: Continue in this session** - Implement with tight feedback loops, interactive course correction

**Option 2: Fresh session** - Open new Claude Code session, say "Execute plan: .claude/data/plans/[filename]"

## Output Format

**CI Mode - Success:**
```
✓ Planned story [STORY_ID]: [Title]
  Score: [score]/1.0
  Plan: .claude/data/plans/[filename].md
  Tasks: [N] TDD cycles
  Status: approved -> planned
```

**CI Mode - No stories:**
```
✓ No approved stories available for planning
```

**Interactive Mode:** Conversational summary with handoff options.
