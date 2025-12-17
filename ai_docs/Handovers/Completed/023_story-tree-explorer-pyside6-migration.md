# Handover: Xstory - PySide6 Migration

## Task
Migrate Xstory from tkinter+tksheet to PySide6 (QTreeWidget) for native per-cell coloring, better performance, and standard arrow conventions.

## Status: PENDING

## Context

Current implementation (v1.1) uses tkinter+tksheet to display hierarchical story tree with 23-status rainbow color system. tksheet has wrong arrow direction (▼=collapsed, ►=expanded) which confuses users. PySide6's QTreeWidget provides native per-cell styling with correct Windows 11 arrow conventions.

## Important: License Notice

**Include in source file header:**
```python
"""
Xstory - A desktop app to explore story-tree databases.
Uses PySide6 (Qt for Python) under the LGPL v3 license.

PySide6 License: LGPL v3 (https://www.gnu.org/licenses/lgpl-3.0.html)
Qt for Python: https://www.qt.io/qt-for-python
"""
```

## Key Files

### Current Implementation
- **`dev-tools\xstory\xstory-1-1.py`** - Current tksheet version with rainbow colors (START HERE)
- **`dev-tools\xstory\requirements.txt`** - Add `PySide6` to dependencies

### Source Material
- **`ai_docs\Research\2025-12-14-Python-frameworks-research.md`** - Full framework comparison with PySide6 recommendation
- **`ai_docs\Handovers\022_story-tree-explorer-rainbow-colors.md`** - Current 23-status color palette

### Red Herrings (Don't Touch)
- `xstory.py` - ttk.Treeview version (old main file, lacks per-cell coloring)
- `xstory-1-0.py` - Backup of pre-tksheet version

## What Needs to Be Done

1. **Create new version**: `xstory-1-2.py` (PySide6 implementation)
2. **Preserve all features**:
   - 23-status rainbow color system (exact hex values from v1.1)
   - Status filter checkboxes with colored labels
   - Ancestor fading (gray italic for non-matching parent nodes)
   - Detail view with back/forward navigation
   - Right-click context menu (concept → approved/rejected/wishlist/refine)
   - Status change dialog with mandatory notes for 'refine'
   - Description panel on tree selection
   - Auto-detect database at `.claude\data\story-tree.db`
3. **PySide6 specifics**:
   - Use `QTreeWidget` (not QTreeView - simpler for our use case)
   - Per-cell colors: `item.setForeground(column, QBrush(QColor(hex_color)))`
   - Layout: `QVBoxLayout`/`QHBoxLayout` instead of pack/grid
   - Signals/slots instead of tkinter bind callbacks
4. **Update launcher**: Modify `explore-stories` to run new version

## Technical Mappings

### tkinter → PySide6 Widget Equivalents
```python
# Tree operations
tk: tree.insert(parent_iid, 'end', text=id, values=[...])
Qt: parent_item.addChild(QTreeWidgetItem([col0, col1, col2]))

# Per-cell coloring (THE KEY ADVANTAGE)
tk: sheet.highlight((row, col), fg=color)  # tksheet only
Qt: item.setForeground(col, QBrush(QColor(color)))

# Expand/collapse
tk: tree.item(iid, open=True)
Qt: tree.expandItem(item) / tree.collapseItem(item)

# Selection event
tk: tree.bind('<<TreeviewSelect>>', handler)
Qt: tree.itemSelectionChanged.connect(handler)

# Right-click menu
tk: tree.bind('<Button-3>', handler)
Qt: tree.setContextMenuPolicy(Qt.CustomContextMenu)
     tree.customContextMenuRequested.connect(handler)
```

### Layout Migration
```python
# tkinter pack/grid
frame.pack(fill=tk.BOTH, expand=True)
widget.grid(row=0, column=0, sticky='nsew')

# PySide6 layouts
layout = QVBoxLayout()
layout.addWidget(widget)
frame.setLayout(layout)
```

### Dialog Migration
```python
# tkinter Toplevel
dialog = tk.Toplevel(parent)
dialog.title("Title")
dialog.grab_set()
dialog.wait_window()

# PySide6 QDialog
dialog = QDialog(parent)
dialog.setWindowTitle("Title")
dialog.setModal(True)
result = dialog.exec()  # Blocks until closed
```

## 23-Status Rainbow Colors (EXACT)
```python
STATUS_COLORS = {
    # Red Zone (Can't/Won't)
    'infeasible': '#CC0000',   'rejected': '#CC3300',   'wishlist': '#CC6600',
    # Orange-Yellow Zone (Concept)
    'concept': '#CC9900',      'refine': '#CCCC00',     'approved': '#99CC00',
    'epic': '#66CC00',
    # Yellow Zone (Planning)
    'planned': '#33CC00',      'blocked': '#00CC00',    'pending': '#00CC33',
    # Yellow-Green Zone (Ready)
    'queued': '#00CC66',       'bugged': '#00CC99',     'paused': '#00CCCC',
    # Green Zone (Development)
    'active': '#0099CC',       'in-progress': '#0066CC',
    # Cyan-Blue Zone (Testing)
    'reviewing': '#0033CC',    'implemented': '#0000CC',
    # Blue Zone (Production)
    'ready': '#3300CC',        'polish': '#6600CC',     'released': '#9900CC',
    # Violet Zone (Post-Production)
    'legacy': '#CC00CC',       'deprecated': '#CC0099', 'archived': '#CC0066',
}
```

## Critical Implementation Notes

### Per-Cell Coloring in QTreeWidget
```python
tree = QTreeWidget()
tree.setHeaderLabels(["Status", "ID", "Title"])
tree.setColumnCount(3)

# Create item with values for all columns
item = QTreeWidgetItem(["concept", "1.2.3", "My Story Title"])

# Color each column independently (THIS IS WHY WE'RE MIGRATING)
item.setForeground(0, QBrush(QColor("#CC9900")))  # Status = orange
item.setForeground(1, QBrush(QColor("#000000")))  # ID = black
item.setForeground(2, QBrush(QColor("#000000")))  # Title = black

# For faded ancestors
item.setForeground(0, QBrush(QColor("#999999")))  # All columns gray
item.setForeground(1, QBrush(QColor("#999999")))
item.setForeground(2, QBrush(QColor("#999999")))
item.setFont(0, QFont("TkDefaultFont", 9, italic=True))
```

### Object References vs String IDs
- **tkinter**: Uses string item IDs (iid), stores node_id in text
- **PySide6**: Uses QTreeWidgetItem object references
- **Solution**: Store mapping `{node_id: QTreeWidgetItem}` for lookups

### Filter Implementation
Current tkinter approach detaches/reattaches items:
```python
tree.detach(item_id)  # Hide
tree.reattach(item_id, parent, 'end')  # Show
```

PySide6 approach - hide via `setHidden()`:
```python
item.setHidden(True)   # Hide
item.setHidden(False)  # Show
```

## Database Schema (Reference)
```sql
CREATE TABLE story_nodes (
    id TEXT PRIMARY KEY,
    title TEXT,
    status TEXT DEFAULT 'concept',
    capacity INTEGER,
    description TEXT,
    notes TEXT,
    project_path TEXT,
    created_at TEXT,
    updated_at TEXT,
    last_implemented TEXT
);

CREATE TABLE story_paths (
    ancestor_id TEXT,
    descendant_id TEXT,
    depth INTEGER,
    PRIMARY KEY (ancestor_id, descendant_id)
);
```

## Previous Implementation Attempts

### tksheet Migration (Handover 019)
- **Goal**: Per-cell coloring in tree view
- **Result**: Works but has inverted arrows (▼=collapsed is wrong)
- **Learning**: tksheet is powerful but has UX quirks

### ttk.Treeview Attempts (Handover 020)
- **Goal**: Stay with stdlib
- **Result**: Only row-level tags, cannot color individual cells
- **Learning**: Canvas overlay too fragile, tkinter limited for this use case

## PySide6 Research Highlights

Source: `ai_docs\Research\2025-12-14-Python-frameworks-research.md`

**Why PySide6 wins**:
- ✅ Native per-cell styling via `setForeground(column, brush)`
- ✅ Correct arrow conventions (►=collapsed, ▼=expanded)
- ✅ LGPL license (commercial use OK)
- ✅ Active maintenance by Qt Company
- ✅ Python 3.9-3.12 support
- ✅ ~15MB packaged size (vs 80-90MB for PyWebView)
- ✅ Better performance with thousands of nodes

**Rejected alternatives**:
- ttk.Treeview: No per-cell coloring
- CTkTable: No hierarchy support
- wxPython: Requires complex DataViewModel implementation
- DearPyGui: No native tree-table widget
- PyWebView+AG-Grid: Massive complexity, slow startup

**Installation**: `pip install PySide6`

**Key docs**:
- QTreeWidget: https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QTreeWidget.html
- QBrush/QColor: https://doc.qt.io/qtforpython-6/PySide6/QtGui/QBrush.html
- Signals/Slots: https://doc.qt.io/qtforpython-6/overviews/signalsandslots.html

## Feature Preservation Checklist

Must preserve from v1.1:
- [ ] 23-status rainbow color system (exact hex values)
- [ ] Status column colored per status
- [ ] ID and Title columns black (unless faded)
- [ ] Ancestor fading (gray+italic for filtered-out parents)
- [ ] Status filter checkboxes with colored labels
- [ ] All/None filter buttons
- [ ] Auto-expand all nodes on load
- [ ] Description panel showing selected node description
- [ ] Double-click opens detail view
- [ ] Detail view back/forward navigation
- [ ] Clickable parent/child links in detail view
- [ ] Right-click context menu (concept nodes only)
- [ ] Status change dialog with notes
- [ ] Mandatory notes for 'refine' status
- [ ] Timestamped notes appended to existing notes
- [ ] Auto-detect database at project root

## Success Criteria

1. Launch `explore-stories` → opens PySide6 window
2. Tree displays with correct arrows: ►=collapsed, ▼=expanded
3. Status column shows rainbow colors per status
4. Filter by status → ancestor nodes show faded
5. Double-click node → detail view with navigation
6. Right-click concept node → approve/reject/wishlist/refine options
7. Change status → dialog → updates database with timestamped note
8. All features from v1.1 work identically

## Next Steps After Migration

- Update `explore-stories` launcher to use v1.2
- Consider deprecating v1.1 (tksheet version)
- Update PyInstaller `build.py` to package PySide6 version
- Document PySide6 installation in README
- Consider this the new canonical version

## References

- PySide6 official tutorial: https://doc.qt.io/qtforpython-6/tutorials/index.html
- Qt Creator for UI design (optional): https://www.qt.io/product/development-tools
- PySide6 examples: https://github.com/qt/pyside-examples

## Estimated Effort

- Core QTreeWidget implementation: 2-3 hours
- Status filters + colored checkboxes: 1 hour
- Detail view with navigation: 2 hours
- Context menu + status dialog: 1 hour
- Testing + refinement: 1-2 hours

Total: **7-9 hours** for complete migration with feature parity
