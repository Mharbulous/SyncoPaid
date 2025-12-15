# Story Tree Explorer: Treeview Display - FIXED

## Problem (Resolved)
tksheet displayed data as flat table rows instead of hierarchical tree with collapsible nodes.

## Root Cause
In tksheet treeview mode, the tree hierarchy (indentation, expand/collapse controls) is rendered in the **row index column** using the `text` parameter. The code had `show_row_index=False`, which hid the entire tree structure.

## Fix Applied (2024-12-14)
1. **Show row index**: Changed `show_row_index=False` to `show_row_index=True`
2. **Column restructure**:
   - `text` parameter now holds node ID (displayed in row index with tree hierarchy)
   - `values` array now contains only [status, title] (2 columns instead of 3)
3. **Headers updated**: Changed from ["ID", "Status", "Title"] to ["Status", "Title"]
4. **Column widths**: Adjusted for 2-column layout + index_width=180 for tree column
5. **Event handlers**: Changed from `get_index_data(row)` to `rowitem(row)` to get node iid

## tksheet Treeview Key Concepts
- `text` parameter = displayed in row index (tree column with hierarchy)
- `values` parameter = displayed in data columns
- `rowitem(row)` = get iid from row number
- `itemrow(iid)` = get row number from iid

## Files
- `dev-tools\story-tree-explorer\story_tree_explorer-1-1.py` - **Active prototype** with fix
- `dev-tools\story-tree-explorer\story_tree_explorer-1-0.py` - Backup (ttk.Treeview version)
- `dev-tools\story-tree-explorer\story_tree_explorer.py` - Production file (v1.0 code)

## Testing Required
Run the explorer and verify:
- [ ] Tree structure shows with indentation
- [ ] Expand/collapse controls work
- [ ] Node selection shows description
- [ ] Double-click opens detail view
- [ ] Right-click context menu works
- [ ] Status filters work (matching nodes + faded ancestors)
- [ ] Per-cell coloring applies correctly

## Reference
- **Wiki (Version 7)**: https://github.com/ragardner/tksheet/wiki/Version-7
- **Full docs**: https://ragardner.github.io/tksheet/DOCUMENTATION.html
