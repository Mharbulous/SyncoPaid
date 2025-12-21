# CI Mode Outcomes

Handling execution outcomes when no human is available for feedback.

## Review Outcomes

### Outcome A: Blocking Issues Found

Cannot proceed without human decision.

**temp-CI-notes.json:**
```json
{
  "review": {
    "outcome": "pause",
    "blocking_issues": [
      {"description": "...", "why_blocking": "...", "options": ["A", "B", "C"]}
    ]
  },
  "final_status": "paused"
}
```

**Database update:** `hold_reason = 'paused'`, `human_review = 1`

**Output format:**
```
=== Story Execution Paused ===
Story: [STORY_ID] - [Title]
Status: planned -> paused

BLOCKING ISSUES REQUIRING HUMAN DECISION:

1. [Issue description]
   Why blocking: [explanation]
   Options: [A, B, C...]

Action required: Review issues and update plan, then re-trigger execution.
```

### Outcome B: Deferrable Issues Found

Can proceed, but needs post-implementation review.

**temp-CI-notes.json:**
```json
{
  "review": {
    "outcome": "proceed_with_review",
    "deferrable_issues": [
      {"description": "...", "decision": "...", "rationale": "..."}
    ]
  },
  "final_status": "in_progress"
}
```

**After all batches complete:**
- Set `final_status = "completed"`
- Database: `stage = 'reviewing'`, `human_review = 1`

**Output format:**
```
=== Story Execution Complete (Review Required) ===
Story: [STORY_ID] - [Title]
Tasks: [N]/[N] completed
Status: planned -> active -> reviewing

DECISIONS MADE DURING CI EXECUTION:

1. [Issue identified]
   Decision: [what was decided]
   Rationale: [why this choice]

Action required: Review decisions above, approve or request changes.
```

### Outcome C: No Critical Issues

Clean execution path.

**temp-CI-notes.json:**
```json
{
  "review": {
    "outcome": "proceed",
    "notes": "Critical review: No blocking or deferrable issues identified"
  },
  "final_status": "in_progress"
}
```

**After all batches complete:**
- Set `final_status = "completed"`
- Database: `stage = 'verifying'`, `human_review = 0`

**Output format:**
```
=== Story Execution Complete ===
Story: [STORY_ID] - [Title]
Tasks: [N]/[N] completed
Status: planned -> active -> verifying

Next step: Run story-verification skill to verify acceptance criteria
```

## Batch Failure Handling

If any batch fails:

```python
python -c "
import json

state_file = '.claude/skills/story-execution/temp-CI-notes.json'
with open(state_file) as f:
    state = json.load(f)

state['final_status'] = 'failed'

# Find failed batch
failed_batch = next((b for b in state['batches'] if b['status'] == 'failed'), None)
failed_task = next((t for t in state['tasks'] if t['status'] == 'failed'), None)

state['failure'] = {
    'batch': failed_batch['batch'] if failed_batch else None,
    'task': failed_task['id'] if failed_task else None,
    'reason': failed_task.get('notes', 'Unknown failure') if failed_task else 'Unknown'
}

with open(state_file, 'w') as f:
    json.dump(state, f, indent=2)

print(json.dumps(state['failure'], indent=2))
"
```

**Output format:**
```
=== Execution Blocked ===
Story: [STORY_ID] - [Title]
Completed: [M]/[N] tasks
Blocked at: Task [M+1] - [task_name]
Status: active -> paused

Issue: [description of blocker]
Need: [what clarification or help is needed]
```

## Final Status Summary

| Review Outcome | Batch Status | Final Status | DB Stage | human_review |
|----------------|--------------|--------------|----------|--------------|
| pause | - | paused | active (hold_reason=paused) | 1 |
| proceed_with_review | all completed | completed | reviewing | 1 |
| proceed | all completed | completed | verifying | 0 |
| any | any failed | failed | active (hold_reason=paused) | 1 |
