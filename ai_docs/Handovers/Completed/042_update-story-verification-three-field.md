# Handover: Update story-verification Skill for Three-Field System

## Task

1. Fix terminology issues (code uses "status" instead of "stage")
2. Remove unnecessary backward compatibility layer

## Issues to Fix

### 1. update_status.py - Remove Legacy Compatibility (Lines 26-34, 46-48)

The `VALID_STATUSES` constant accepts old status values "for backward compatibility" but the migration is complete.

```python
# CURRENT (lines 26-34):
# Legacy: kept for backward compatibility
VALID_STATUSES = {
    'infeasible', 'rejected', 'wishlist',
    'concept', 'broken', 'blocked', 'refine',
    ...
}

# Lines 46-48: accepts both sets
if new_stage not in VALID_STAGES and new_stage not in VALID_STATUSES:
```

**Fix:** Remove `VALID_STATUSES` entirely. Only validate against `VALID_STAGES`:
```python
if new_stage not in VALID_STAGES:
    return {"error": f"Invalid stage: {new_stage}", "valid_stages": list(VALID_STAGES)}
```

### 2. update_status.py - Documentation (Lines 3, 6, 10)

```diff
- Update story status based on verification results.
+ Update story stage and hold_reason based on verification results.

- python update_status.py <story_id> <new_status> ["<verification_notes>"]
+ python update_status.py <story_id> <new_stage> ["<verification_notes>"]
```

### 3. parse_criteria.py - Rename COALESCE Result (Line 41)

```python
# CURRENT:
COALESCE(disposition, hold_reason, stage) AS status

# FIX - rename to clarify it's a computed display value:
COALESCE(disposition, hold_reason, stage) AS display_state
```

Also update line 58 output:
```python
"display_state": story_dict['display_state'],
```

### 4. generate_report.py - Variable Names (Lines 189-204)

```python
# CURRENT:
suggested_status = "ready"
"current_status": story_data.get('status'),

# FIX:
suggested_stage = "ready"
"current_stage": story_data.get('stage'),
```

## Key Files

| File | Lines | Change |
|------|-------|--------|
| `.claude/skills/story-verification/update_status.py` | 3, 6, 10, 26-34, 46-48 | Remove legacy compat, fix docs |
| `.claude/skills/story-verification/parse_criteria.py` | 41, 58 | Rename `status` → `display_state` |
| `.claude/skills/story-verification/generate_report.py` | 189-204, 222 | Rename variables |

## Red Herrings (Do NOT Touch)

- **SKILL.md** - Already compliant
- **find_evidence.py** - No status references
- **Lines 72-77, 82-85 in update_status.py** - Already use correct three-field syntax (`hold_reason = 'pending'`, `stage = ?`)
- **Line 160 in update_status.py** - Correctly selects `stage, hold_reason, disposition, human_review`

## Cascading Changes

If you rename `status` → `display_state` in parse_criteria.py, you must also update generate_report.py which reads `story_data.get('status')`.

Consider whether to:
- Option A: Rename to `display_state` (clearer semantics)
- Option B: Keep as `status` but add comment explaining it's computed from COALESCE

## Verification

```bash
# After removing VALID_STATUSES:
grep -n "VALID_STATUSES" .claude/skills/story-verification/update_status.py
# Expected: 0 matches

# After renaming status variables:
grep -n "suggested_status\|current_status" .claude/skills/story-verification/generate_report.py
# Expected: 0 matches
```
