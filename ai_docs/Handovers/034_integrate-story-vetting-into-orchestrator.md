# Handover: Integrate Story-Vetting into Orchestrator

## Task

Add story-vetting as step 3 in the orchestrator's drain-pipeline loop.

## Prerequisites

- Handover 033 complete (`deferred` → `pending` rename done)
- Story-vetting skill updated to handle CI mode (set `pending` status for HUMAN_REVIEW cases)

## Target Architecture

```
drain-pipeline loop:
  1. plan-stories (drain approved)
  2. write-stories (fill capacity)
  3. vet-stories (resolve conflicts)  ← NEW
  4. Check if idle
```

## Key Files

| File | Purpose |
|------|---------|
| `.github/workflows/story-tree-orchestrator.yml` | Add vet-stories step |
| `.claude/skills/story-vetting/SKILL.md` | Skill to invoke |
| `ai_docs/Orchestrator/2025-12-16-Dev-Workflow.md` | Update documentation |

## Implementation

### 1. Update story-vetting skill for CI

Modify `.claude/skills/story-vetting/SKILL.md` to:
- For HUMAN_REVIEW cases: set status to `pending` with conflict details in `notes`
- Skip interactive prompts
- Return summary counts (deleted, merged, rejected, blocked, pending)

### 2. Add to orchestrator workflow

In `.github/workflows/story-tree-orchestrator.yml`, after write-stories:

```bash
# Step 3: Vet stories (resolve conflicts)
echo "=== VET STORIES ==="
vet_output=$(claude --model haiku \
  --prompt "invoke skill: story-vetting" \
  --allowedTools "Bash,Read,Write,Glob,Grep" \
  --dangerously-skip-permissions 2>&1)

# Extract pending count for logging
pending_count=$(echo "$vet_output" | grep -oP 'pending: \K\d+' || echo "0")
if [ "$pending_count" -gt 0 ]; then
  echo "::warning::$pending_count conflicts need human review"
fi

# Commit any changes from vetting
if [ -n "$(git status --porcelain)" ]; then
  git add -A && git commit -m "ci: vet stories" && git push
fi
```

### 3. Update documentation

Update `ai_docs/Orchestrator/2025-12-16-Dev-Workflow.md`:
- Add vet-stories to architecture diagram
- Document the new step in Jobs Specification
- Update loop logic description

## CI Behavior for HUMAN_REVIEW Cases

When vetting finds a scope overlap between concept and non-concept:
1. Set concept's status to `pending`
2. Add to notes: `Conflict with [story_id]: [conflict_type]. Needs human review.`
3. Log warning to GitHub Actions summary
4. Continue workflow (don't block)

Human reviews `pending` stories later via xstory or direct DB query.

## Testing

1. Run orchestrator manually with `max_cycles=1`
2. Verify vet-stories step executes after write-stories
3. Check that conflicts are handled (merged/deleted/pending)
4. Confirm no interactive prompts block CI
