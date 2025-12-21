---
name: story-execution
description: Use when user says "execute plan", "implement story", "run plan for [ID]", "start implementation", or asks to execute a planned story - loads TDD implementation plan from .claude/data/plans/, executes RED-GREEN-COMMIT cycles for each task, updates story status through active->reviewing->implemented, verifies acceptance criteria, and outputs implementation report. (project)
disable-model-invocation: true
---

# Story Execution

Load plan from story-tree database, review critically, execute tasks in batches, report for review between batches.

**Announce:** On activation, say: "I'm using the story-execution skill to implement this plan."

## Mode Detection

**CI Mode** activates when:
- Environment variable `CI=true` is set, OR
- Trigger phrase includes "(ci)" like "execute plan (ci)"
- Prompt includes `Phase: REVIEW` or `Phase: EXECUTE_BATCH`

**Interactive Mode** (default): Pause after each batch for human feedback.

## CI Mode Phases

When `Phase:` is specified in the prompt, load the appropriate reference:

| Phase | Reference | Purpose |
|-------|-----------|---------|
| `REVIEW` | `references/critical-review.md` | Review plan, classify issues |
| `EXECUTE_BATCH` | `references/tdd-execution.md` | TDD cycle for task batch |

**Shared state:** `.claude/skills/story-execution/temp-CI-notes.json`

### Phase: REVIEW

Load reference: `references/critical-review.md`

1. Initialize temp-CI-notes.json with plan info
2. Read and review plan critically
3. Classify issues as blocking or deferrable
4. Write review outcome to temp-CI-notes.json
5. Update database (load `references/database-updates.md`)

### Phase: EXECUTE_BATCH

Load reference: `references/tdd-execution.md`

1. Read temp-CI-notes.json for task list and batch number
2. Execute tasks in specified range using TDD cycle
3. RED (failing test) -> GREEN (implementation) -> COMMIT
4. Update task status and commits in temp-CI-notes.json
5. Update database (load `references/database-updates.md`)

For outcome handling: Load `references/ci-mode-outcomes.md`

## Interactive Mode Workflow

### Step 1: Select and Load Plan

Scan `.claude/data/plans/` for earliest sequence-numbered plan file:

```python
python -c "
import os, re, json
plans_dir = '.claude/data/plans'
pattern = re.compile(r'^(\d{3})([A-Z])?_(.+)\.md$')
plans = []
for f in os.listdir(plans_dir):
    m = pattern.match(f)
    if m:
        plans.append({'filename': f, 'path': os.path.join(plans_dir, f), 'sequence': int(m.group(1)), 'letter': m.group(2) or ''})
plans.sort(key=lambda x: (x['sequence'], x['letter']))
print(json.dumps(plans[0] if plans else {'selected': None}))
"
```

**If no plans found:** Output "No plan files available for execution" and exit.

### Step 2: Review Plan Critically

Load reference: `references/critical-review.md`

- Read the entire plan
- Identify concerns and classify as blocking or deferrable
- If concerns: Raise them before starting
- If no concerns: Create TodoWrite with tasks, proceed to execution

### Step 3: Execute Batch (3 tasks at a time)

Load reference: `references/tdd-execution.md`

For each task:
1. Mark as `in_progress`
2. Follow TDD cycle: RED -> GREEN -> COMMIT
3. Mark as `completed`

### Step 4: Report

When batch complete:
- Show what was implemented
- Display verification output

**Interactive:** Say "Ready for feedback." and wait.
**CI Mode:** Continue to next batch immediately.

### Step 5: Continue or Adjust

Based on feedback:
- Apply requested changes
- Execute next batch
- Repeat until complete

### Step 6: Complete and Verify

Load reference: `references/database-updates.md`

1. Run full test suite
2. Verify acceptance criteria
3. Link commits to story
4. Archive plan file to `.claude/data/executed/`
5. Update story status

## Database Integration

Load reference: `references/database-updates.md`

**Database:** `.claude/data/story-tree.db`
**Critical:** Use Python sqlite3 module, NOT sqlite3 CLI.

## When to Stop

- Missing dependencies
- Failed tests that shouldn't fail
- RED phase passes (feature already exists)
- Repeated failures
- Regression detected

**Ask for clarification rather than guessing.** Don't force through blockers.

## Related Skills

- **story-planning:** Creates the plans this skill executes
- **story-verification:** Verifies acceptance criteria after execution
- **story-tree:** Manages story hierarchy and status
