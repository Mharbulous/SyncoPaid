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

## Output

Document the Phase 5 step breakdown in this file, then proceed to handover 048.
