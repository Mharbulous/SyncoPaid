# Story Tree Explorer: tksheet Migration for Per-Cell Coloring

## Problem
ttk.Treeview doesn't support per-column styling - tags apply to entire rows. User wants Status column colored by status while ID/Title columns use black (or gray when faded for ancestor-only nodes).

## Current State
Migrating from ttk.Treeview to tksheet which supports per-cell coloring via `sheet.highlight(row=iid, column=col, fg=color)`.

### Files
- `dev-tools\story-tree-explorer\story_tree_explorer.py` - Main file (currently v1.0 code)
- `dev-tools\story-tree-explorer\story_tree_explorer-1-0.py` - Backup of ttk.Treeview version
- `dev-tools\story-tree-explorer\story_tree_explorer-1-1.py` - **Active prototype using tksheet**

## Issue Being Fixed
Filters and Refresh cause "iid 'root' already exists" error. Just applied fix using `sheet.tree_reset()` to clear treeview before rebuilding. **Needs testing.**

## tksheet Key APIs (from research)

```python
# Enable treeview mode
sheet = Sheet(parent, treeview=True)

# Insert hierarchical items
sheet.insert(parent="", iid="node_id", text="Display", values=["col0", "col1", "col2"])

# Per-cell coloring (the goal)
sheet.highlight(row="node_id", column=1, fg="#228B22")

# Clear treeview before rebuild
sheet.tree_reset()

# Expand nodes
sheet.tree_set_open(sheet.get_children())
```

## Failed Approaches
1. `sheet.set_sheet_data([])` - Doesn't clear treeview iids
2. Loop with `sheet.delete(iid)` - Didn't work properly
3. Building tree in both `_build_tree()` and `_apply_filters()` - Caused duplicate iid insertions

## Design Intent
- **Normal nodes**: Black ID, colored Status, black Title
- **Faded ancestors**: Gray ID, colored Status, gray Title

Coloring logic in `_add_filtered_node()` around line 860.

## Useful Documentation
- tksheet wiki: https://github.com/ragardner/tksheet/wiki/Version-7
- tksheet docs: https://ragardner.github.io/tksheet/DOCUMENTATION.html
- GitHub: https://github.com/ragardner/tksheet

## Next Steps
1. Test if `tree_reset()` fix works for filters and Refresh
2. Verify per-cell highlighting applies correctly
3. Test right-click context menu, double-click detail view
4. If working, update main `story_tree_explorer.py` with v1.1 code
