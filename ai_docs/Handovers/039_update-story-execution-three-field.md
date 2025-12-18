# Handover: Update story-execution Skill for Three-Field System

## Task

Fix commands and plan files that still use the old `status` column instead of `stage`.

## Context

The three-field migration (commit f45c6df) replaced `WHERE status = 'X'` with:
- `WHERE stage = 'X'` for workflow positions
- `WHERE hold_reason = 'X'` for paused states
- `WHERE disposition = 'X'` for terminal states

## Issues to Fix

### 1. review-stories.md (Line 21) - BLOCKING

```sql
-- CURRENT (broken):
WHERE s.status = 'concept'

-- FIX:
WHERE s.stage = 'concept'
```

**File:** `.claude/commands/review-stories.md`

### 2. Plan Files - Documentation Examples

These are historical plan files with example SQL that references old columns:

**File:** `.claude/data/plans/2025-12-16-write-stories-workflow-token-optimization.md`
- Line 181: `WHERE s.status NOT IN (...)` - complex status list
- Line 243: `WHERE status = 'implemented'` → `WHERE stage = 'implemented'`
- Line 245: `WHERE status = 'concept'` → `WHERE stage = 'concept'`

**File:** `.claude/data/plans/2025-12-16-visualize-workflow-token-optimization.md`
- Line 101: `WHERE status = 'approved'` → `WHERE stage = 'approved'`
- Line 103: `WHERE status = 'rejected'` → `WHERE disposition = 'rejected'`
- Line 116, 131: Similar fixes

### 3. Special Case: Line 181 Complex Query

The current query excludes old status values:
```sql
WHERE s.status NOT IN ('concept', 'broken', 'refine', 'rejected', 'wishlist', ...)
```

This maps to three-field as:
```sql
WHERE s.stage NOT IN ('concept')
  AND s.hold_reason IS NULL
  AND s.disposition IS NULL
```

## Key Files

| File | Action |
|------|--------|
| `.claude/commands/review-stories.md` | Line 21: `status` → `stage` |
| `.claude/data/plans/2025-12-16-write-stories-workflow-token-optimization.md` | Lines 181, 243, 245 |
| `.claude/data/plans/2025-12-16-visualize-workflow-token-optimization.md` | Lines 101, 103, 116, 131 |

## Red Herrings (Do NOT Touch)

- **story-execution/SKILL.md** - Already compliant with three-field system
- **story-verification/SKILL.md** - Already uses `hold_reason` correctly
- **story-verification/update_status.py** - Maintains intentional backward compatibility
- **write-story.md** - Already uses `hold_reason` correctly
- **Database triggers** - `status` column maintained via trigger for backward compatibility

## Status Value Mappings

When converting old queries:

| Old Status | Three-Field Equivalent |
|------------|----------------------|
| `concept` | `stage = 'concept'` |
| `approved`, `planned`, `active`, `reviewing`, `implemented`, `released` | `stage = 'X'` |
| `pending`, `blocked`, `paused`, `broken`, `refine` | `hold_reason = 'X'` |
| `rejected`, `wishlist`, `infeasible`, `archived`, `deprecated`, `legacy` | `disposition = 'X'` |

## Verification

```bash
# Should return 0 matches after fixes
grep -rn "s\.status\s*=" .claude/commands/ .claude/data/plans/
grep -rn "WHERE status\s*=" .claude/commands/ .claude/data/plans/
```
