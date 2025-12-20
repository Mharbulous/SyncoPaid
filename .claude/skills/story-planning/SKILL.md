---
name: story-planning
description: Use when user says "plan story", "plan next feature", "create implementation plan", "what's ready to plan", or asks to plan an approved story - looks up approved story-nodes from story-tree database, prioritizes which to plan first, creates detailed TDD-focused implementation plan, and saves to .claude/data/plans/ folder.
disable-model-invocation: true
---

# Story Planning - TDD Implementation Plan Generator

Generate test-driven implementation plans for approved stories.

**Announce:** On activation, say: "I'm using the story-planning skill to create the implementation plan."

**Database:** `.claude/data/story-tree.db`
**Plans:** `.claude/data/plans/`

**Critical:** Use Python sqlite3 module, NOT sqlite3 CLI.

## Design Principles

- **Task Granularity:** Each task = 2-5 minutes of focused work
- **Zero Context:** Assume implementer knows nothing about the codebase
- **Self-Contained:** Every task has exact file paths, complete code, exact commands
- **TDD Discipline:** RED (write failing test) → verify failure → GREEN (minimal impl) → verify pass → COMMIT
- **DRY/YAGNI:** No speculative abstractions, no premature optimization
- **Frequent Commits:** One commit per passing test cycle

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
    FROM story_nodes s
    WHERE s.stage = 'approved' AND s.hold_reason IS NULL AND s.disposition IS NULL
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

- If user specified ID: validate exists and `stage = 'approved'` with no hold_reason/disposition
- Otherwise: select highest-scoring non-blocked story
- **Interactive only:** Confirm selection with user before proceeding

### Step 4: Research Codebase

**Goal:** Gather enough context to write a zero-context plan.

1. **Read the story** - full description, notes, acceptance criteria
2. **Locate affected files** - use `project_path` field or search by keywords
3. **Study existing patterns** - how do sibling features implement similar behavior?
4. **Check technical docs** - `ai_docs/technical-reference.md` for conventions
5. **Understand test patterns** - review existing tests in `tests/` for style

**Code Landmarks** (for targeted reads):
- `src/syncopaid/tracker.py:88-130` - ActivityEvent dataclass
- `src/syncopaid/tracker.py:204-260` - TrackerLoop init
- `src/syncopaid/database.py:1-50` - Schema and imports
- `src/syncopaid/config.py:15-45` - DEFAULT_CONFIG dict

**Research Output:** Before writing the plan, you should know:
- Exact files to create/modify (with line numbers for modifications)
- The function signatures and data structures involved
- How to test this feature (unit test location, fixtures needed)
- Any edge cases mentioned in story notes

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
**Stage:** `planned`

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

### Task 1: [Descriptive Name] (~N min)

**Files:**
- **Create:** `tests/test_x.py`
- **Modify:** `src/syncopaid/x.py:45-60`

**Context:** [Why this task exists and what it enables for subsequent tasks]

**Step 1 - RED:** Write failing test
```python
# tests/test_x.py
def test_behavior():
    """[What this test verifies]"""
    result = module.func(input)
    assert result == expected
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_x.py::test_behavior -v
```
Expected: `FAILED` - test fails because [specific reason]

**Step 3 - GREEN:** Write minimal implementation
```python
# src/syncopaid/x.py (lines 45-60)
def func(input):
    """[Brief docstring]"""
    return result
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_x.py::test_behavior -v
```
Expected: `PASSED`

**Step 5 - COMMIT:**
```bash
git add tests/test_x.py src/syncopaid/x.py && git commit -m "feat: add behavior"
```

---

### Task 2: [Next Task] (~N min)

[Repeat structure...]

---

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

#### CI Mode Template (Compact, Self-Contained)

```markdown
# [Story Title] - Implementation Plan

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

**Goal:** [One sentence - what user-visible outcome does this achieve?]
**Approach:** [2-3 sentences on technical approach]
**Tech Stack:** [Modules/libraries involved]

---

**Story ID:** [ID] | **Created:** [YYYY-MM-DD] | **Stage:** `planned`

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

## TDD Tasks

### Task 1: [Descriptive Name] (~N min)

**Files:**
- **Create:** `tests/path/test_x.py`
- **Modify:** `src/path/x.py:123-145`

**Context:** [1-2 sentences: why this task exists, what it enables]

**Step 1 - RED:** Write failing test
```python
# tests/path/test_x.py
def test_behavior():
    """[What this test verifies]"""
    result = module.func(input)
    assert result == expected
```

**Step 2 - Verify RED:**
```bash
pytest tests/path/test_x.py::test_behavior -v
```
Expected output: `FAILED` (test should fail because [reason])

**Step 3 - GREEN:** Write minimal implementation
```python
# src/path/x.py (lines 123-145)
def func(input):
    """[Brief docstring]"""
    return result
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/path/test_x.py::test_behavior -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add tests/path/test_x.py src/path/x.py && git commit -m "feat: [message]"
```

---

### Task 2: [Next Task Name] (~N min)

[Repeat same structure...]

---

## Final Verification

Run after all tasks complete:
```bash
python -m pytest -v                    # All tests pass
python -m syncopaid.[module]           # Module runs without error
```

## Rollback

If issues arise: `git log --oneline -10` to find commit, then `git revert <hash>`

## Notes

[Edge cases discovered, follow-up work, dependencies on other stories]
```

**Quality Requirements (both modes):**
- **Exact file paths** with line numbers where modifying existing code
- **Complete code** - copy-paste ready, not "add validation here"
- **Exact commands** with expected output (not "run tests")
- **Zero ambiguity** - implementer makes no decisions, just executes
- **Zero context assumption** - explain why, not just what

**CI Mode Autonomy:**
In CI mode, the plan must be executable without human guidance:
- No "choose between A or B" - make the decision in the plan
- No "verify manually" - provide automated verification commands
- No "ask if unclear" - the plan IS the clarity

### Step 6: Update Stage

```python
python -c "
import sqlite3
conn = sqlite3.connect('.claude/data/story-tree.db')
conn.execute('''
    UPDATE story_nodes
    SET stage = 'planned',
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
  Stage: approved -> planned
```

**CI Mode - No stories:**
```
✓ No approved stories available for planning
```

**Interactive Mode:** Conversational summary with handoff options.
