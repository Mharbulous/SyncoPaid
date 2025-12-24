# Execute Plan - TDD Implementation

Execute a TDD implementation plan following strict Red-Green-Commit discipline.

**Arguments:**
- `$ARGUMENTS` - Path to the plan file (e.g., `.claude/data/plans/024A_feature-part1.md`)

---

## ENVIRONMENT

- **Runner:** ubuntu-latest (Linux) when in CI
- **Python venv:** Use `source venv/bin/activate` NOT `venv\Scripts\activate`
- **Paths:** Use Linux paths with forward slashes in CI, Windows paths locally

## YOUR TASK

1. Read the plan document at `$ARGUMENTS` completely
2. Follow EACH task's TDD steps EXACTLY as written in the plan:
   - **RED**: Write the failing test as specified
   - **Verify RED**: Run the test, confirm it fails for the right reason
   - **GREEN**: Implement the code as specified
   - **Verify GREEN**: Run the test, confirm it passes
   - **COMMIT**: Stage and commit with the message format shown
3. Continue through ALL tasks in the plan
4. After each task, immediately commit your changes

## TDD DISCIPLINE

- Follow the plan's test code EXACTLY - do not modify tests
- Follow the plan's implementation code as a guide
- If a test already passes (RED fails to be RED), note it and move on
- If you get stuck on a task, document what happened and continue

## COMMIT FORMAT

Use the format specified in the plan, typically:
```
feat: [task description]

Story: [story_id]
Task: N of M
```

## OUTPUT REQUIRED

After completing all tasks, write to `.claude/skills/story-execution/ci-execute-result.json`:

```json
{
  "status": "completed",
  "tasks_completed": 2,
  "tasks_total": 2,
  "commits": ["abc1234", "def5678"],
  "files_modified": ["src/syncopaid/feature.py", "tests/test_feature.py"],
  "notes": "Both tasks completed successfully. All tests passing.",
  "error": null
}
```

If partial completion:
```json
{
  "status": "partial",
  "tasks_completed": 1,
  "tasks_total": 2,
  "commits": ["abc1234"],
  "files_modified": ["src/syncopaid/feature.py"],
  "notes": "Task 1 completed, Task 2 blocked by import error",
  "error": "ModuleNotFoundError: No module named 'missing_dep'"
}
```

If failed:
```json
{
  "status": "failed",
  "tasks_completed": 0,
  "tasks_total": 2,
  "commits": [],
  "files_modified": [],
  "notes": "Could not start execution",
  "error": "Plan file references non-existent base class"
}
```

## IMPORTANT FOR RESULT FILE

- Include ALL commit SHAs you created (full 40-char or short 7-char)
- List the key files you modified (not every file, just the main ones)
- If status is "failed" or "partial", explain WHY in the error field

## VERIFICATION STEPS

- Read the plan document directly - it contains all instructions
- The plan has explicit test code and implementation code to follow
- Do NOT skip the verification steps (run pytest after each RED and GREEN)
- Commit your changes after each task (push is handled automatically by the workflow)

## HUMAN-READABLE OUTPUT

After writing the JSON, print a summary:

```
## Execution Result: [COMPLETED/PARTIAL/FAILED]

**Plan:** [filename]
**Tasks:** [completed]/[total]

### Commits Made
- `abc1234` - feat: [description]
- `def5678` - feat: [description]

### Files Modified
- src/syncopaid/feature.py
- tests/test_feature.py

### Notes
[Summary of what was accomplished or why it failed]
```
