# Line 070: IMPLEMENTED --> READY (ready-check)

> Working on transition: `IMPLEMENTED --> READY: ready-check<br/>integration OK`

## Overview

This WIP document tracks implementation of the `ready-check` workflow as specified in `.claude/skills/story-tree/references/orchestrator-workflow-complete.md`.

**Implementation Priority**: #5 (Low complexity, integration verification)

## Current State Analysis

Per the spec's "Workflows to Implement" table:
- `ready-check.yml` - ❌ Missing

No workflow currently exists. Stories that reach `implemented` stage remain there until manually advanced.

### Transition Context

Looking at the workflow diagram:
- Line 68: `VERIFYING --> IMPLEMENTED: verify-stories<br/>tests pass`
- **Line 70**: `IMPLEMENTED --> READY: ready-check<br/>integration OK` ← This transition
- Line 72: `READY --> RELEASED: deploy.yml<br/>(manual trigger)`

## Target State (from spec)

Per line 70 of the mermaid diagram:
- `IMPLEMENTED --> READY: ready-check<br/>integration OK`

### Transition Details

| Step | Workflow | From State | To State | Hold Outcomes |
|------|----------|------------|----------|---------------|
| - | `ready-check` | implemented (no hold) | ready (no hold) | - (simple transition) |

### Position in Orchestrator Loop

This transition is NOT shown in the main DRAIN or FILL phases in the spec diagram.
It appears to be a separate verification step that happens after the main loop.

Looking at the spec, this transition:
1. Verifies integration is OK (all tests pass together)
2. Advances story to `ready` status
3. `ready` stories can then be manually deployed via `deploy.yml`

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
            'READY: Integration verification passed. ' || datetime('now'),
    updated_at = datetime('now')
WHERE id = ?;
```

### Phase 2: Integration Check Logic

The ready-check should verify:
1. Story implementation is complete (already in `implemented` stage)
2. All related tests pass together (integration test)
3. No conflicts with other implemented stories
4. Build succeeds with all changes included

### Phase 3: Workflow Structure

Similar to other story workflows:
- Schedule: After verify-stories completes
- Uses `anthropics/claude-code-action@v1`
- Queries database for eligible stories
- Performs integration verification
- Updates status and commits

## Progress Log

### Session 2025-12-18

**Status**: Implementation Complete

#### Initial Analysis

1. **Verified transition is NOT yet implemented**: No `ready-check.yml` workflow exists
2. **Checked existing WIP files**: No 070-working-on-orchestrator.md exists
3. **Position in lifecycle**: Final automated step before manual deploy

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
   - PENDING: Sets `hold_reason = 'pending'` for human review
   - All queries tested against mock database

#### Test Results

```
=== Test: Query implemented stories without holds ===
Found 1 story(ies) ready for integration check:
  - 1.1: Test Story 1
  Query: VALID

=== Test: Query implemented stories WITH holds ===
Found 2 implemented story(ies) with holds (NOT eligible):
  - 1.2: Test Story 2 (hold: pending)
  - 1.4: Test Story 4 (hold: None)
  Query: VALID

=== Test: UPDATE query syntax (dry run) ===
  PASS query: Valid (would affect 0 rows for nonexistent-id)
  FAIL query: Valid (would affect 0 rows for nonexistent-id)
  PENDING query: Valid (would affect 0 rows for nonexistent-id)

All queries validated successfully!
```

#### Workflow File Summary

| Aspect | Value |
|--------|-------|
| Schedule | `30 11 * * *` (3:30 AM PST) |
| Concurrency | `daily-ready-check` |
| Model | `claude-sonnet-4-5-20250929` |
| Timeout | 30 minutes (integration checks are lightweight) |

#### Integration Check Logic

The workflow performs:
1. **Build verification** - Python syntax check via `py_compile`
2. **Test suite** - Run pytest if available
3. **Conflict detection** - Check git status for uncommitted changes

Decision outcomes:
- **PASS** → story advances to `ready` stage
- **FAIL** → story gets `hold_reason = 'broken'`
- **PENDING** → story gets `hold_reason = 'pending'` for human review

#### Integration Notes

The standalone `ready-check.yml` is now ready for deployment. To fully integrate into the orchestrator:

1. This is a separate step that runs after the main DRAIN phase
2. Stories must first reach `implemented` via verify-stories
3. `ready` stories can then be manually deployed via existing `deploy.yml`

**Status**: ✅ IMPLEMENTED - Ready for deployment and testing

---
*Last updated: 2025-12-18*
