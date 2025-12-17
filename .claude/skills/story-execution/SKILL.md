---
name: story-execution
description: Use when user says "execute plan", "implement story", "run plan for [ID]", "start implementation", or asks to execute a planned story - loads TDD implementation plan from .claude/data/plans/, executes RED-GREEN-COMMIT cycles for each task, updates story status through active→reviewing→implemented, verifies acceptance criteria, and outputs implementation report. (project) (project)
---

# Story Execution

Load plan from story-tree database, review critically, execute tasks in batches, report for review between batches.

**Announce:** On activation, say: "I'm using the story-execution skill to implement this plan."

## The Process

### Step 1: Select and Load Plan

**If user provides story ID or filename:**
- Load the specified plan from `.claude/data/plans/`

**If no plan specified (auto-select):**
Query the story-tree database for planned stories, prioritizing:
1. Stories with no blocking dependencies
2. Stories with all dependencies already implemented
3. Oldest planned stories (by updated_at)

```python
python -c "
import sqlite3, json
conn = sqlite3.connect('.claude/data/story-tree.db')
conn.row_factory = sqlite3.Row

# Get planned stories ordered by readiness
planned = conn.execute('''
    SELECT id, title, notes FROM story_nodes
    WHERE status = 'planned'
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

Select the most ready plan and read the plan file.

### Step 2: Review Plan Critically

Before executing anything:
- Read the entire plan
- Identify any questions, concerns, or ambiguities
- Check prerequisites (dependencies implemented, baseline tests pass)

**If concerns exist:** Raise them before starting. Ask for clarification.

**If no concerns:**
- Create a TodoWrite with all tasks from the plan
- Update story status to `active`
- Proceed to execution

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

Say: **"Ready for feedback."**

### Step 5: Continue or Adjust

Based on feedback:
- Apply any requested changes
- Execute next batch of 3 tasks
- Repeat until all tasks complete

### Step 6: Complete and Verify

After all tasks complete:
1. Run full test suite
2. Verify each acceptance criterion from the story
3. Update status: `active` → `reviewing` → `implemented`
4. Link commits to story in database

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
- **Between batches: report and wait** - don't continue without feedback
- **Stop when blocked; don't guess** - ask for help immediately

## Database Integration

**Database:** `.claude/data/story-tree.db`
**Plans:** `.claude/data/plans/`
**Critical:** Use Python sqlite3 module, NOT sqlite3 CLI.

### Status Updates

```python
# Update to active (Step 2)
conn.execute('''
    UPDATE story_nodes
    SET status = 'active',
        notes = COALESCE(notes || chr(10), '') || 'Execution started: ' || datetime('now'),
        updated_at = datetime('now')
    WHERE id = ?
''', (story_id,))

# Update to reviewing (Step 6)
conn.execute('''
    UPDATE story_nodes
    SET status = 'reviewing',
        updated_at = datetime('now')
    WHERE id = ?
''', (story_id,))

# Update to implemented (after verification)
conn.execute('''
    UPDATE story_nodes
    SET status = 'implemented',
        last_implemented = datetime('now'),
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

### Batch Complete
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
Status: planned → active → reviewing → implemented

Acceptance Criteria:
[x] Criterion 1
[x] Criterion 2
[x] Criterion 3
```

### Blocked
```
=== Execution Blocked ===
Story: [STORY_ID] - [Title]
Completed: [M]/[N] tasks
Blocked at: Task [M+1] - [task_name]

Issue: [description of blocker]
Need: [what clarification or help is needed]
```

## Related Skills

- **story-planning:** Creates the plans this skill executes
- **story-verification:** Verifies acceptance criteria after execution
- **story-tree:** Manages story hierarchy and status

## References

- Plan format: `.claude/data/plans/*.md`
- Status workflow: concept → approved → planned → active → reviewing → implemented
- Commit format: Include `Story: [ID]` in commit body for traceability
