# 049: Implement Multi-Call Workflow

## Goal
Update `.github/workflows/execute-stories.yml` to use multiple `claude-code-action` calls in Phase 5, each invoking the `story-execution` skill with shared state.

## Prerequisites
- Handover 047 complete: Phase 5 step breakdown defined
- Handover 048 complete: Skill references created

## Context

Current Phase 5:
```yaml
- name: "5.1 Execute plan with Claude"
  uses: anthropics/claude-code-action@v1
  # Single call does everything
```

Target Phase 5:
```yaml
- name: "5.1 Review plan critically"
  uses: anthropics/claude-code-action@v1
  # Writes review outcome to temp-CI-notes.json

- name: "5.2 Execute batch 1"
  if: # review passed
  uses: anthropics/claude-code-action@v1
  # Reads from temp-CI-notes.json, executes tasks 1-3

- name: "5.3 Execute batch 2"
  if: # batch 1 succeeded and more tasks remain
  # ... and so on
```

## Shared State Pattern

Each Claude call:
1. Reads `.claude/skills/story-execution/temp-CI-notes.json`
2. Does its work
3. Writes updated state back

Workflow conditionals check the JSON to decide next steps.

## Key Challenges

### Dynamic Batch Count
Plans have variable task counts. Options:
- **Fixed max batches**: 5.2, 5.3, 5.4, 5.5 (skip if no tasks)
- **Loop in bash**: Parse task count, run N calls
- **Single execution call**: One call for all tasks (simpler)

Recommend: Start with fixed max (4 batches = 12 tasks max), add more if needed.

### Conditional Execution
```yaml
- name: "5.2 Execute batch 1"
  if: |
    steps.review.outputs.outcome == 'proceed' &&
    steps.review.outputs.task_count > 0
```

Need to extract values from temp-CI-notes.json into step outputs.

## Key Files

- `.github/workflows/execute-stories.yml` - modify this
- `.claude/skills/story-execution/SKILL.md` - invoked by each call
- `.claude/skills/story-execution/temp-CI-notes.json` - shared state

## Prompt Pattern

Each Claude call gets a focused prompt:

```yaml
prompt: |
  Use story-execution skill in CI mode.
  Phase: REVIEW  # or EXECUTE_BATCH_1, EXECUTE_BATCH_2, etc.
  Plan: ${{ steps.select-plan.outputs.path }}

  Read/write state: .claude/skills/story-execution/temp-CI-notes.json
```

The skill's SKILL.md reads the phase and loads appropriate references.

## Tasks

1. Add JSON read step after each Claude call to extract outputs
2. Implement 5.1 (review) with conditional for blocking issues
3. Implement 5.2-5.5 (batches) with task range parameters
4. Update Phase 6 to read final state from JSON
5. Test with a simple plan

## Testing

Run workflow manually via `workflow_dispatch` and check:
- Each step visible separately in Actions UI
- temp-CI-notes.json updated correctly between calls
- Failures isolated to specific steps

## Output

Working multi-call workflow with shared state.
