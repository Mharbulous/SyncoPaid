# Story Tree Orchestrator - Development Workflow Documentation

> Single source of truth for the GitHub Actions meta-workflow that automates story backlog management.

## Overview

The **Story Tree Orchestrator** is a GitHub Actions workflow that autonomously maintains a hierarchical story backlog. It runs daily at 2:00 AM PST, looping through plan→write cycles until the pipeline is idle.

**Workflow File:** `.github/workflows/story-tree-orchestrator.yml`

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    story-tree-orchestrator                      │
│                  (runs daily at 2:00 AM PST)                    │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │        GATE          │
                    │ Check if automation  │
                    │    is enabled        │
                    └──────────┬───────────┘
                               │
              ┌────────────────┴────────────────┐
              │                                 │
         [DISABLED]                       [ENABLED]
              │                                 │
              ▼                                 ▼
        ┌──────────┐              ┌─────────────────────────────┐
        │   EXIT   │              │      drain-pipeline         │
        │ (skip)   │              │   (loop until idle)         │
        └──────────┘              └─────────────┬───────────────┘
                                                │
                                  ┌─────────────┴─────────────┐
                                  │                           │
                                  │  ┌──────────────────────┐ │
                                  │  │    plan-stories      │ │
                                  │  │  (drain approved)    │ │
                                  │  └──────────┬───────────┘ │
                                  │             │             │
                                  │             ▼             │
                                  │  ┌──────────────────────┐ │
                                  │  │   write-stories      │ │
                                  │  │  (fill capacity)     │ │
                                  │  └──────────┬───────────┘ │
                                  │             │             │
                                  │    ┌────────┴────────┐    │
                                  │    │ Both idle?      │    │
                                  │    │ NO_APPROVED &&  │    │
                                  │    │ NO_CAPACITY     │    │
                                  │    └────────┬────────┘    │
                                  │             │             │
                                  │      ┌──────┴──────┐      │
                                  │    [NO]          [YES]    │
                                  │      │             │      │
                                  │      │ (loop)      │      │
                                  │      └─────────────│──────│
                                  │                    │      │
                                  └────────────────────│──────┘
                                                       │
                                                       ▼
                                            ┌───────────────────────┐
                                            │       summary         │
                                            │   Report loop results │
                                            │   GITHUB_STEP_SUMMARY │
                                            └───────────────────────┘
```

## Key Design Decisions

### 1. Drain Before Fill (Pipeline Order)

**Principle:** Clear downstream work before creating upstream work.

```
Plan first → Write second
(drain)      (fill)
```

This prevents "concept glut" where approved stories pile up waiting for planning while new concepts keep being added.

### 2. Loop Until Idle

The orchestrator loops internally until **both** conditions are true:
- `NO_APPROVED`: No approved stories waiting for planning
- `NO_CAPACITY`: All tree nodes at capacity

| Exit Condition | Meaning |
|----------------|---------|
| `IDLE` | Both NO_APPROVED and NO_CAPACITY in same cycle |
| `MAX_CYCLES` | Safety limit reached (default: 10) |
| `ERROR` | Script or Claude failure |

### 3. Master Switch

A single repository variable controls the entire automation:

```
Variable: STORY_AUTOMATION_ENABLED
Values: "true" | "false"
Default: "true"
Location: Settings > Secrets and variables > Actions > Variables
```

### 4. Synthesize-Goals is Separate

Goal synthesis only changes when the user acts (approves/rejects stories). Since there's no user input during CI, it runs as a separate daily workflow (`synthesize-goals-non-goals.yml`), not part of the loop.

## Story Status Lifecycle

Stories progress through defined states:

| Status | Meaning |
|--------|---------|
| `concept` | Initial idea awaiting human review |
| `approved` | Human has validated the idea |
| `rejected` | Human decided against pursuing it |
| `planned` | Implementation plan exists |
| `queued` | Ready to work on, dependencies satisfied |
| `active` | Currently being developed |
| `in-progress` | Partially complete |
| `bugged` | Encountering issues requiring fixes |
| `implemented` | Development complete |
| `ready` | Fully tested and production-ready |
| `deprecated` | No longer relevant |
| `infeasible` | Cannot be built as conceived |

**Orchestrator Flow:**
```
concept → [user approves] → approved → [plan-stories] → planned → [user implements] → implemented
```

## Jobs Specification

### Job 1: gate

**Purpose:** Check if automation is enabled

```yaml
gate:
  runs-on: ubuntu-latest
  outputs:
    enabled: ${{ steps.check.outputs.enabled }}
  steps:
    - id: check
      run: |
        if [ "${{ vars.STORY_AUTOMATION_ENABLED }}" = "false" ]; then
          echo "enabled=false" >> $GITHUB_OUTPUT
        else
          echo "enabled=true" >> $GITHUB_OUTPUT
        fi
```

### Job 2: drain-pipeline

**Purpose:** Loop plan→write until pipeline is idle

**Loop Logic:**
```bash
while [ $cycle -lt $MAX_CYCLES ]; do
    # Step 1: Plan stories (drain approved backlog)
    approved=$(sqlite3 .claude/data/story-tree.db "SELECT COUNT(*) FROM story_nodes WHERE status='approved'")
    if [ "$approved" -gt 0 ]; then
        # invoke Claude Code with story-planning-ci skill
        git add -A && git commit -m "ci: plan story" && git push
        plan_result="SUCCESS"
    else
        plan_result="NO_APPROVED"
    fi

    # Step 2: Write stories (fill capacity)
    if ! python .claude/scripts/story_workflow.py --ci 2>&1 | grep -q "NO_CAPACITY"; then
        # invoke Claude Code to generate story
        python .claude/scripts/insert_story.py
        git add -A && git commit -m "ci: add story" && git push
        write_result="SUCCESS"
    else
        write_result="NO_CAPACITY"
    fi

    # Exit if idle
    [ "$plan_result" = "NO_APPROVED" ] && [ "$write_result" = "NO_CAPACITY" ] && break
    cycle=$((cycle + 1))
done
```

**Outputs:**
- `cycles_completed`: Number of iterations run
- `plans_created`: Total plans created across all cycles
- `stories_created`: Total stories created across all cycles
- `exit_reason`: `IDLE` | `MAX_CYCLES` | `ERROR`
- `progress_file`: Path to detailed progress report

### Job 3: summary

**Purpose:** Generate pipeline summary to `GITHUB_STEP_SUMMARY`

Shows cycles completed, stories created, plans created, and exit reason.

## Implementation Files

| File | Purpose |
|------|---------|
| `.github/workflows/story-tree-orchestrator.yml` | Main orchestrator workflow |
| `.github/workflows/write-stories.yml` | Standalone - kept for manual runs |
| `.github/workflows/plan-stories.yml` | Standalone - kept for manual runs |
| `.github/workflows/synthesize-goals-non-goals.yml` | Separate daily workflow |
| `.claude/scripts/story_workflow.py` | Returns JSON context or `NO_CAPACITY` |
| `.claude/scripts/insert_story.py` | Inserts stories into DB |
| `.claude/data/story-tree.db` | SQLite database with story tree |

## Progress Tracking

Each run creates a progress file at:
```
ai_docs/Progress/YYYY-MM-DD-GitHub-Actions-Results.md
```

**Contents:**
- Run metadata (date, max_cycles, workflow run link)
- Step-by-step table with: Cycle, Step, Story ID, Action, Files Changed, Input/Output Tokens, Cost USD, Commit Time
- Summary section with totals

## Usage

### Enable/Disable Automation

**To disable:**
1. Go to repository Settings
2. Navigate to Secrets and variables > Actions > Variables
3. Set `STORY_AUTOMATION_ENABLED` to `false`

**To re-enable:**
1. Set `STORY_AUTOMATION_ENABLED` to `true`

### Manual Trigger

```yaml
workflow_dispatch:
  inputs:
    max_cycles:
      type: number
      default: 10
      description: Maximum loop iterations (safety limit)
```

Use `max_cycles=1` for testing, higher values for actual backlog processing.

## Test Results (2025-12-16)

| Metric | Value |
|--------|-------|
| Duration | 3m 42s |
| Cycles Completed | 1 |
| Plans Created | 1 |
| Stories Created | 1 |
| Exit Reason | MAX_CYCLES |

**Validated:**
- Claude CLI with `CLAUDE_CODE_OAUTH_TOKEN` ✅
- `--dangerously-skip-permissions` flag ✅
- `--allowedTools` and `--model` flags ✅
- Skills invocation from CLI prompt ✅
- Git pull/push in loop (no conflicts) ✅
- Loop exit on conditions ✅

## Design Evolution

| Version | Changes | Flaws |
|---------|---------|-------|
| v1 | `workflow_call` chaining | Doesn't give true sequential execution |
| v2 | Added PAUSED state, state files | Over-engineered, git noise |
| v3 | Two states, no state files | Wrong order (write→plan), single cycle |
| **v4** | Plan first, loop until idle, shell loop | Current implementation |

## Known Limitations

- Each cycle takes ~2 minutes (Claude latency)
- `max_cycles=10` could take 20+ minutes total
- Net drain rate: ~0 (each cycle plans 1 and writes 1)
- To actually drain backlog faster, increase `max_cycles` or run more frequently

## Related Documentation

| Document | Purpose |
|----------|---------|
| `ai_docs/story-tree-skill-overview.md` | Story tree skill concepts |
| `ai_docs/story-tree-workflow-diagrams.md` | Visual workflow diagrams |
| `ai_docs/Plans/meta-workflow.md` | Original v4 design spec |
| `ai_docs/Handovers/026_meta-workflow-design.md` | Design requirements |
| `ai_docs/Handovers/027_implement-story-tree-orchestrator.md` | Implementation handover |
| `ai_docs/Handovers/029_orchestrator-analysis-report.md` | Test analysis |
