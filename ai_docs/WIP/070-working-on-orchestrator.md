# Line 070: IMPLEMENTED --> READY (ready-check)

> Working on transition: `IMPLEMENTED --> READY: ready-check<br/>integration OK`

## Overview

This WIP document tracks implementation of the `ready-check` workflow as specified in `.claude/skills/story-tree/references/orchestrator-workflow-complete.md`.

**Implementation Priority**: #5 (Low complexity, integration verification)

## Current State Analysis

Per the spec's "Workflows to Implement" table:
- `ready-check.yml` - ❌ Missing

No workflow currently exists. Stories that reach `implemented` stage remain there until manually advanced to `ready`.

## Target State (from spec)

Per line 70 of the mermaid diagram:
- `IMPLEMENTED --> READY: ready-check<br/>integration OK`

### Transition Details

| Step | Workflow | From State | To State | Hold Outcomes |
|------|----------|------------|----------|---------------|
| N/A | `ready-check` | implemented (no hold) | ready (no hold) | → (broken) if integration fails |

### Position in Orchestrator Loop

This transition comes AFTER the DRAIN phase verifications:
1. verify-stories (Step 1) - verifying → implemented
2. review-stories (Step 2) - reviewing → verifying
3. execute-stories (Step 3) - active → reviewing/verifying
4. activate-stories (Step 4) - planned → active
5. plan-stories (Step 5) - approved → planned
6. **ready-check** ← This transition (after verify-stories)

## Context: What is "Integration OK"?

According to the spec's state diagram:
- `implemented` means verification passed (tests pass)
- `ready` means integration verified (ready for release)
- `released` is the final state (via manual deploy.yml trigger)

The ready-check workflow should verify:
1. Story's implementation is complete and tested
2. No conflicting changes from other stories
3. Integration tests pass (if applicable)
4. Story is ready for production release

## Implementation Plan

### Phase 1: SQL Queries

```sql
-- Find implemented stories without holds
SELECT id, title, description, notes, project_path
FROM story_nodes
WHERE stage = 'implemented'
  AND hold_reason IS NULL
  AND disposition IS NULL;

-- Transition to ready (integration OK)
UPDATE story_nodes
SET stage = 'ready',
    notes = COALESCE(notes || char(10), '') ||
            'READY: Integration check passed. ' || datetime('now'),
    updated_at = datetime('now')
WHERE id = ?;

-- Mark as broken (integration failed)
UPDATE story_nodes
SET hold_reason = 'broken',
    notes = COALESCE(notes || char(10), '') ||
            'INTEGRATION FAILED: <reason>. ' || datetime('now'),
    updated_at = datetime('now')
WHERE id = ?;
```

### Phase 2: Integration Check Logic

The integration check should:
1. Read the story's notes to understand what was implemented
2. Check if any tests exist that should be run
3. Verify no merge conflicts with other stories
4. Make a pass/fail decision

For this project (SyncoPaid), integration checks might include:
- Running `python -m syncopaid` to verify the app starts
- Running any module tests that relate to the implemented story
- Checking for import errors or syntax issues

### Phase 3: Workflow Structure

Similar to other story workflows:
- Schedule: After verify-stories
- Uses `anthropics/claude-code-action@v1`
- Queries database for eligible stories
- Performs integration verification
- Updates status and commits

## Progress Log

### Session 2025-12-18

**Status**: Implementation Complete

#### Analysis Complete

1. **Database state verified**: 31 implemented stories exist (30 without holds, 1 with pending hold)
2. **No stories in ready/released stages**: Pipeline has never advanced past implemented
3. **Transition flow understood**: verify-stories → implemented → ready-check → ready
4. **Schema verified**: `ready` is a valid stage value in the CHECK constraint

#### Implementation Details

1. **Created `.github/workflows/ready-check.yml`**:
   - Scheduled at 11:30 UTC (3:30 AM PST) - after verify-stories at 11:00 UTC
   - Manual trigger via `workflow_dispatch`
   - Uses `anthropics/claude-code-action@v1`
   - Multi-step process: Query stories → Integration check → Update status
   - Includes token usage reporting

2. **SQL Implementation Verified**:
   - Query finds `implemented` stories with `hold_reason IS NULL` and `disposition IS NULL`
   - PASS: Sets `stage = 'ready'` with timestamp note
   - FAIL: Sets `hold_reason = 'broken'` with reason note
   - All queries tested against actual database

#### Test Results

```
=== Test: Query implemented stories without holds ===
Found 30 story(ies) ready for integration check:
  - 1.1.3: Event Merging...
  - 1.1.4: Activity State Management...
  - 1.1.5: Start/End Time Recording...
  - 1.2.1: Periodic Screenshot Capture...
  - 1.2.2: Perceptual Hash Deduplication...
  ... and 25 more

=== Test: Query implemented stories WITH holds ===
Found 1 implemented story(ies) with holds (NOT eligible):
  - 1.4.6: Activity Timeline View... (hold: pending)

=== Stage distribution ===
  implemented: 31
  concept: 19
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
| Schedule | `30 11 * * *` (3:30 AM PST) |
| Concurrency | `daily-ready-check` |
| Model | `claude-sonnet-4-5-20250929` |
| Timeout | 20 minutes (lightweight integration checks) |

#### Integration Checks Performed

The workflow performs these lightweight checks:
1. **Import check**: `python3 -c "import syncopaid"` - catches import errors
2. **Syntax check**: `python3 -m py_compile src/syncopaid/*.py` - catches syntax errors
3. **Structural check**: Verifies project_path exists if specified

#### Integration Notes

The standalone `ready-check.yml` is now ready for deployment. To fully integrate into the orchestrator:

1. Add ready-check after verify-stories in the DRAIN phase of `story-tree-orchestrator.yml`
2. Currently 30 implemented stories are eligible for integration check
3. This is the final gate before stories can be marked as `ready` for release

**Status**: ✅ IMPLEMENTED - Ready for deployment and testing

---
*Last updated: 2025-12-18*
