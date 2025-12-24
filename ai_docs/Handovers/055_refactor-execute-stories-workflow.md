# Handover: Refactor execute-stories.yml into Modular Components

## Objective

Decompose `.github/workflows/execute-stories.yml` (1686 lines) into smaller, maintainable components using GitHub Actions' reusable workflows and composite actions.

## Current State

The workflow has 6 jobs with these line counts:

| Job | Lines | Notes |
|-----|-------|-------|
| setup-and-plan | 283 | Plan selection, validation |
| identify-plan | 145 | Story ID matching |
| review-plan | 112 | Claude review step |
| decompose | 156 | Complexity assessment |
| execute | 264 | Claude execution step |
| **finalize** | **684** | 40% of file - main target |

### Finalize Job Breakdown

| Step | Lines | Refactor Target |
|------|-------|-----------------|
| FN.13 Post results to story issue | 283 | Composite action |
| FN.9 Generate execution summary | 69 | Composite action |
| FN.3 Determine final outcome | 68 | Keep inline |
| FN.12 Parse result files | 67 | Composite action |
| FN.5 Update story status in database | 56 | Composite action |
| FN.10 Report pipeline status | 53 | Merge with FN.9 |

## Recommended Approach

### 1. Composite Actions (step-level reuse)

Create in `.github/actions/`:

```
.github/actions/
├── post-story-results/action.yml    # FN.13 (283 lines)
├── generate-summary/action.yml      # FN.9 + FN.10 (~120 lines)
├── parse-results/action.yml         # FN.12 (67 lines)
└── update-story-db/action.yml       # FN.5 (56 lines)
```

Composite action structure:
```yaml
# .github/actions/post-story-results/action.yml
name: Post Story Results
inputs:
  story_id:
    required: true
  outcome:
    required: true
  # ... other inputs
runs:
  using: composite
  steps:
    - run: |
        # Shell logic moved here
      shell: bash
```

### 2. Alternative: Reusable Workflow

Could extract entire `finalize` job to `.github/workflows/finalize-execution.yml` with `workflow_call` trigger. Trade-off: adds workflow dispatch overhead but cleaner separation.

## Key Files

| File | Purpose |
|------|---------|
| `.github/workflows/execute-stories.yml` | Main workflow to refactor |
| `.claude/commands/ci-*.md` | Claude prompts (already extracted) |
| `.claude/skills/story-execution/ci-*-result.json` | Result file schemas |

## Technical Notes

- Composite actions share the runner's environment (no container overhead)
- Inputs/outputs must be explicitly declared in `action.yml`
- Shell scripts in composite actions use `shell: bash` (required)
- `$GITHUB_OUTPUT` and `$GITHUB_STEP_SUMMARY` work normally in composite actions

## Success Criteria

- `execute-stories.yml` reduced to ~400 lines
- Composite actions are independently testable
- No change to workflow behavior or outputs
- Issue comments and summaries render identically
