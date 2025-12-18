# Handover: Update story-vetting Skill for Three-Field System

## Task

Update SKILL.md documentation to use three-field terminology instead of treating stage/hold_reason/disposition as a single "status" field.

## Issues to Fix

All in `.claude/skills/story-vetting/SKILL.md`:

### 1. Decision Matrix (Lines 49-69)

Current text lists status values without explaining which column they come from:

```diff
- **Mergeable with concepts:** `concept`, `wishlist`, `refine`
+ **Mergeable with concepts:**
+ - `stage = 'concept'`
+ - `disposition = 'wishlist'`
+ - `hold_reason = 'refine'`

- **Block against:** `rejected`, `infeasible`, `broken`, `pending`, `blocked`
+ **Block against:**
+ - `disposition IN ('rejected', 'infeasible')`
+ - `hold_reason IN ('broken', 'pending', 'blocked')`

- **Auto-delete/reject against:** `approved`, `planned`, `implemented`, ...
+ **Auto-delete/reject against:**
+ - `stage IN ('approved', 'planned', 'queued', 'active', 'reviewing', 'implemented', ...)`
+ - `disposition IN ('legacy', 'deprecated', 'archived')`
```

### 2. CI Mode Description (Line 77)

```diff
- **HUMAN_REVIEW → DEFER_PENDING**: Set concept status to `pending` with note
+ **HUMAN_REVIEW → DEFER_PENDING**: Set `hold_reason = 'pending'` with `human_review = 1` (stage preserved)
```

### 3. Output Format (Lines 137-139)

Current shows `"status": "concept"` - should clarify this is computed from COALESCE.

### 4. Summary Output (Line 282)

```diff
- 5 concepts set to 'pending' status for later human review.
+ 5 concepts set to hold_reason='pending' with human_review=1 for later review.
```

### 5. Add Three-Field Explanation Section

Add after the Decision Matrix:

```markdown
### Three-Field System Internals

The vetting system computes a pseudo-status field using:
```sql
COALESCE(disposition, hold_reason, stage) AS status
```

Priority: disposition (terminal) > hold_reason (paused) > stage (position)

This means:
- Story with `disposition='rejected'` shows status='rejected' regardless of stage
- Story with `hold_reason='pending'` shows status='pending' (stage preserved for resume)
- Story with only stage set shows that stage value
```

## Key Files

| File | Action |
|------|--------|
| `.claude/skills/story-vetting/SKILL.md` | Lines 49-69, 77, 137-139, 282 |

## Red Herrings (Do NOT Touch)

- **vetting_actions.py** - Covered in handover 038 (prioritize-story-notes)
- **vetting_processor.py** - Covered in handover 038
- **candidate_detector.py** - COALESCE at line 234 is intentional and correct
- **bulk_vetting.py** - Already uses correct three-field updates
- **process_candidates.py** - Works correctly with computed status field
- **Actual database UPDATE statements** - Already use correct three-field syntax

## Reference: Value Mappings

| Value | Three-Field Column |
|-------|-------------------|
| concept, approved, planned, active, reviewing, implemented, ready, released | `stage` |
| pending, blocked, paused, broken, refine | `hold_reason` |
| rejected, infeasible, wishlist, legacy, deprecated, archived | `disposition` |

## Verification

```bash
# After fixes, documentation should reference columns explicitly
grep -n "stage\s*=\|hold_reason\s*=\|disposition\s*=" .claude/skills/story-vetting/SKILL.md
# Expected: Multiple matches in the decision matrix section
```
