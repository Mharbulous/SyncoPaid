---
name: story-planning-ci
description: CI-optimized story planning - creates TDD implementation plans for approved stories with minimal token usage. Use in automated workflows only.
---

# Story Planning - CI Mode

## Purpose

Generate TDD implementation plans for approved stories (CI-optimized):
1. Query approved story-nodes from database
2. Prioritize by readiness score
3. Create compact TDD plan
4. Save to `ai_docs/Plans/`
5. Update status: `approved` → `planned`

## Storage

**Database:** `.claude/data/story-tree.db`
**Plans:** `ai_docs/Plans/`

## Workflow Steps

### Step 1: Query Approved Stories

```python
python -c "
import sqlite3, json

conn = sqlite3.connect('.claude/data/story-tree.db')
conn.row_factory = sqlite3.Row

stories = [dict(row) for row in conn.execute('''
    SELECT
        s.id, s.title, s.description, s.notes, s.project_path,
        (SELECT MIN(depth) FROM story_paths WHERE descendant_id = s.id) as node_depth,
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

Identify blockers:
- **Explicit**: Story IDs in description (e.g., "after 1.2")
- **Keyword**: "requires", "depends on", "needs"

Mark blocked stories and exclude from selection.

### Step 3: Score and Prioritize

```python
score = min(depth, 5) * 0.30 \
      + (1 if description else 0) * 0.25 \
      + (10 - min(len(criteria), 10)) / 10 * 0.20 \
      + (1 if not blocked else 0) * 0.25
```

**Tie-breaker:** Shallower depth → shorter title → alphabetical ID

### Step 4: Select Story

- **If ID specified:** Use that story (validate exists + approved)
- **If no ID:** Select highest-scoring story

### Step 5: Research Codebase

1. Read story description and notes
2. Use `project_path` or search by keywords
3. Reference `ai_docs/technical-reference.md` for architecture

**Code Landmarks** (use offset/limit for targeted reads):
- `src/syncopaid/tracker.py:88-130` - ActivityEvent dataclass
- `src/syncopaid/tracker.py:204-260` - TrackerLoop init
- `src/syncopaid/database.py:1-50` - Schema and imports
- `src/syncopaid/config.py:15-45` - DEFAULT_CONFIG dict

### Step 6: Create Compact Plan

**Filename:** `ai_docs/Plans/YYYY-MM-DD-[story-id]-[slug].md`

**Compact TDD Template:**

```markdown
# [Story Title] - Implementation Plan

> **TDD Required:** Each task: Write test → RED → Write code → GREEN → Commit

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
Run: `pytest tests/path/test_x.py::test_behavior -v` → Expect: FAILED

**GREEN:** Implement [minimal solution].
```python
def func(input):
    return result
```
Run: `pytest tests/path/test_x.py::test_behavior -v` → Expect: PASSED

**COMMIT:** `git add tests/path/test_x.py src/path/x.py && git commit -m "feat: [message]"`

---

[Repeat for additional tasks - keep examples minimal]

## Verification

- [ ] All tests pass: `python -m pytest -v`
- [ ] Module test: `python -m syncopaid.[module]`
- [ ] Acceptance criteria verified

## Notes

[Edge cases, alternatives, follow-up work]
```

### Step 7: Save Plan and Update Status

1. Write plan file to `ai_docs/Plans/`

2. Update story status:

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
print('Status updated to planned')
"
```

### Step 8: CI Output

**Successful planning:**
```
✓ Planned story [STORY_ID]: [Title]
  Score: [score]/1.0
  Plan: ai_docs/Plans/[filename].md
  Tasks: [N] TDD cycles
  Status: approved → planned
```

**No stories to plan:**
```
✓ No approved stories available for planning
```

## Requirements

- Use Python sqlite3 module (NOT sqlite3 CLI)
- All file paths must be exact
- Code examples must be minimal but complete
- Each task = 3 checkpoints (RED/GREEN/COMMIT)

## References

- **Database:** `.claude/data/story-tree.db`
- **Plans:** `ai_docs/Plans/`
- **Technical Reference:** `ai_docs/technical-reference.md`
