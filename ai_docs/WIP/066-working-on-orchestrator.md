# Line 066: REVIEWING --> VERIFYING (review-stories)

> Working on transition: `REVIEWING --> VERIFYING: review-stories<br/>review passed`

## Overview

This WIP document tracks implementation of the `review-stories` workflow as specified in `.claude/skills/story-tree/references/orchestrator-workflow-complete.md`.

**Implementation Priority**: #3 (Medium complexity, enables reviewing→verifying)

## Current State Analysis

Per the spec's "Workflows to Implement" table:
- `review-stories.yml` - ❌ Missing

No workflow currently exists. Stories that enter `reviewing` stage (from execute-stories with deferrable issues) remain there until manually advanced.

### Current Database State

```
=== Stories in reviewing stage ===
  1.3.6: AI Learning Database for Categorization... (hold: pending)
  1.5.6: Configuration Validation & Error Handlin... (hold: pending)
Total: 2

Both reviewing stories have hold_reason='pending' (human review required).
Currently no reviewing stories without holds to process.
```

## Target State (from spec)

Per line 66 of the mermaid diagram:
- `REVIEWING --> VERIFYING: review-stories<br/>review passed`

### Transition Details

| Step | Workflow | From State | To State | Hold Outcomes |
|------|----------|------------|----------|---------------|
| 2 | `review-stories` | reviewing (no hold) | verifying (no hold) | → (broken) if issues found |

### Position in Orchestrator Loop

This is **Step 2** in the **DRAIN Phase**:
1. verify-stories (Step 1) - verifying → implemented
2. **review-stories (Step 2)** ← This transition
3. execute-stories (Step 3) - active → reviewing/verifying
4. activate-stories (Step 4) - planned → active
5. plan-stories (Step 5) - approved → planned

## Context: How Stories Enter `reviewing`

Stories enter `reviewing` stage from `execute-stories.yml` when:
- Implementation was completed but had "deferrable issues"
- These are non-blocking issues that need code review
- Common scenarios:
  - Minor code style issues
  - Documentation gaps
  - Edge case handling that should be reviewed
  - Test coverage could be improved

## Implementation Plan

### Phase 1: SQL Queries

```sql
-- Find reviewing stories without holds
SELECT id, title, description, notes, project_path
FROM story_nodes
WHERE stage = 'reviewing'
  AND hold_reason IS NULL
  AND disposition IS NULL;

-- Transition to verifying (review passed)
UPDATE story_nodes
SET stage = 'verifying',
    notes = COALESCE(notes || char(10), '') ||
            'REVIEW PASSED: Code review completed successfully. ' || datetime('now'),
    updated_at = datetime('now')
WHERE id = ?;

-- Mark as broken (review failed)
UPDATE story_nodes
SET hold_reason = 'broken',
    notes = COALESCE(notes || char(10), '') ||
            'REVIEW FAILED: <reason>. ' || datetime('now'),
    updated_at = datetime('now')
WHERE id = ?;
```

### Phase 2: Review Logic

The code review check should:
1. Read the story's notes for deferred issues from execution
2. Check if the related code/tests address those issues
3. Run any relevant tests to verify
4. Make a pass/fail decision

### Phase 3: Workflow Structure

Similar to other story workflows:
- Schedule: After execute-stories (4:00 AM PST / 12:00 UTC)
- Uses `anthropics/claude-code-action@v1`
- Queries database for eligible stories
- Performs code review analysis
- Updates status and commits

## Progress Log

### Session 2025-12-18

**Status**: Implementation Complete

#### Analysis Complete

1. **Database state verified**: 2 reviewing stories exist, both with `pending` holds
2. **Transition flow understood**: execute-stories → reviewing → review-stories → verifying
3. **hold_reason constraint noted**: Schema allows: pending, paused, blocked, broken, refine
4. **story-verification skill exists**: Handles verifying → implemented (separate workflow)

#### Implementation Details

1. **Created `.github/workflows/review-stories.yml`**:
   - Scheduled at 12:30 UTC (4:30 AM PST) - after approve-stories
   - Manual trigger via `workflow_dispatch`
   - Uses `anthropics/claude-code-action@v1`
   - Three-step process: Query stories → Review code → Update status
   - Includes token usage reporting

2. **SQL Implementation Verified**:
   - Query finds `reviewing` stories with `hold_reason IS NULL` and `disposition IS NULL`
   - PASS: Sets `stage = 'verifying'` with timestamp note
   - FAIL: Sets `hold_reason = 'broken'` with reason note
   - All queries tested against actual database

#### Test Results

```
=== Test: Query reviewing stories without holds ===
Found 0 story(ies) ready for review:

=== Test: Query reviewing stories WITH holds ===
Found 2 reviewing story(ies) with holds (NOT eligible):
  - 1.3.6: AI Learning Database for Categorization ... (hold: pending)
  - 1.5.6: Configuration Validation & Error Handlin... (hold: pending)

=== Stage distribution ===
  implemented: 31
  concept: 24
  active: 15
  planned: 5
  approved: 3
  reviewing: 2

=== Test: UPDATE query syntax (dry run) ===
  PASS query: Valid (would affect 0 rows for nonexistent-id)
  FAIL query: Valid (would affect 0 rows for nonexistent-id)

All queries validated successfully!
```

#### Workflow File Summary

| Aspect | Value |
|--------|-------|
| Schedule | `30 12 * * *` (4:30 AM PST) |
| Concurrency | `daily-story-review` |
| Model | `claude-sonnet-4-5-20250929` |
| Timeout | 30 minutes (review takes longer) |

#### Integration Notes

The standalone `review-stories.yml` is now ready for deployment. To fully integrate into the orchestrator:

1. Add review-stories as Step 2 in the DRAIN phase of `story-tree-orchestrator.yml`
2. Currently 0 reviewing stories without holds are eligible
3. The 2 reviewing stories with `pending` holds require human intervention first

**Status**: ✅ IMPLEMENTED - Ready for deployment and testing

---
*Last updated: 2025-12-18*
