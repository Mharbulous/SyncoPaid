# Meta-Workflow Design Handover

## Task
Design GitHub Actions meta-workflow to orchestrate story-tree automation. Continue from v3, iterate up to v6 max before getting user feedback.

## User Feedback on v3 (Critical)

**1. Pipeline order is backwards**
- v3 order: write-stories → plan-stories → synthesize-goals
- Problem: Creates concept glut. Approved stories pile up waiting for planning.
- Fix: Prioritize downstream steps first. Clear the pipeline before adding more concepts.
- Correct order: plan-stories → write-stories (→ synthesize-goals daily only)

**2. Single cycle per night defeats purpose**
- Goal: "Constantly working even while I sleep"
- v3 runs once at 2am, stops. Leaves work undone.
- Fix: Loop until no work remains (NO_CAPACITY AND NO_APPROVED)

**3. Synthesize-goals is wrong cadence**
- It interprets user choices → only changes when user acts
- No user input during CI → no reason to re-synthesize
- Fix: Keep synthesize-goals as separate daily workflow, not part of the loop

## Key Files

| File | Purpose |
|------|---------|
| `ai_docs/Plans/meta-workflow.json` | Current v3 design spec |
| `ai_docs/Plans/meta-workflow.md` | Current v3 documentation |
| `.github/workflows/write-stories.yml` | Existing - generates concepts |
| `.github/workflows/plan-stories.yml` | Existing - plans approved stories |
| `.github/workflows/synthesize-goals-non-goals.yml` | Existing - daily visualization |
| `.claude/scripts/story_workflow.py` | Returns `NO_CAPACITY` when tree full |
| `ai_docs/story-tree-skill-overview.md` | Explains story statuses and flow |

## Story Status Flow
```
concept → [user approves] → approved → [plan-stories] → planned → ...
```

## Stop Signals
- `NO_CAPACITY`: All tree nodes at capacity (write-stories has nothing to do)
- `NO_APPROVED`: No approved stories waiting (plan-stories has nothing to do)
- Both true = pipeline idle, stop looping

## Design Requirements

1. **Master switch**: Single repo variable to enable/disable
2. **Sequential execution**: One workflow at a time (shared SQLite DB)
3. **Loop until idle**: Keep cycling plan→write until both return no-work
4. **Concurrency safety**: Prevent parallel runs
5. **Daily synthesis**: synthesize-goals runs separately, once per day

## Previous Design Flaws (Don't Repeat)

| Version | Flaw |
|---------|------|
| v1 | `workflow_call` misconception - doesn't give true sequential execution |
| v2 | Over-engineered PAUSED state, state files add git noise |
| v3 | Wrong pipeline order, single cycle, synthesize in loop |

## Technical Constraints

- GitHub Actions doesn't support true loops in workflows
- Options: recursive workflow_dispatch, or run multiple cycles in single job
- Claude Code action outputs are hard to capture as workflow outputs
- Concurrency group: `story-tree-automation`

## Branch
`claude/setup-github-actions-EFeMY`

## Deliverables
1. Updated `ai_docs/Plans/meta-workflow.json` (v4+)
2. Updated `ai_docs/Plans/meta-workflow.md`
3. Commit and push to branch
