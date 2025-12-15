# Research: Alternatives to tksheet for Python Desktop Treeview

## Research Objective
Find Python GUI libraries/widgets that can display hierarchical tree data with per-cell styling capabilities, as an alternative to tksheet.

## Current Solution: tksheet
- **What it is**: Python tkinter-based spreadsheet/treeview widget
- **GitHub**: https://github.com/ragardner/tksheet
- **Version**: 7.5.19 (latest as of Dec 2024)

### What tksheet does well
- Treeview mode with parent-child hierarchy
- Per-cell color customization via `sheet.highlight((row, col), fg=color)`
- Insert nodes with `sheet.insert(parent=parent_iid, iid=node_id, text=..., values=[...])`
- Expand/collapse functionality
- Good performance

### Problems with tksheet
1. **Arrow direction is wrong**: Expanded nodes show UP-pointing arrow (^) instead of the universal DOWN-pointing arrow (v). This is hardcoded in `row_index.py` with no configuration option.
2. **Development ceased**: Maintainer states only bug fixes/behavioral issues will be addressed
3. **Unconventional treeview model**: Tree hierarchy displays in row index column (via `text` param), not in a dedicated tree column like ttk.Treeview

## Requirements for Alternative

### Must Have
- [ ] Hierarchical treeview display (parent-child with indentation)
- [ ] Expand/collapse nodes (preferably with standard down/right arrows)
- [ ] Per-cell font color customization (different colors for different columns in same row)
- [ ] Python 3.11+ compatible
- [ ] Windows 11 compatible
- [ ] Reasonably active maintenance or stable

### Nice to Have
- [ ] Built on tkinter (for consistency with existing app)
- [ ] Table-like display with multiple columns
- [ ] Selection events (single-click, double-click)
- [ ] Right-click context menu support
- [ ] Keyboard navigation
- [ ] Sorting/filtering capabilities

## Alternatives to Research

### tkinter-based
1. **ttk.Treeview** (standard library)
   - Pros: Built-in, stable, standard arrow directions
   - Cons: No per-cell coloring (only per-row tags), limited styling
   - Question: Any workarounds for per-cell styling?

2. **ttkwidgets** / **ttkbootstrap**
   - Enhanced ttk widgets - do they add per-cell styling to Treeview?

3. **CustomTkinter**
   - Modern-looking tkinter widgets - does it have a treeview?

### Other GUI frameworks
4. **PyQt / PySide (QTreeView, QTreeWidget)**
   - Pros: Powerful, extensive styling via delegates
   - Cons: Different framework, heavier dependency

5. **wxPython (wx.TreeCtrl, wx.dataview.TreeListCtrl)**
   - Pros: Native look, TreeListCtrl has columns
   - Cons: Different framework

6. **DearPyGui**
   - Modern immediate-mode GUI - tree support?

7. **Kivy**
   - Cross-platform - tree widget availability?

### Web-based / Hybrid
8. **Eel / PyWebView + JavaScript tree component**
   - Use web tech for UI, Python for backend

## Context: Current Application

**Xstory** - Desktop app for viewing hierarchical story data from SQLite database.

Current implementation:
- `dev-tools\xstory\xstory-1-0.py` - ttk.Treeview version (working tree structure, but no per-cell coloring)
- `dev-tools\xstory\xstory-1-1.py` - tksheet version (has per-cell coloring, but arrow direction is wrong)

### Per-cell coloring use case
- **Status column**: Colored by status (green for implemented, blue for active, gray for concept, etc.)
- **ID column**: Black normally, gray for "faded ancestor" nodes
- **Title column**: Black normally, gray for "faded ancestor" nodes

This is why ttk.Treeview's row-level-only tags weren't sufficient - we need the Status cell colored differently than the ID/Title cells in the same row.

## Deliverable
A summary comparing viable alternatives with:
1. Per-cell styling capability (critical)
2. Treeview hierarchy support
3. Arrow/chevron behavior
4. Ease of migration from tkinter
5. Maintenance status
6. Any gotchas or limitations
