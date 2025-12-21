# 047: Design Multi-Call Execution Phases

## Goal
Break step 5.1 "Execute plan with Claude" into multiple `claude-code-action` calls, each with fresh context. Define the logical boundaries.

## Context

The workflow `.github/workflows/execute-stories.yml` was refactored to have 17 granular steps across 7 phases. All phases except Phase 5 use bash/Python (no AI). Phase 5 currently has ONE Claude call that does everything.

Problem: Even with focused prompts, complex plans can overwhelm context. Breaking into multiple calls gives:
- Fresh context per phase
- Better failure isolation
- Progressive skill loading via references

## Current Phase 5 (single call)

```yaml
- name: "5.1 Execute plan with Claude"
  prompt: |
    Execute the implementation plan: ${{ steps.select-plan.outputs.path }}
    ...
```

## Proposed Phase 5 Breakdown

Analyze what the `story-execution` skill currently does in Step 2-6:

| Current Skill Step | Proposed Workflow Step | Claude Call? |
|--------------------|------------------------|--------------|
| Step 2: Critical Review | 5.1 Review plan critically | Yes |
| Step 3: Execute Batch (×N) | 5.2-5.N Execute task batch | Yes (per batch) |
| Step 4: Report | 5.N+1 Report completion | Maybe bash |

**Key decision**: How many tasks per Claude call?
- Option A: 1 call per task (fine-grained, expensive)
- Option B: 1 call per batch of 3 tasks (current skill default)
- Option C: 1 call for review + 1 call for all execution

Recommend **Option B** - matches existing TDD batch pattern.

## Shared State File

`.claude/skills/story-execution/temp-CI-notes.json`

Schema:
```json
{
  "plan_file": "012E_cmdline-database-schema.md",
  "story_id": "1.1.2",
  "review_outcome": "proceed|pause|blocked",
  "review_notes": "...",
  "tasks": [
    {"id": 1, "status": "completed|failed|pending", "notes": "..."}
  ],
  "current_batch": 1,
  "commits": ["abc123", "def456"]
}
```

## Key Files

- `.github/workflows/execute-stories.yml` - workflow to modify
- `.claude/skills/story-execution/SKILL.md` - skill to decompose (800 lines)
- Branch: `claude/debug-ci-workflow-X60Of` - current work

## Red Herrings

- `.claude/commands/` - slash commands, not skills
- `story-planning` skill - creates plans, doesn't execute them

## Tasks

1. Decide task grouping strategy (recommend batch of 3)
2. Define exact workflow steps for Phase 5 (5.1, 5.2, 5.3...)
3. Define temp-CI-notes.json schema
4. Map each new step to skill reference files (next handover)

## Decisions

### Task Grouping Strategy: Option B (Batch of 3)

Selected **Option B** - 1 call per batch of 3 tasks:
- Matches existing TDD batch pattern in the skill
- Provides fresh context between batches
- Balances cost vs. failure isolation
- Most plans have 6-12 tasks, fitting 2-4 batches

### Phase 5 Step Breakdown

| Step | Name | Claude Call | Purpose |
|------|------|-------------|---------|
| 5.1 | Critical Review | Yes | Review plan, classify issues (blocking/deferrable) |
| 5.1a | Read Review Output | Bash | Extract review outcome from temp-CI-notes.json |
| 5.2 | Execute Batch 1 | Yes (conditional) | TDD for tasks 1-3 |
| 5.2a | Read Batch 1 Output | Bash | Extract batch status, commit hashes |
| 5.3 | Execute Batch 2 | Yes (conditional) | TDD for tasks 4-6 |
| 5.3a | Read Batch 2 Output | Bash | Extract batch status |
| 5.4 | Execute Batch 3 | Yes (conditional) | TDD for tasks 7-9 |
| 5.4a | Read Batch 3 Output | Bash | Extract batch status |
| 5.5 | Execute Batch 4 | Yes (conditional) | TDD for tasks 10-12 |
| 5.5a | Read Batch 4 Output | Bash | Extract final status |

**Conditionals:**
- 5.2: `review_outcome == 'proceed' || review_outcome == 'proceed_with_review'`
- 5.3-5.5: `previous_batch_status == 'completed' && tasks_remaining > 0`

### temp-CI-notes.json Schema

```json
{
  "version": 1,
  "plan_file": "012E_cmdline-database-schema.md",
  "story_id": "1.1.2",

  "review": {
    "outcome": "proceed|pause|proceed_with_review",
    "blocking_issues": [],
    "deferrable_issues": [
      {"description": "...", "decision": "...", "rationale": "..."}
    ],
    "notes": "..."
  },

  "tasks": [
    {"id": 1, "name": "...", "status": "pending|in_progress|completed|failed", "notes": ""},
    {"id": 2, "name": "...", "status": "pending", "notes": ""},
    {"id": 3, "name": "...", "status": "pending", "notes": ""}
  ],

  "batches": [
    {"batch": 1, "task_range": [1, 3], "status": "pending|in_progress|completed|failed", "commits": []}
  ],

  "current_batch": 0,
  "total_tasks": 8,

  "final_status": "not_started|in_progress|completed|failed|paused"
}
```

**Key fields:**
- `review.outcome`: Controls whether execution proceeds
- `tasks[].status`: Individual task tracking
- `batches[].status`: Per-batch success/failure for workflow conditionals
- `batches[].commits`: Commit hashes for linking to story
- `current_batch`: 0-indexed pointer for state resumption
- `final_status`: Overall execution outcome

### Workflow Step → Skill Reference Mapping

| Workflow Step | Reference File | Content |
|---------------|----------------|---------|
| 5.1 Critical Review | `references/critical-review.md` | Step 2 logic, issue classification |
| 5.2-5.5 Execute Batch | `references/tdd-execution.md` | Step 3 TDD cycle, verification |
| (all) | `references/database-updates.md` | SQL for stage updates, commit linking |
| (all) | `references/ci-mode-outcomes.md` | Outcome handling, final status |

### Prompt Pattern for Each Call

```yaml
# 5.1 Critical Review
prompt: |
  Use story-execution skill in CI mode.
  Phase: REVIEW
  Plan: ${{ steps.select-plan.outputs.path }}
  Story ID: ${{ steps.extract-story.outputs.story_id }}

  Read/write state: .claude/skills/story-execution/temp-CI-notes.json

  Instructions:
  1. Initialize temp-CI-notes.json with plan info
  2. Read and review plan critically
  3. Classify any issues as blocking or deferrable
  4. Write review outcome to temp-CI-notes.json
  5. If blocking issues: set outcome to "pause"
  6. If deferrable issues: set outcome to "proceed_with_review"
  7. If no issues: set outcome to "proceed"

# 5.2 Execute Batch 1
prompt: |
  Use story-execution skill in CI mode.
  Phase: EXECUTE_BATCH
  Batch: 1
  Task Range: 1-3
  Plan: ${{ steps.select-plan.outputs.path }}

  Read/write state: .claude/skills/story-execution/temp-CI-notes.json

  Instructions:
  1. Read temp-CI-notes.json to get task list
  2. Execute tasks 1-3 using TDD cycle
  3. For each task: RED (failing test) → GREEN (implementation) → COMMIT
  4. Update task status and commits in temp-CI-notes.json
  5. Set batch 1 status to "completed" or "failed"
```

## Output

Phase 5 step breakdown documented above. Proceed to handover 048 to create skill reference structure.
