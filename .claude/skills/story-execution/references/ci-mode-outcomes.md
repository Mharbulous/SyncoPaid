# CI Mode Outcomes

Handling execution outcomes in the 5-stage CI pipeline.

## Pipeline Overview

```
setup-and-plan → review-plan → decompose → execute → finalize
```

Each stage produces a result file that the next stage (or finalize) uses.

## Review Outcomes

### Outcome A: Blocking Issues Found

Cannot proceed without human decision.

**ci-review-result.json:**
```json
{
  "outcome": "pause",
  "blocking_issues": [
    {"description": "...", "why_blocking": "...", "options": ["A", "B", "C"]}
  ],
  "deferrable_issues": [],
  "notes": "Plan paused due to blocking issue"
}
```

**Result:** Pipeline stops at review-plan stage.
**Database update:** `stage = 'reviewing'`, `human_review = 1`

### Outcome B: Deferrable Issues Found

Can proceed, but needs post-implementation review.

**ci-review-result.json:**
```json
{
  "outcome": "proceed_with_review",
  "blocking_issues": [],
  "deferrable_issues": [
    {"description": "...", "decision": "...", "rationale": "..."}
  ],
  "notes": "Proceeding with documented decisions"
}
```

**Result:** Pipeline continues through all stages.
**Database update:** `stage = 'reviewing'`, `human_review = 1`

### Outcome C: No Issues

Clean execution path.

**ci-review-result.json:**
```json
{
  "outcome": "proceed",
  "blocking_issues": [],
  "deferrable_issues": [],
  "notes": "No issues identified"
}
```

**Result:** Pipeline continues through all stages.
**Database update:** `stage = 'verifying'`, `human_review = 0`

## Decompose Outcomes

### Simple/Medium Complexity

Execute the plan as-is.

**ci-decompose-result.json:**
```json
{
  "complexity": "medium",
  "task_count": 5,
  "execute_plan": ".claude/data/plans/016_configurable-idle-threshold.md",
  "sub_plans_created": [],
  "notes": "5 tasks, moderate complexity"
}
```

### Complex - Decomposed

Split into sub-plans, execute first one.

**ci-decompose-result.json:**
```json
{
  "complexity": "complex",
  "task_count": 12,
  "execute_plan": ".claude/data/plans/016A_configurable-idle-threshold.md",
  "sub_plans_created": [
    ".claude/data/plans/016B_idle-threshold-integration.md",
    ".claude/data/plans/016C_idle-threshold-ui.md"
  ],
  "notes": "Split into 3 sub-plans"
}
```

**Result:** Execute first sub-plan (A), others picked up in future runs.

## Execute Outcomes

### All Tasks Completed

**ci-execute-result.json:**
```json
{
  "status": "completed",
  "tasks_completed": 5,
  "tasks_total": 5,
  "commits": ["abc1234", "def5678", "ghi9012", "jkl3456", "mno7890"],
  "notes": "All tasks completed successfully"
}
```

### Partial Completion

**ci-execute-result.json:**
```json
{
  "status": "partial",
  "tasks_completed": 3,
  "tasks_total": 5,
  "commits": ["abc1234", "def5678", "ghi9012"],
  "notes": "Stopped at task 4 due to test failure"
}
```

### Failed

**ci-execute-result.json:**
```json
{
  "status": "failed",
  "tasks_completed": 0,
  "tasks_total": 5,
  "commits": [],
  "notes": "Could not start execution - missing dependency"
}
```

## Final Status Summary

| Review | Execute | Final | DB Stage | human_review |
|--------|---------|-------|----------|--------------|
| pause | - | paused | reviewing | 1 |
| proceed_with_review | completed | success | reviewing | 1 |
| proceed | completed | success | verifying | 0 |
| any | partial | partial | reviewing | 1 |
| any | failed | failure | reviewing | 1 |

## Finalize Actions

Based on outcome:

1. **success**: Archive plan, update DB to verifying/reviewing, commit & push
2. **partial**: Keep plan, update DB to reviewing, commit & push what's done
3. **paused**: Keep plan, update DB hold_reason, report blocking issues
4. **failure**: Keep plan, update DB to reviewing, report errors
