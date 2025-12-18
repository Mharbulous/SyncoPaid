# Handover: Update story-tree Skill for Three-Field System

## Task

1. Remove or deprecate incompatible migration script
2. Update outdated documentation in reference files

## Critical Issues

### 1. migrate_v1_to_v2.py - ENTIRE SCRIPT INCOMPATIBLE

**File:** `.claude/skills/story-tree/scripts/migrate_v1_to_v2.py`

The script header claims "v2.x → v3.0 (21-Status System)" but implements the OLD single-column status system, not the current three-field system.

**Lines 17-31:** Defines `OLD_STATUSES` and `NEW_STATUSES` with values like `'epic'`, `'bugged'`, `'in-progress'` that don't exist in three-field.

**Lines 100-121:** Schema creates single `status` column, ignores stage/hold_reason/disposition.

**Action:** Either:
- DELETE the script entirely, OR
- Add deprecation notice at top:
```python
"""
DEPRECATED: This script migrates v1.x → v2.x (old single-status system).
NOT compatible with current three-field system (stage, hold_reason, disposition).
For current schema, see: references/schema.sql
"""
```

### 2. rationales.md (Line 15)

```diff
- Priority algorithm excludes: `concept`, `rejected`, `deprecated`, `infeasible`, `bugged`
+ Priority algorithm excludes stories where:
+ - `stage = 'concept'` (not yet approved)
+ - `hold_reason IS NOT NULL` (blocked/pending/broken/refine)
+ - `disposition IS NOT NULL` (rejected/archived/etc)
```

Note: `bugged` doesn't exist in three-field system.

### 3. common-mistakes.md (Line 11)

```diff
- Always run git analysis before generation. Update status from in-progress → implemented if match found.
+ Always run git analysis before generation. Update stage from 'active' or 'reviewing' → 'implemented' if match found.
```

Note: `in-progress` was old status; active work now uses `stage = 'active'`.

### 4. epic-decomposition.md (Lines 8, 10)

Current text references `epic` as a status value. In three-field system, epics are identified by `capacity > 5` or explicit tags, not a status value.

```diff
- 2. **Excluded from generation** - `epic` is excluded from priority algorithm because epic nodes already have approved scope
+ 2. **Excluded from generation** - Parent/epic nodes (identified by `capacity > 5` or children) are excluded from priority algorithm. They should have `stage >= 'approved'` and focus on decomposition.
```

## Key Files

| File | Action |
|------|--------|
| `.claude/skills/story-tree/scripts/migrate_v1_to_v2.py` | Delete or deprecate |
| `.claude/skills/story-tree/references/rationales.md` | Line 15 |
| `.claude/skills/story-tree/references/common-mistakes.md` | Line 11 |
| `.claude/skills/story-tree/references/epic-decomposition.md` | Lines 8, 10 |

## Red Herrings (Do NOT Touch)

- **SKILL.md** - Already compliant
- **schema.sql** - Already defines three-field system correctly
- **sql-queries.md** - Already shows three-field query patterns
- **tree-view.py** - COALESCE usage is intentional for display (disposition > hold_reason > stage priority is correct)
- **migrate_to_three_field.py** - This is the CORRECT migration script (different from v1_to_v2)

## Reference

| Value Type | Three-Field Column |
|------------|-------------------|
| concept, approved, planned, active, reviewing, implemented, ready, released | `stage` |
| pending, blocked, paused, broken, refine | `hold_reason` |
| rejected, infeasible, wishlist, legacy, deprecated, archived | `disposition` |

## Verification

```bash
# Confirm old status values removed from docs
grep -rn "in-progress\|bugged\|epic" .claude/skills/story-tree/references/
# Expected: 0 matches after fixes
```
