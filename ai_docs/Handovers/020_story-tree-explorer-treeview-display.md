# Story Tree Explorer: Treeview Display Not Working

## Current Problem
tksheet displays data as flat table rows, not hierarchical tree with collapsible nodes. Per-cell coloring now works correctly.

## What's Fixed
- Highlight API: Changed from `sheet.highlight(row=iid, column=col, fg=color)` to `sheet.highlight((row_idx, col), fg=color)` using `sheet.itemrow(iid)` to convert iid to row index
- No more "iid already exists" errors on filter/refresh (tree_reset() fix works)
- Per-cell coloring applies correctly (Status colored, ID/Title black or gray for faded ancestors)

## Files
- `dev-tools\story-tree-explorer\story_tree_explorer-1-1.py` - **Active prototype** - fix treeview display here
- `dev-tools\story-tree-explorer\story_tree_explorer-1-0.py` - Backup of working ttk.Treeview version (has tree structure but no per-cell coloring)
- `dev-tools\story-tree-explorer\story_tree_explorer.py` - Production file (currently v1.0 code)

## Root Cause Investigation Needed
The sheet is initialized with `treeview=True` but nodes display flat. Compare how v1.0 (ttk.Treeview) builds hierarchy vs v1.1 (tksheet).

Check these tksheet treeview APIs:
- `sheet.insert(parent=parent_iid, iid=node_id, ...)` - parent param may not be working as expected
- Tree expansion: `sheet.tree_set_open()`
- Treeview mode initialization options

## Key tksheet Documentation
- **Wiki (Version 7)**: https://github.com/ragardner/tksheet/wiki/Version-7
- **Full docs**: https://ragardner.github.io/tksheet/DOCUMENTATION.html
- **GitHub**: https://github.com/ragardner/tksheet

## Technical Notes from Research
```python
# Correct cell highlighting (WORKS)
row_idx = sheet.itemrow(iid)
sheet.highlight((row_idx, col), fg=color)

# Treeview insert (verify parent param works)
sheet.insert(parent="parent_iid", iid="child_iid", text="Display", values=[...])

# Clear tree before rebuild
sheet.tree_reset()

# Expand nodes
sheet.tree_set_open(sheet.get_children())
```

## Next Steps
1. Compare v1.0 ttk.Treeview insert logic with v1.1 tksheet insert
2. Verify `parent=` parameter in `sheet.insert()` creates hierarchy
3. Check if tksheet treeview mode requires additional config for tree display
4. May need to check tksheet wiki for treeview-specific examples
