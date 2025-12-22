# Plan: Reclassify 'wishlist' from Disposition to Hold Status

## Summary

Move `wishlist` from the `disposition` field (terminal states) to the `hold_reason` field (temporary pauses). This reflects the semantic reality that wishlist items are deferred indefinitely, not terminated—they can be revived when resources/priorities allow.

### Rationale

| Current (Disposition) | Proposed (Hold Reason) |
|----------------------|------------------------|
| Terminal state | Indefinite deferral |
| Exits pipeline | Stays in pipeline |
| Same category as 'rejected', 'archived' | Same category as 'blocked', 'paused' |
| Cannot be resumed | Can be promoted to active work |

### New Field Values After Change

**hold_reason** (8 values + NULL):
```
queued, pending, paused, blocked, broken, polish, conflict, wishlist
```

**disposition** (6 values + NULL):
```
rejected, infeasible, duplicative, legacy, deprecated, archived
```

---

## Detailed Checklist

### 1. Database Schema
**File:** `.claude/skills/story-tree/references/schema.sql`

- [ ] **Line 20-21:** Add 'wishlist' to hold_reason CHECK constraint
  ```sql
  CHECK (hold_reason IS NULL OR hold_reason IN (
      'queued', 'pending', 'paused', 'blocked', 'broken', 'polish', 'conflict', 'wishlist'
  ))
  ```

- [ ] **Line 23-26:** Remove 'wishlist' from disposition CHECK constraint
  ```sql
  CHECK (disposition IS NULL OR disposition IN (
      'rejected', 'infeasible', 'duplicative', 'legacy', 'deprecated', 'archived'
  ))
  ```

- [ ] **Lines 117-135:** Update comment reference section:
  - Move wishlist from DISPOSITION section to HOLD_REASON section
  - Update description: "wishlist = Indefinite hold, maybe someday"
  - Update disposition count from 7 to 6
  - Update hold_reason count from 7 to 8

---

### 2. Python Constants - story_db_common.py
**File:** `.claude/skills/story-tree/utility/story_db_common.py`

- [ ] **Line 32:** Update MERGEABLE_STATUSES comment (wishlist is now a hold_reason, still mergeable)
  ```python
  MERGEABLE_STATUSES = {'concept', 'wishlist', 'polish'}
  # Note: concept=stage, wishlist=hold_reason, polish=hold_reason
  ```

- [ ] **Line 129:** Update compute_effective_status docstring to note wishlist is now a hold_reason

---

### 3. Xstory UI Application
**File:** `dev-tools/xstory/xstory.py`

#### Constants Section (lines 69-101)

- [ ] **Line 84:** Move 'wishlist' from DISPOSITION_VALUES to HOLD_REASON_VALUES
  ```python
  HOLD_REASON_VALUES = {'pending', 'paused', 'blocked', 'broken', 'polish', 'conflict', 'wishlist'}
  DISPOSITION_VALUES = {'rejected', 'infeasible', 'duplicative', 'legacy', 'deprecated', 'archived'}
  ```

- [ ] **Line 89:** Update HOLD_REASON_ORDER (add wishlist at end - most indefinite)
  ```python
  HOLD_REASON_ORDER = ['pending', 'paused', 'blocked', 'broken', 'polish', 'conflict', 'wishlist']
  ```

- [ ] **Line 90:** Update DISPOSITION_ORDER (remove wishlist)
  ```python
  DISPOSITION_ORDER = ['rejected', 'infeasible', 'duplicative', 'legacy', 'deprecated', 'archived']
  ```

- [ ] **Lines 93-101:** Add wishlist to HOLD_ICONS
  ```python
  HOLD_ICONS = {
      'queued': '📋',
      'pending': '⏳',
      'paused': '⏸',
      'blocked': '🚧',
      'broken': '🔥',
      'polish': '💎',
      'conflict': '⚔',
      'wishlist': '💭',  # NEW - dreaming/wishing
  }
  ```

#### Status Colors (lines 32-67)

- [ ] **Line 38:** Move wishlist color comment to hold reasons section or relabel
  - Consider changing color to cyan/blue family (hold colors) instead of orange (disposition colors)
  - OR keep orange but note it's a hold status
  - Recommendation: Keep '#CC6600' but move to hold section comment

#### Designer Transitions (lines 103-122)

- [ ] **Lines 105-110:** Update transitions involving wishlist (now sets hold_reason, not disposition)
  ```python
  DESIGNER_TRANSITIONS = {
      'infeasible': ['concept', 'wishlist', 'archived'],  # wishlist now valid (sets hold_reason)
      'rejected': ['concept', 'wishlist', 'archived'],
      'wishlist': ['concept', 'rejected', 'archived'],  # FROM wishlist (clears hold, may set disp)
      'concept': ['approved', 'pending', 'rejected', 'wishlist', 'polish'],
      'polish': ['concept', 'ready', 'rejected', 'wishlist'],
      'pending': ['approved', 'wishlist', 'rejected'],
      # ... rest unchanged
  }
  ```

#### Status Update Logic (lines 1121-1151)

- [ ] **Lines 1125-1148:** The `_update_node_status_in_db` method already checks value sets correctly. After updating HOLD_REASON_VALUES and DISPOSITION_VALUES, this will automatically route 'wishlist' through the hold_reason branch instead of disposition branch. **No code change needed** - just verify constants are correct.

---

### 4. Test File
**File:** `tests/test_xstory_filters.py`

- [ ] **Line 14:** Update HOLD_REASON_ORDER (add wishlist)
  ```python
  HOLD_REASON_ORDER = ['no hold', 'queued', 'pending', 'paused', 'blocked', 'broken', 'polish', 'wishlist']
  ```

- [ ] **Line 15:** Update DISPOSITION_ORDER (remove wishlist)
  ```python
  DISPOSITION_ORDER = ['live', 'rejected', 'infeasible', 'conflict', 'legacy', 'deprecated', 'archived']
  ```
  Note: 'conflict' in this list appears to be a bug - it's a hold_reason, not disposition. Consider fixing.

- [ ] **Lines 62-64:** Update test fixtures - wishlist nodes now have hold_reason instead of disposition
  ```python
  StoryNode(id='8', status='wishlist', stage='concept', hold_reason='wishlist'),
  ```

---

### 5. Commands
**File:** `.claude/commands/review-stories.md`

- [ ] **Line 73:** Update Wishlist SQL to use hold_reason
  ```sql
  SET hold_reason = 'wishlist', updated_at = datetime('now')
  ```

- [ ] **Lines 121-134:** Update the wishlist SQL block
  ```python
  cursor.execute('''
      UPDATE story_nodes
      SET hold_reason = 'wishlist', updated_at = datetime('now')
      WHERE id = '[STORY_ID]'
  ''')
  ```

- [ ] **Line 63:** Update options comment: "Approve | Reject | Refine | Wishlist" (no change needed, just verify)

**File:** `.claude/commands/write-story.md`

- [ ] **Line 153:** Update workflow diagram comment (wishlist is now a hold state)
  ```
  Hold:         refine, wishlist ───────────────────────────────┘
  ```

---

### 6. Tree View Script
**File:** `.claude/skills/story-tree/scripts/tree-view.py`

- [ ] **Lines 20-28, 30-38:** Status symbols already include wishlist - no change needed (symbols are per-status, not per-field)

- [ ] **Lines 40-52:** ANSI colors already include wishlist - no change needed

---

### 7. Skill Documentation

**File:** `.claude/skills/story-tree/SKILL.md`

- [ ] **Lines 139-149:** Update Hold Reason table - add wishlist row
  ```markdown
  | wishlist | Indefinite hold, maybe someday |
  ```

- [ ] **Lines 151-162:** Update Disposition table - remove wishlist row, update Stage Required column note

- [ ] **Line 181:** Update MERGEABLE_STATUSES comment
  ```python
  MERGEABLE_STATUSES,         # {'concept', 'wishlist', 'polish'} - note: wishlist/polish are hold_reasons
  ```

**File:** `.claude/skills/story-vetting/SKILL.md`

- [ ] **Lines 51, 69:** Update references to wishlist being a disposition
  - Line 51: Merge rules table
  - Line 69: "disposition = 'wishlist'" → "hold_reason = 'wishlist'"

- [ ] **Lines 193-194:** Update MERGEABLE_STATUSES comment to note wishlist is now a hold_reason

---

### 8. Workflow Diagrams
**File:** `.claude/skills/story-tree/references/workflow-diagrams.md`

- [ ] **Lines 37, 130-137:** Move wishlist from Disposition States diagram to Hold States diagram

- [ ] **Lines 98-120:** Add wishlist to Hold States mindmap
  ```mermaid
  mindmap
    root((Any Stage))
      ...existing holds...
      wishlist
        Indefinite deferral
        Clear: Priority increases
  ```

- [ ] **Lines 122-141:** Remove wishlist from Disposition States diagram

---

### 9. Epic Decomposition Reference
**File:** `.claude/skills/story-tree/references/epic-decomposition.md`

- [ ] **Lines 12-14:** Update wishlist vs rejected distinction to reflect wishlist as hold_reason
  ```markdown
  - **wishlist** (hold_reason): Desirable but indefinitely deferred
  - **rejected** (disposition): Decided not to implement
  ```

---

### 10. Migration Script (NEW)
**File:** `dev-tools/xstory/migrate_wishlist_to_hold.py` (create new)

- [ ] Create migration script to:
  1. Backup database
  2. For all rows where `disposition = 'wishlist'`:
     - Copy `disposition` value to `hold_reason`
     - Set `disposition = NULL`
  3. Verify migration success

```python
# Pseudocode
UPDATE story_nodes
SET hold_reason = 'wishlist', disposition = NULL
WHERE disposition = 'wishlist'
```

---

### 11. Handover Documentation (Optional but Recommended)

- [ ] Create handover document: `ai_docs/Handovers/044_wishlist-to-hold-reason.md`
  - Document the rationale
  - List all changed files
  - Include migration instructions
  - Note any queries that need updating

---

## Execution Order

1. **Schema first** - Update schema.sql (reference document)
2. **Constants** - Update Python constants in story_db_common.py and xstory.py
3. **Tests** - Update test_xstory_filters.py to match new structure
4. **Run tests** - Verify tests pass with new constants
5. **Commands** - Update review-stories.md and write-story.md
6. **Documentation** - Update SKILL.md files, workflow diagrams
7. **Migration** - Create and test migration script
8. **Run migration** - Execute on actual database
9. **Final verification** - Run xstory app, verify wishlist items display correctly

---

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Existing wishlist items in DB have wrong field | Migration script converts them |
| UI shows wishlist items incorrectly | Update filter checkboxes to new column |
| Queries exclude wishlist items | Most queries check both fields; verify |
| Transition logic breaks | Tests will catch; DISPOSITION_VALUES/HOLD_REASON_VALUES drive logic |

---

## Verification Checklist

After implementation:

- [ ] `python -m pytest tests/test_xstory_filters.py` passes
- [ ] Xstory app launches without errors
- [ ] Wishlist filter checkbox appears in "Hold Status" column, not "Disposition"
- [ ] Can transition story TO wishlist (sets hold_reason)
- [ ] Can transition story FROM wishlist (clears hold_reason)
- [ ] Wishlist items show hold icon (💭) in tree view
- [ ] Migration script runs without errors on test database
