---
name: story-planning-ci
description: CI-optimized story planning - creates TDD implementation plans for approved stories with minimal token usage. Use in automated workflows only.
---

# Story Planning - CI Mode

Token-optimized variant for automated workflows. See `story-planning` skill for full details.

**Database:** `.claude/data/story-tree.db`
**Plans:** `ai_docs/Plans/`

## Key Differences from Main Skill

- Compact plan template (no verbose explanations)
- Minimal output format
- No execution handoff options
- Use Python sqlite3 module (NOT CLI)

## Code Landmarks

For targeted reads with offset/limit:
- `src/syncopaid/tracker.py:88-130` - ActivityEvent dataclass
- `src/syncopaid/tracker.py:204-260` - TrackerLoop init
- `src/syncopaid/database.py:1-50` - Schema and imports
- `src/syncopaid/config.py:15-45` - DEFAULT_CONFIG dict

## Compact TDD Template

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

## Verification

- [ ] All tests pass: `python -m pytest -v`
- [ ] Module test: `python -m syncopaid.[module]`

## Notes

[Edge cases, follow-up work]
```

## CI Output

**Success:**
```
✓ Planned story [STORY_ID]: [Title]
  Score: [score]/1.0
  Plan: ai_docs/Plans/[filename].md
  Tasks: [N] TDD cycles
  Status: approved → planned
```

**No stories:**
```
✓ No approved stories available for planning
```
