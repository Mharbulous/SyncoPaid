# Handover 024: Status Reordering and 'broken' Status Rename

## Context

User requested two sequential changes to the Story Tree status system:

1. ✅ **Completed**: Renamed 'bugged' → 'broken' and moved it between 'concept' and 'refine', shifting all intermediate colors
2. ⏭️ **Next Task**: Reorder multiple statuses while keeping colors in their current positions

## What Was Completed

### Phase 1: 'bugged' → 'broken' Rename & Reorder

**Changes made:**
- Renamed status from 'bugged' to 'broken' (indicates major non-functional bug, not minor bugs)
- Moved 'broken' from position 12 to position 5 (after 'concept', before 'refine')
- Shifted colors for positions 5-12 to maintain rainbow progression

**Files updated:**
- `dev-tools\story-tree-explorer\story_tree_explorer-1-2.py` (PySide6 - main version)
- `dev-tools\story-tree-explorer\story_tree_explorer.py` (tkinter)
- `dev-tools\story-tree-explorer\story_tree_explorer-1-1.py` (tksheet)
- `dev-tools\story-tree-explorer\story_tree_explorer-1-0.py` (older version)
- `.claude\skills\story-tree\SKILL.md` (status table, excluded statuses list, SQL queries)
- `.claude\skills\story-tree\scripts\tree-view.py` (STATUS_SYMBOLS, STATUS_SYMBOLS_ASCII, ANSI_COLORS)

**Files NOT updated** (archived, leave as-is):
- `archived\story-tree-v1\*` - All archived story-tree v1 files

### Custom Checkbox Implementation (Completed Bonus Work)

Created `ColoredCheckBox` class in `story_tree_explorer-1-2.py` with:
- White checkmark on colored background when checked
- White background with gray border when unchecked
- Text colored to match status color
- Full custom `paintEvent()` to avoid Qt stylesheet limitations
- Proper `hitButton()` for clickable area

## Next Task: Status Reordering

### Goal

Reorder these statuses while **keeping colors at their current positions**:

**Desired order (positions 5-15):**
```
5. broken
6. deferred      (currently at 11)
7. refine        (currently at 6)
8. approved      (currently at 7)
9. epic          (currently at 8)
10. blocked      (currently at 10)
11. queued       (currently at 12)
12. paused       (currently at 13)
13. active       (currently at 14)
14. reviewing    (currently at 16)
15. in-progress  (currently at 15)
```

**What about 'planned'?** Currently at position 9, not in user's list - needs clarification.

**What about 'implemented'?** Currently at position 17, not in user's list - needs clarification.

### Approach: Word Replacement Mapping

User suggested creating a mapping that keeps colors in the same order but swaps which status name gets which color.

**Current position → color mapping (positions 5-17):**
```
5:  broken     → #CCCC00
6:  refine     → #99CC00
7:  approved   → #66CC00
8:  epic       → 
9:  planned    → #00CC00
10: blocked    → #00CC33
11: deferred   → #00CC66
12: queued     → #00CC99
13: paused     → #00CCCC
14: active     → #0099CC
15: in-progress→ #0066CC
16: reviewing  → 
17: implemented→ #0000CC
```

**Proposed remapping** (colors stay in place, names move):
```
Position 5 color → broken (no change)
Position 6 color → deferred (was refine)
Position 7 color → refine (was approved)
Position 8 color → approved (was epic)
Position 9 color → epic (was planned)
Position 10 color → blocked (no change)
Position 11 color → queued (was deferred)
Position 12 color → paused (was queued)
Position 13 color → active (was paused)
Position 14 color → reviewing (was active)
Position 15 color → in-progress (no change)
Position 16 color → ??? (was reviewing)
Position 17 color → ??? (was implemented)
```

**Problem**: User's list omits 'planned' and 'implemented' - need to handle these.

## Key Files Reference

### Primary files (must update):
- `dev-tools\story-tree-explorer\story_tree_explorer-1-2.py` - Main PySide6 version
- `.claude\skills\story-tree\SKILL.md` - Status documentation table
- `.claude\skills\story-tree\scripts\tree-view.py` - Tree view script

### Secondary files (should update for consistency):
- `dev-tools\story-tree-explorer\story_tree_explorer.py`
- `dev-tools\story-tree-explorer\story_tree_explorer-1-1.py`
- `dev-tools\story-tree-explorer\story_tree_explorer-1-0.py`

### Files to ignore:
- `archived\story-tree-v1\*` - Archived, historical only

## Technical Details

### STATUS_COLORS Dictionary Structure

Two color schemes exist:
1. **PySide6 versions** (1-2, 1-1): Hex colors optimized for Qt (`#CC0000` format)
2. **tkinter versions** (main, 1-0): Different hex colors optimized for tkinter

Each file has both `STATUS_COLORS` dict and `ALL_STATUSES` list.

### ALL_STATUSES List

Order in this list determines:
- Filter checkbox order in UI
- Display order in documentation tables
- Processing order in queries

Both STATUS_COLORS keys and ALL_STATUSES entries must match exactly.

## Implementation Strategy

1. **Get clarification** on 'planned' and 'implemented' positions
2. **Create complete mapping** for all 23 statuses
3. **Update STATUS_COLORS** - reassign colors to new status names at each position
4. **Update ALL_STATUSES** - reorder the list
5. **Update documentation** - SKILL.md table and exclusion lists
6. **Test** - Run story_tree_explorer-1-2.py to verify

## Previous Approaches

### What Worked:
- Creating todo list to track all files needing updates
- Updating colors in batches (all explorer files, then skill files)
- Using comments like `(was 'bugged')` to track color shifts

### What Failed:
- Initial attempts to use Qt stylesheets for custom checkboxes (Qt has limited pseudo-element support)
- Using checkbox icons (clicking only worked on text, not checkbox itself)
- Calling `super().paintEvent()` in custom widget (caused duplicate checkmarks)

### What Succeeded:
- Full custom `paintEvent()` implementation drawing everything manually
- `hitButton()` override to make entire widget clickable
- Hiding default indicator with `width: 0px; height: 0px` stylesheet

## Questions for User

Before proceeding:
1. Where should 'planned' go in the new order?
2. Where should 'implemented' go in the new order?
3. Should colors stay at their current positions (5-17) or also shift with the reordering?

## References

- Qt Checkbox styling: Custom `QCheckBox` requires full `paintEvent()` override for complex styling
- Color scheme is 23-status rainbow system progressing from red (infeasible) → violet (archived)
- Status progression represents "distance to production" (red=furthest, blue=closest, violet=past production)
