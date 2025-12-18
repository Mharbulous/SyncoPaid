# Handover: Update story-planning Skill for Three-Field System

## Task

Fix 3 cosmetic label issues where template output shows "Status" instead of "Stage".

## Issues to Fix

All in `.claude/skills/story-planning/SKILL.md`:

### 1. Line 127 (Interactive Mode Template)

```diff
- **Status:** `planned`
+ **Stage:** `planned`
```

### 2. Line 240 (CI Mode Template)

```diff
- **Story ID:** [ID] | **Created:** [YYYY-MM-DD] | **Status:** `planned`
+ **Story ID:** [ID] | **Created:** [YYYY-MM-DD] | **Stage:** `planned`
```

### 3. Line 376 (CI Mode Output Format)

```diff
- Status: approved -> planned
+ Stage: approved -> planned
```

## Key File

`.claude/skills/story-planning/SKILL.md` - Only file needing changes

## Red Herrings (Do NOT Touch)

- **SQL Query (Line 59)** - Already correct: `WHERE s.stage = 'approved' AND s.hold_reason IS NULL`
- **Database Update (Lines 346-352)** - Already correct: `SET stage = 'planned'`
- **Stage Validation (Line 83)** - Already correct terminology

The skill is functionally compliant; only display labels need updating.

## Verification

```bash
# After fixes, should find only lowercase "stage" references, no "Status:" labels
grep -n "Status:" .claude/skills/story-planning/SKILL.md
# Expected: 0 matches

grep -n "Stage:" .claude/skills/story-planning/SKILL.md
# Expected: 3 matches at lines 127, 240, 376
```
