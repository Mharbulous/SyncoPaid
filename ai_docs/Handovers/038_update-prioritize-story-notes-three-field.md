# Handover: Update prioritize-story-notes Skill for Three-Field System

## Task

Fix critical vetting system constants that mix stage/hold_reason/disposition values as if they were a single "status" field.

## Context

The three-field system uses:
- `stage`: workflow position (concept, approved, planned, active, reviewing, implemented, verifying, verified, ready, released)
- `hold_reason`: why paused (pending, blocked, paused, broken, refine) - NULL if active
- `disposition`: terminal state (rejected, wishlist, archived, etc.) - NULL if in pipeline

## Critical Issues to Fix

### 1. vetting_actions.py (Lines 8-9)

```python
# CURRENT - mixes three different columns:
MERGEABLE_STATUSES = {'concept', 'wishlist', 'refine'}
BLOCK_STATUSES = {'rejected', 'infeasible', 'broken', 'pending', 'blocked'}
```

The problem: `concept` is a stage, `wishlist` is a disposition, `refine` is a hold_reason. These constants work due to a hidden COALESCE mapping in `candidate_detector.py:234` but are semantically misleading.

**Fix:** Add explanatory comments documenting which field each value comes from:
```python
# Three-field system mappings (values from COALESCE(disposition, hold_reason, stage))
# - 'concept' = stage='concept'
# - 'wishlist' = disposition='wishlist'
# - 'refine' = hold_reason='refine'
MERGEABLE_STATUSES = {'concept', 'wishlist', 'refine'}
```

### 2. vetting_processor.py (Lines 23-24)

Same issue - duplicate constants. Apply identical fix.

## Key Files

| File | Purpose |
|------|---------|
| `.claude/skills/prioritize-story-notes/SKILL.md` | Main skill doc - already compliant |
| `.claude/skills/story-vetting/vetting_actions.py` | Lines 8-9: Constants to fix |
| `.claude/skills/story-vetting/vetting_processor.py` | Lines 23-24: Duplicate constants |
| `.claude/skills/story-vetting/candidate_detector.py` | Line 234: The hidden COALESCE that makes constants work |
| `.claude/skills/story-tree/references/schema.sql` | Three-field definition |

## Red Herrings (Do NOT Touch)

- **prioritize-story-notes/SKILL.md** - Already uses `stage='approved'`, `hold_reason IS NULL` correctly
- **story_tree_helpers.py** - Already compliant
- **story_workflow.py** - Already compliant
- **The actual vetting logic** - Works correctly; only comments/documentation need updates

## Verification

```bash
# After changes, grep for the explanatory comments
grep -n "COALESCE\|stage=\|disposition=\|hold_reason=" .claude/skills/story-vetting/vetting_actions.py
grep -n "COALESCE\|stage=\|disposition=\|hold_reason=" .claude/skills/story-vetting/vetting_processor.py
```

## Why This Matters

Future developers will see `MERGEABLE_STATUSES = {'concept', 'wishlist', 'refine'}` and assume these are all values from the same database column. Without comments explaining the COALESCE mapping, they may write broken queries like `WHERE status IN ('concept', 'wishlist')` instead of `WHERE stage = 'concept' OR disposition = 'wishlist'`.
