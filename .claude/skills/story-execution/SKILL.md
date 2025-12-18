---
name: story-execution
description: Use when user says "execute plan", "implement story", "run plan for [ID]", "start implementation", or asks to execute a planned story - loads TDD implementation plan from .claude/data/plans/, executes RED-GREEN-COMMIT cycles for each task, updates story status through active→reviewing→implemented, verifies acceptance criteria, and outputs implementation report. (project) (project) (project)
---

# Story Execution

Load plan from story-tree database, review critically, execute tasks in batches, report for review between batches.

**Announce:** On activation, say: "I'm using the story-execution skill to implement this plan."

## Mode Detection

**CI Mode** activates when:
- Environment variable `CI=true` is set, OR
- Trigger phrase includes "(ci)" like "execute plan (ci)"

**CI Mode behavior:**
- No human available for immediate feedback
- Critical review determines whether to proceed, pause, or proceed with review flag
- Executes all batches without waiting for feedback between batches
- Final status depends on critical review outcome

**Interactive Mode** (default):
- Pause after each batch for human feedback
- Ask for clarification when concerns arise
- Human guides decisions in real-time

## The Process

### Step 1: Select and Load Plan

**If user provides story ID or filename:**
- Load the specified plan from `.claude/data/plans/`

**If no plan specified (auto-select):**
Query the story-tree database for planned stories (oldest first):

```python
python -c "
import sqlite3, json
conn = sqlite3.connect('.claude/data/story-tree.db')
conn.row_factory = sqlite3.Row

planned = conn.execute('''
    SELECT id, title, notes FROM story_nodes
    WHERE stage = 'planned'
      AND hold_reason IS NULL AND disposition IS NULL
    ORDER BY updated_at ASC
''').fetchall()

for story in planned:
    notes = story['notes'] or ''
    plan_line = [l for l in notes.split('\n') if 'Plan:' in l]
    plan_path = plan_line[0].split('Plan:')[1].strip() if plan_line else None
    print(json.dumps({
        'id': story['id'],
        'title': story['title'],
        'plan_path': plan_path
    }))
conn.close()
"
```

Select the first available plan and read the plan file.

### Step 1.5: Dependency Check

Before proceeding, verify the story's dependencies are met:

1. **Check dependency stories** - Extract story IDs mentioned in description/notes (patterns like "1.2", "depends on X")
2. **Verify dependencies are implemented** - Referenced stories must be in stage >= `implemented`
3. **Check all children are planned** - All child stories must be in stage >= `planned`

```python
python -c "
import sqlite3, re, json
conn = sqlite3.connect('.claude/data/story-tree.db')

story_id = '[STORY_ID]'  # Replace with actual ID

# Get story details
story = conn.execute('SELECT description, notes FROM story_nodes WHERE id = ?', (story_id,)).fetchone()
if not story:
    print(json.dumps({'ready': False, 'reason': 'Story not found'}))
    exit()

text = (story[0] or '') + ' ' + (story[1] or '')

# Extract dependency IDs (patterns: 1.2, 1.3.1, etc., or explicit 'depends on X')
dep_pattern = r'(?:depends on|requires|after|needs)\s+(\d+(?:\.\d+)*)|(?<!\d)(\d+\.\d+(?:\.\d+)*)(?!\d)'
deps = set()
for match in re.finditer(dep_pattern, text, re.IGNORECASE):
    dep_id = match.group(1) or match.group(2)
    if dep_id and dep_id != story_id:
        deps.add(dep_id)

# Check dependency stories are implemented (stage >= implemented)
IMPLEMENTED_STAGES = ('implemented', 'ready', 'polish', 'released')
unmet_deps = []
for dep_id in deps:
    dep = conn.execute('SELECT stage FROM story_nodes WHERE id = ? AND disposition IS NULL', (dep_id,)).fetchone()
    if dep and dep[0] not in IMPLEMENTED_STAGES:
        unmet_deps.append({'id': dep_id, 'stage': dep[0]})

# Check all children are at least planned
PLANNED_OR_LATER = ('planned', 'active', 'reviewing', 'verifying', 'implemented', 'ready', 'polish', 'released')
unplanned_children = []
children = conn.execute('''
    SELECT s.id, s.title, s.stage FROM story_nodes s
    JOIN story_paths p ON s.id = p.descendant_id
    WHERE p.ancestor_id = ? AND p.depth = 1
      AND s.disposition IS NULL
''', (story_id,)).fetchall()

for child in children:
    if child[2] not in PLANNED_OR_LATER:
        unplanned_children.append({'id': child[0], 'title': child[1], 'stage': child[2]})

ready = len(unmet_deps) == 0 and len(unplanned_children) == 0
print(json.dumps({
    'ready': ready,
    'dependencies_found': list(deps),
    'unmet_dependencies': unmet_deps,
    'unplanned_children': unplanned_children
}))
conn.close()
"
```

**If ready:** Proceed to Step 2 (which transitions to `active`).

**If not ready:** Block the story and try the next candidate:

```python
# Block story with dependency issues
conn.execute('''
    UPDATE story_nodes
    SET hold_reason = 'blocked', human_review = 1,
        notes = COALESCE(notes || chr(10), '') || 'BLOCKED - Dependencies not met: ' || datetime('now') || chr(10) || ?,
        updated_at = datetime('now')
    WHERE id = ?
''', (blocking_reason, story_id))
conn.commit()
```

### Step 2: Review Plan Critically

Before executing anything:
- Read the entire plan
- Identify any questions, concerns, or ambiguities
- Check prerequisites (dependencies implemented, baseline tests pass)

Classify any concerns found:
- **Blocking issues:** Require human decision before implementation (architectural choices, security implications, breaking changes)
- **Deferrable issues:** Can be addressed by post-implementation refactoring (code style, minor optimizations, naming conventions)

#### Interactive Mode

**If concerns exist:** Raise them before starting. Ask for clarification.

**If no concerns:**
- Create a TodoWrite with all tasks from the plan
- Update story status to `active`
- Proceed to execution

#### CI Mode - Critical Review Outcomes

**Outcome A: Blocking issues found** (cannot proceed without human decision)
- Update status to `paused`
- Add detailed notes describing the blocking issues and why human decision is required
- Do NOT proceed with implementation
- Output the blocking issues report

**Outcome B: Deferrable issues found** (can proceed, needs post-implementation review)
- Add notes documenting:
  - Issues identified
  - Decisions made in absence of human
  - Rationale for proceeding
- Update story status to `active`
- Proceed with implementation
- Flag for `reviewing` status at completion (not `implemented`)

**Outcome C: No critical issues found**
- Add note: "Critical review: No blocking or deferrable issues identified"
- Update story status to `active`
- Proceed with implementation
- Will set `verifying` status at completion (post-execution verification required)

### Step 3: Execute Batch

Default approach: handle **3 tasks** at a time.

For each task in the batch:
1. Mark as `in_progress` in TodoWrite
2. Follow each step exactly as written in the plan
3. Execute the TDD cycle: RED → GREEN → COMMIT
4. Run specified verifications
5. Mark as `completed`

**TDD Cycle per Task:**
- **RED:** Write failing test, verify it fails for the right reason
- **GREEN:** Write minimal implementation, verify test passes
- **COMMIT:** Stage and commit with story ID in message

### Step 4: Report

When batch is complete:
- Show what was implemented (files changed, tests added)
- Display verification output (test results)
- Update progress in story notes

#### Interactive Mode
Say: **"Ready for feedback."**

#### CI Mode
Continue immediately to next batch (no pause).

### Step 5: Continue or Adjust

#### Interactive Mode
Based on feedback:
- Apply any requested changes
- Execute next batch of 3 tasks
- Repeat until all tasks complete

#### CI Mode
- Execute all remaining batches without pause
- If mid-execution blocker encountered, update status to `paused` and stop

### Step 6: Complete and Verify

After all tasks complete:
1. Run full test suite
2. Verify each acceptance criterion from the story
3. Link commits to story in database
4. Update final status based on mode and review outcome

#### Final Status Determination

**Interactive Mode:**
- Update status: `active` → `reviewing` → `verifying`

**CI Mode - Based on Step 2 outcome:**
- **Outcome B (deferrable issues):** Set status to `reviewing`
  - Human needs to review decisions made during CI execution
- **Outcome C (no issues):** Set status to `verifying`
  - Clean execution, post-execution verification required via story-verification skill

**Announce:** "I'm using the story-verification skill to verify acceptance criteria."

## When to Stop and Ask for Help

Stop immediately when encountering:
- **Mid-batch blockers:** Missing dependencies, failed tests that shouldn't fail, unclear instructions
- **Critical plan gaps:** Missing information that prevents starting a task
- **RED phase passes:** Test should fail but passes (feature may already exist)
- **Repeated verification failures:** Same test failing after multiple attempts
- **Regression detected:** Existing tests fail after implementation

**Ask for clarification rather than guessing.** Don't force through blockers.

## When to Revisit Earlier Steps

Return to plan review when:
- User updates the plan based on your feedback
- Fundamental approach needs rethinking after discovering new information
- Dependencies change mid-execution

## Remember

- **Review plan critically first** - raise concerns before starting
- **Follow plan steps exactly** - the plan was designed for copy-paste execution
- **Don't skip verifications** - RED must fail, GREEN must pass
- **Batch execution with checkpoints** - 3 tasks, then report
- **Interactive: report and wait** - don't continue without feedback
- **CI Mode: classify issues** - blocking → pause, deferrable → proceed with review flag
- **Stop when blocked; don't guess** - pause and document for human review

## Database Integration

**Database:** `.claude/data/story-tree.db`
**Plans:** `.claude/data/plans/`
**Critical:** Use Python sqlite3 module, NOT sqlite3 CLI.

### Stage/Hold Updates (Three-Field System)

```python
# Update to active (Step 2 - proceeding with execution)
conn.execute('''
    UPDATE story_nodes
    SET stage = 'active',
        notes = COALESCE(notes || chr(10), '') || 'Execution started: ' || datetime('now'),
        updated_at = datetime('now')
    WHERE id = ?
''', (story_id,))

# Update to paused (CI Mode - blocking issues found)
# Note: stage stays 'active', hold_reason indicates why stopped
conn.execute('''
    UPDATE story_nodes
    SET hold_reason = 'paused', human_review = 1,
        notes = COALESCE(notes || chr(10), '') || 'PAUSED - Blocking issues require human decision: ' || datetime('now') || chr(10) || ?,
        updated_at = datetime('now')
    WHERE id = ?
''', (blocking_issues_description, story_id))

# Update to reviewing (CI Mode Outcome B, or Interactive Mode step)
conn.execute('''
    UPDATE story_nodes
    SET stage = 'reviewing', human_review = 1,
        notes = COALESCE(notes || chr(10), '') || 'Awaiting human review of CI decisions: ' || datetime('now'),
        updated_at = datetime('now')
    WHERE id = ?
''', (story_id,))

# Update to verifying (CI Mode Outcome C, or after Interactive Mode)
conn.execute('''
    UPDATE story_nodes
    SET stage = 'verifying', human_review = 0,
        notes = COALESCE(notes || chr(10), '') || 'Execution complete, awaiting verification: ' || datetime('now'),
        updated_at = datetime('now')
    WHERE id = ?
''', (story_id,))

# Clear hold after human resolves issue (resume from preserved stage)
conn.execute('''
    UPDATE story_nodes
    SET hold_reason = NULL, human_review = 0,
        notes = COALESCE(notes || chr(10), '') || 'Hold cleared, resuming: ' || datetime('now'),
        updated_at = datetime('now')
    WHERE id = ?
''', (story_id,))
```

### Commit Linking

After execution, link commits to story:
```python
conn.execute('''
    INSERT OR IGNORE INTO story_commits (story_id, commit_hash, commit_date, commit_message)
    VALUES (?, ?, datetime('now'), ?)
''', (story_id, commit_hash, commit_message))
```

## Output Format

### Batch Complete (Interactive Mode)
```
=== Batch Complete (Tasks 1-3 of 8) ===
Implemented:
- Task 1: [name] ✓
- Task 2: [name] ✓
- Task 3: [name] ✓

Tests: 12 passed, 0 failed
Files changed: 4

Ready for feedback.
```

### Execution Complete
```
=== Story Execution Complete ===
Story: [STORY_ID] - [Title]
Tasks: [N]/[N] completed
Status: planned → active → [reviewing|verifying]

Next step: Run story-verification skill to verify acceptance criteria

Acceptance Criteria:
[x] Criterion 1
[x] Criterion 2
[x] Criterion 3
```

### CI Mode - Paused (Blocking Issues)
```
=== Story Execution Paused ===
Story: [STORY_ID] - [Title]
Status: planned → paused

BLOCKING ISSUES REQUIRING HUMAN DECISION:

1. [Issue description]
   Why blocking: [explanation]
   Options: [A, B, C...]

2. [Issue description]
   Why blocking: [explanation]
   Options: [A, B, C...]

Action required: Review issues and update plan, then re-trigger execution.
```

### CI Mode - Complete with Review Flag
```
=== Story Execution Complete (Review Required) ===
Story: [STORY_ID] - [Title]
Tasks: [N]/[N] completed
Status: planned → active → reviewing

DECISIONS MADE DURING CI EXECUTION:

1. [Issue identified]
   Decision: [what was decided]
   Rationale: [why this choice]

2. [Issue identified]
   Decision: [what was decided]
   Rationale: [why this choice]

Action required: Review decisions above, approve or request changes.
```

### Blocked (Mid-Execution)
```
=== Execution Blocked ===
Story: [STORY_ID] - [Title]
Completed: [M]/[N] tasks
Blocked at: Task [M+1] - [task_name]
Status: active → paused

Issue: [description of blocker]
Need: [what clarification or help is needed]
```

## Related Skills

- **story-planning:** Creates the plans this skill executes
- **story-verification:** Verifies acceptance criteria after execution
- **story-tree:** Manages story hierarchy and status

## References

- Plan format: `.claude/data/plans/*.md`
- Stage workflow: concept → approved → planned → active → reviewing → verifying → implemented
- `planned` → `active`: After dependency check passes (Step 1.5 → Step 2)
- Dependencies not met: `hold_reason = 'blocked'`
- CI pause: hold_reason='paused' (stage preserved at 'active')
- Three-field system: stage shows position, hold_reason shows why stopped, stage preserved when held
- Commit format: Include `Story: [ID]` in commit body for traceability
