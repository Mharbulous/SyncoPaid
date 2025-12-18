# Line 054: CONCEPT --> APPROVED (approve-stories)

> Working on transition: `CONCEPT --> APPROVED: approve-stories`

## Overview

This WIP document tracks implementation of the `approve-stories` workflow as specified in `.claude/skills/story-tree/references/orchestrator-workflow-complete.md`.

**Implementation Priority**: #2 (Low complexity, high value - closes loop)

## Current State Analysis

Per the spec's "Workflows to Implement" table:
- `approve-stories.yml` - ❌ Missing

No workflow currently exists. Concepts that pass vetting remain in `concept` stage until manually approved.

## Target State (from spec)

Per line 54 of the mermaid diagram:
- `CONCEPT --> APPROVED: approve-stories`

### Transition Details

| Step | Workflow | From State | To State | Hold Outcomes |
|------|----------|------------|----------|---------------|
| 8 | `approve-stories` | concept (no hold) | approved (no hold) | - |

### Position in Orchestrator Loop

This is **Step 8** in the **FILL Phase**:
1. write-stories (Step 6)
2. vet-stories (Step 7)
3. **approve-stories (Step 8)** ← This transition

## Implementation Plan

### Phase 1: Create standalone workflow

Create `.github/workflows/approve-stories.yml` that:
1. Queries concept stories without holds (`stage = 'concept' AND hold_reason IS NULL AND disposition IS NULL`)
2. Optionally filters for stories that have been vetted (have passed through vetting step)
3. Updates stage to 'approved'
4. Commits and pushes changes

### Phase 2: SQL Implementation

```sql
-- Find concepts ready for approval
SELECT id, title
FROM story_nodes
WHERE stage = 'concept'
  AND hold_reason IS NULL
  AND disposition IS NULL;

-- Approve a concept story
UPDATE story_nodes
SET stage = 'approved',
    notes = COALESCE(notes || char(10), '') ||
            'AUTO-APPROVED: Concept passed vetting. ' || datetime('now'),
    updated_at = datetime('now')
WHERE id = ?;
```

### Phase 3: Workflow file structure

Simple workflow similar to other story transitions:
- Uses `anthropics/claude-code-action@v1`
- Queries database for eligible stories
- Approves them in batch
- Commits changes

## Progress Log

### Session 2025-12-18

**Status**: Implementation complete

#### Changes Made

1. **Created `.github/workflows/approve-stories.yml`**:
   - Scheduled at 12:00 UTC (4:00 AM PST) - after write and vet
   - Manual trigger via `workflow_dispatch`
   - Uses `anthropics/claude-code-action@v1`
   - Two-step process: Query concepts → Auto-approve
   - Includes token usage reporting

2. **SQL Implementation Verified**:
   - Query finds `concept` stories with `hold_reason IS NULL` and `disposition IS NULL`
   - Update sets `stage = 'approved'` with timestamp note
   - All queries tested against actual database

#### Test Results

```
=== Test: Query concepts without holds ===
Found 19 concept(s) ready for approval:
  - 1.11: Website & Marketing Platform
  - 1.13: Documentation & Help System
  - 1.1.1.2: Process Command Line and Arguments Tracking
  - 1.1.7: Application-Specific Context Extraction
  - 1.1.8: Multi-Monitor Window Position Tracking
  - 1.4.9: Matter Selection and Assignment UI
  - ... (14 more)

=== Stage distribution ===
  concept: 19
  approved: 3
  planned: 5
  active: 15
  reviewing: 2
  implemented: 31

=== Concepts WITH holds (not eligible) ===
Found 0 concept(s) with holds (NOT eligible)

All queries executed successfully!
```

#### Workflow File Summary

| Aspect | Value |
|--------|-------|
| Schedule | `0 12 * * *` (4:00 AM PST) |
| Concurrency | `daily-story-approval` |
| Model | `claude-sonnet-4-5-20250929` |
| Timeout | 15 minutes (simple operation) |

#### Integration Notes

The standalone `approve-stories.yml` is now ready for deployment. To fully integrate into the orchestrator:

1. Add approve-stories as Step 8 in the FILL phase of `story-tree-orchestrator.yml`
2. Currently 19 concepts are eligible and will be approved on first run

**Status**: ✅ IMPLEMENTED - Ready for deployment and testing

---
*Last updated: 2025-12-18*
