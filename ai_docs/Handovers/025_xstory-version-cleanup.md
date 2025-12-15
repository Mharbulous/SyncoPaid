# Handover: Xstory Version Cleanup & Detail View UI Refinement

**Status: IN PROGRESS**

## Task
1. Remove obsolete xstory versions to prevent confusion in future sessions
2. Document recent UI improvement: hide "Open Database..." and "Refresh" buttons in detail view

## What Just Happened

User reported that changes made to detail view weren't visible when running `./Xstory`. Root cause: Modified wrong file (`xstory.py` instead of `xstory-1-2.py`). The launcher script executes `xstory-1-2.py`, which is the current PySide6/Qt version.

**Changes applied**: When user double-clicks a story node to view details, the "Open Database..." and "Refresh" buttons now hide. They reappear when closing detail view.

## Files to Keep vs Delete

### KEEP:
- **`dev-tools/xstory/xstory-1-2.py`** - Current version (PySide6/Qt) ✓
- **`dev-tools/xstory/build.py`** - Build script
- **`Xstory`** - Launcher script (points to xstory-1-2.py)

### DELETE:
- `dev-tools/xstory/xstory.py` - tkinter version (37KB, modified Dec 14 23:58)
- `dev-tools/xstory/xstory-1-0.py` - Old version (34KB)
- `dev-tools/xstory/xstory-1-1.py` - Old version (36KB)

## Recent Implementation (Detail View Button Hiding)

**File**: `dev-tools/xstory/xstory-1-2.py`

**Changes**:
1. Lines 542-548: Store button references as `self.open_btn` and `self.refresh_btn`
2. Lines 676-677 in `show_detail_view()`: Added `self.open_btn.hide()` and `self.refresh_btn.hide()`
3. Lines 667-668 in `show_tree_view()`: Added `self.open_btn.show()` and `self.refresh_btn.show()`

**Rationale**: UI clutter reduction. Database operations irrelevant when viewing single node details.

## Tech Stack

**Current Version (xstory-1-2.py)**:
- **Framework**: PySide6 (Qt for Python)
- **Main widget**: QTreeWidget for hierarchical story display
- **Database**: SQLite with closure table pattern (`.claude/data/story-tree.db`)
- **Views**: Two-pane system (tree view ↔ detail view)

**Deprecated Versions**:
- xstory.py: tkinter-based (replaced by PySide6 for better UI capabilities)
- xstory-1-0.py, xstory-1-1.py: Earlier PySide6 iterations

## Key Architecture Details

### View Switching System
- `show_tree_view()`: Displays tree, shows toolbar buttons
- `show_detail_view(node_id)`: Displays single node, hides toolbar buttons
- DetailView class maintains navigation history (back/forward buttons)

### Status System
Uses 21-status rainbow system with role-based transitions (Designer/Engineer modes). See handover 024 for full status definitions and transition tables.

## Red Herrings

- **`archived/story-tree-explorer/`** - Contains even older versions; ignore
- **`src/syncopaid/`** - Main SyncoPaid app (window tracker); unrelated to story-tree
- **`.claude/skills/story-tree/SKILL.md`** - Skill prompt documentation, not UI code

## Next Steps

1. Delete obsolete versions: `xstory.py`, `xstory-1-0.py`, `xstory-1-1.py`
2. Verify `./Xstory` launcher still works after cleanup
3. Consider renaming `xstory-1-2.py` → `xstory.py` (no longer need version suffix)
4. Update launcher script if renaming

## Documentation References

- **024_status-context-menu-role-toggle.md** - Role-based status transitions
- **ai_docs/story-tree-workflow-diagrams.md** - Visual workflow documentation
- **.claude/skills/story-tree/references/schema.sql** - Database schema

## Testing

Verify after cleanup:
```bash
./Xstory  # Should launch xstory-1-2.py
# Double-click any node → buttons should hide
# Click "Close" → buttons should reappear
```
