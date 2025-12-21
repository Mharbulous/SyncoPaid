# TDD Execution

Execute all tasks in the plan following strict RED-GREEN-COMMIT cycle.

## Reading the Plan

The plan document is the source of truth. It contains:
- Task list with numbered tasks
- For each task: RED (test code), GREEN (implementation code), COMMIT (message)
- Verification commands to run

Read the entire plan first, then execute each task sequentially.

## TDD Cycle per Task

### RED: Write Failing Test

1. Write the test as specified in the plan
2. Run the test suite
3. **Verify the new test FAILS** for the expected reason

```bash
# Run tests
python -m pytest tests/ -v --tb=short
```

**If test passes:** STOP. Feature may already exist. Document and continue to next task.

### GREEN: Minimal Implementation

1. Write the minimal code to make the test pass
2. Follow plan implementation steps exactly
3. Run the test suite again

```bash
python -m pytest tests/ -v --tb=short
```

**If test fails:** Debug and fix. Do not proceed until test passes.

### COMMIT: Stage and Commit

```bash
# Stage changes
git add -A

# Commit with story ID
git commit -m "feat: [task description]

Story: [STORY_ID]
Task: [TASK_NUMBER] of [TOTAL_TASKS]"
```

## Tracking Progress

After each task, note:
- Task number completed
- Commit hash
- Any issues encountered

At the end, write the result to `.claude/skills/story-execution/ci-execute-result.json`:

```json
{
  "status": "completed",
  "tasks_completed": 5,
  "tasks_total": 5,
  "commits": ["abc1234", "def5678", "ghi9012", "jkl3456", "mno7890"],
  "notes": "All tasks completed successfully"
}
```

## Status Values

- `completed`: All tasks finished successfully
- `partial`: Some tasks completed, but stopped early
- `failed`: Unable to complete due to errors

## When to Stop

Stop and set status to 'failed' when:
- Test should fail but passes (feature already exists)
- Test fails for wrong reason (wrong implementation path)
- Cannot find file/function mentioned in plan
- Repeated failures after 3 attempts
- Regression detected (existing tests fail)

## Example Execution

Given a plan with 3 tasks:

1. Read task 1 from plan
2. Write test code exactly as specified
3. Run pytest, verify test fails
4. Write implementation code as specified
5. Run pytest, verify test passes
6. Commit: "feat: add validation for idle threshold - Task 1/3"
7. Repeat for tasks 2 and 3
8. Write result JSON with all commit hashes
