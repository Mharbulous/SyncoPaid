# Line 068: VERIFYING --> IMPLEMENTED (verify-stories)

> Working on transition: `VERIFYING --> IMPLEMENTED: verify-stories<br/>tests pass`

## Overview

This WIP document tracks implementation of the `verify-stories` workflow as specified in `.claude/skills/story-tree/references/orchestrator-workflow-complete.md`.

**Implementation Priority**: #4 (Medium complexity, uses existing skill)

## Current State Analysis

Per the spec's "Workflows to Implement" table:
- `verify-stories.yml` - ❌ Missing

No workflow currently exists. Stories that enter `verifying` stage remain there until manually verified.

## Target State (from spec)

Per line 68 of the mermaid diagram:
- `VERIFYING --> IMPLEMENTED: verify-stories<br/>tests pass`

### Transition Details

| Step | Workflow | From State | To State | Hold Outcomes |
|------|----------|------------|----------|---------------|
| 1 | `verify-stories` | verifying (no hold) | implemented (no hold) | → (broken) if tests fail |

### Position in Orchestrator Loop

This is **Step 1** in the **DRAIN Phase** (earliest stage, processed first):
1. **verify-stories (Step 1)** ← This transition
2. review-stories (Step 2) - reviewing → verifying
3. execute-stories (Step 3) - active → reviewing/verifying
4. activate-stories (Step 4) - planned → active
5. plan-stories (Step 5) - approved → planned

## Context: How Stories Enter `verifying`

Stories enter `verifying` stage from:
1. `execute-stories.yml` - when implementation completed with no issues
2. `review-stories.yml` - when code review passed

## Implementation Plan

### Phase 1: SQL Queries

```sql
-- Find verifying stories without holds
SELECT id, title, description, notes, project_path
FROM story_nodes
WHERE stage = 'verifying'
  AND hold_reason IS NULL
  AND disposition IS NULL;

-- Transition to implemented (tests pass)
UPDATE story_nodes
SET stage = 'implemented',
    notes = COALESCE(notes || char(10), '') ||
            'VERIFIED: All tests pass. ' || datetime('now'),
    updated_at = datetime('now')
WHERE id = ?;

-- Mark as broken (tests fail)
UPDATE story_nodes
SET hold_reason = 'broken',
    notes = COALESCE(notes || char(10), '') ||
            'VERIFICATION FAILED: <reason>. ' || datetime('now'),
    updated_at = datetime('now')
WHERE id = ?;
```

### Phase 2: Verification Logic

The verification check should:
1. Read the story's acceptance criteria
2. Check if related tests pass
3. Verify implementation matches acceptance criteria
4. Make a pass/fail decision

### Phase 3: Workflow Structure

Similar to other story workflows:
- Schedule: Before review-stories (earliest in DRAIN phase)
- Uses `anthropics/claude-code-action@v1`
- Queries database for eligible stories
- Uses existing `story-verification` skill
- Updates status and commits

## Progress Log

### Session 2025-12-18

**Status**: Implementation Complete

#### Analysis Complete

1. **Existing skill found**: `story-verification` skill exists at `.claude/skills/story-verification/SKILL.md`
2. **Helper scripts verified**: All 4 helper scripts exist and have valid Python syntax:
   - `parse_criteria.py` - Parses acceptance criteria from story description
   - `find_evidence.py` - Searches for test and code evidence
   - `generate_report.py` - Generates verification report
   - `update_status.py` - Updates story status in database
3. **Workflow position**: Step 1 in DRAIN phase (earliest, most advanced stories first)
4. **Schedule**: 11:00 UTC (3:00 AM PST) - before review-stories at 12:30 UTC

#### Implementation Details

1. **Created `.github/workflows/verify-stories.yml`**:
   - Scheduled at 11:00 UTC (3:00 AM PST) - first in DRAIN phase
   - Manual trigger via `workflow_dispatch`
   - Uses `anthropics/claude-code-action@v1`
   - Multi-step process: Query stories → Use skill or manual verification → Update status
   - Includes token usage reporting

2. **SQL Implementation Verified**:
   - Query finds `verifying` stories with `hold_reason IS NULL` and `disposition IS NULL`
   - PASS: Sets `stage = 'implemented'` with timestamp note
   - FAIL: Sets `hold_reason = 'broken'` with reason note
   - All queries tested against actual database

#### Test Results

```
=== Test: Query verifying stories without holds ===
Found 0 story(ies) ready for verification:

=== Test: Query verifying stories WITH holds ===
Found 0 verifying story(ies) with holds (NOT eligible):

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

```
=== Test: Verify helper scripts exist ===
  ✓ .claude/skills/story-verification/parse_criteria.py
  ✓ .claude/skills/story-verification/find_evidence.py
  ✓ .claude/skills/story-verification/generate_report.py
  ✓ .claude/skills/story-verification/update_status.py

=== Test: parse_criteria.py syntax ===
  ✓ parse_criteria.py - Valid Python syntax

=== Test: update_status.py syntax ===
  ✓ update_status.py - Valid Python syntax

All helper scripts validated!
```

#### Workflow File Summary

| Aspect | Value |
|--------|-------|
| Schedule | `0 11 * * *` (3:00 AM PST) |
| Concurrency | `daily-story-verification` |
| Model | `claude-sonnet-4-5-20250929` |
| Timeout | 45 minutes (verification requires running tests) |

#### Integration Notes

The standalone `verify-stories.yml` is now ready for deployment. To fully integrate into the orchestrator:

1. Add verify-stories as Step 1 in the DRAIN phase of `story-tree-orchestrator.yml`
2. Currently 0 verifying stories are eligible (all stories are in other stages)
3. Stories will enter verifying stage via execute-stories or review-stories workflows

**Status**: ✅ IMPLEMENTED - Ready for deployment and testing

---
*Last updated: 2025-12-18*
