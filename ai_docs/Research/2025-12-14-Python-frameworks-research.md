# Replacing tksheet: Per-cell styled treeview options for Python

**PySide6/PyQt6 emerges as the clear winner** for your Story Tree Explorer requirements. It's the only framework that natively combines hierarchical treeview functionality with true per-cell font color customization through a simple API: `QTreeWidgetItem.setForeground(column, brush)`. The standard right-arrow/down-arrow chevron conventions work correctly out of the box.

Other evaluated frameworks either lack treeview hierarchy (CTkTable), lack per-cell styling (ttk.Treeview, ttkbootstrap), require complex custom implementations (wxPython DataViewCtrl, DearPyGui), or add web technology overhead (PyWebView + AG-Grid). For your specific use case—different Status column colors while maintaining distinct ID/Title styling—PySide6 offers the most direct solution with the least friction.

## PySide6 directly solves the per-cell coloring requirement

The `QTreeWidgetItem.setForeground(column, brush)` method provides exactly what tksheet's `highlight((row, col), fg=color)` does, but with a cleaner API. Here's how your exact use case maps:

```python
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem
from PySide6.QtGui import QBrush, QColor

tree = QTreeWidget()
tree.setHeaderLabels(["Status", "ID", "Title"])

# Story node with per-cell colors (your exact requirement)
story = QTreeWidgetItem(["Active", "ST-042", "The Adventure Begins"])
story.setForeground(0, QBrush(QColor("#2ecc71")))  # Status = green (implemented)
story.setForeground(1, QBrush(QColor("#2c3e50")))  # ID = black
story.setForeground(2, QBrush(QColor("#2c3e50")))  # Title = black

# Faded ancestor node
faded = QTreeWidgetItem(["Concept", "ST-001", "Legacy Arc"])
faded.setForeground(0, QBrush(QColor("#95a5a6")))  # Status = gray
faded.setForeground(1, QBrush(QColor("#95a5a6")))  # ID = gray (faded)
faded.setForeground(2, QBrush(QColor("#95a5a6")))  # Title = gray (faded)

tree.addTopLevelItem(faded)
faded.addChild(story)  # Hierarchy preserved
```

Arrow behavior uses the standard **▶** (collapsed) / **▼** (expanded) convention on Windows 11—no hardcoded wrong direction like tksheet. The LGPL-licensed PySide6 works with Python 3.9–3.12, receives regular updates from The Qt Company, and handles thousands of nodes efficiently with `setUniformRowHeights(True)`.

## tkinter-based solutions cannot deliver per-cell styling

None of the tkinter ecosystem options support different colors for different columns in the same row:

| Solution | Per-Cell Color | Treeview | Status | Notes |
|----------|---------------|----------|--------|-------|
| **ttk.Treeview** | ❌ Row-only tags | ✅ Yes | Standard library | Canvas overlay workaround is fragile |
| **ttkwidgets** | ❌ No | ✅ Yes | Inactive 12+ months | Inherits ttk.Treeview limitations |
| **ttkbootstrap** | ❌ No | ✅ Yes | Active (v1.14.2) | Styling is row-level only |
| **CTkTable** | ✅ Yes | ❌ No | Active | Flat table, no hierarchy |
| **CTkTreeview** | ⚠️ Unclear | ✅ Yes | Community | Wraps ttk.Treeview |

**CTkTable** deserves mention—it implements cells as `CTkButton` widgets, enabling `table.edit(row=0, column=1, fg_color="green")` for true per-cell styling. However, it's a flat table with **no expand/collapse hierarchy**, disqualifying it for your tree explorer use case. You'd lose the parent-child relationships that define your data structure.

## wxPython works but requires complex model implementation

wxPython's `wx.dataview.DataViewCtrl` with a custom `DataViewModel` does support per-cell styling through the `GetAttr(item, col, attr)` callback:

```python
def GetAttr(self, item, col, attr):
    if col == 0:  # Status column
        attr.SetColour(wx.Colour(0, 128, 0))  # Green
        return True
    elif col == 1:  # ID column  
        attr.SetColour(wx.BLACK)
        return True
    return False
```

This approach requires implementing a full `PyDataViewModel` subclass with `GetValue()`, `GetParent()`, `GetChildren()`, and `IsContainer()` methods—significantly more boilerplate than PySide6's direct `setForeground()` call. The `wx.lib.agw.HyperTreeList` looks promising but only supports column-wide defaults or row-level `SetItemTextColour()`, not true per-cell differentiation.

**wxPython Phoenix 4.2.4** (October 2025) supports Python 3.8–3.14 and remains actively maintained. The learning curve is moderate, with sizer-based layouts replacing tkinter's pack/grid. If you need to stay closer to a "native" look without Qt's visual style, it's viable—just expect more implementation work.

## DearPyGui and Kivy lack native tree-table integration

Neither framework provides an out-of-the-box multi-column tree with per-cell styling:

**DearPyGui** has excellent tables (`dpg.table()`) and basic tree nodes (`dpg.tree_node()`), but combining them into a tree-grid is a pending feature request (GitHub #2379). Workarounds involving manual row visibility toggling are reported as slow with large datasets. Per-cell text coloring in tables works via `dpg.add_text(color=[255, 0, 0, 255])`, making it technically capable but requiring substantial custom implementation.

**Kivy's** TreeView is explicitly documented as "very basic" with single-column display only. Multi-column trees require building custom `TreeViewNode` subclasses with `BoxLayout` containers—essentially constructing your own widget from scratch. The mobile-first design also produces non-native aesthetics on Windows 11.

## Web-based hybrid offers maximum flexibility at higher complexity

**PyWebView + AG-Grid** provides enterprise-grade per-cell styling through native CSS:

```javascript
columnDefs: [
    { field: 'status', cellStyle: p => ({color: p.value === 'Active' ? 'green' : 'gray'}) },
    { field: 'id', cellStyle: p => ({color: p.data.isFaded ? '#999' : '#000'}) }
]
```

AG-Grid's `treeData` mode handles hierarchy, sorting, filtering, and lazy loading for massive datasets. The Python-JavaScript bridge via `js_api` enables clean data exchange without REST overhead. However, this approach adds significant complexity:

- Separate HTML/CSS/JS frontend codebase
- **80–90MB** packaged executable size (vs ~15MB for PySide6)
- Dual debugging environments required
- Slower startup compared to native widgets

**Critical warning**: **Eel was archived on June 22, 2025** and should not be used for new projects. PyWebView (BSD licensed, actively maintained) is the recommended alternative if you pursue this path.

## Migration path from tkinter to PySide6

The conceptual mapping from your current tksheet implementation is straightforward:

| tksheet Operation | PySide6 Equivalent |
|-------------------|-------------------|
| `sheet.insert(parent=parent_iid, iid=node_id, values=[...])` | `parent_item.addChild(QTreeWidgetItem(values))` |
| `sheet.highlight((row, col), fg=color)` | `item.setForeground(col, QBrush(QColor(color)))` |
| `sheet.expand(iid)` | `tree.expandItem(item)` |
| `sheet.collapse(iid)` | `tree.collapseItem(item)` |

Key differences to adapt: Qt uses object references rather than string iids, signals/slots replace callbacks, and layouts use `QVBoxLayout`/`QHBoxLayout` instead of pack/grid. Expect **2–3 weeks** to reach proficiency if you're starting fresh with Qt, though the per-cell styling implementation itself is simpler than your current approach.

## Recommendation matrix by priority

| Priority | Best Choice | Why |
|----------|-------------|-----|
| **Per-cell styling + tree hierarchy** | **PySide6** | Only native solution combining both |
| Minimal migration effort | ttk.Treeview + Canvas overlay | Stay in tkinter, but fragile |
| Maximum styling flexibility | PyWebView + AG-Grid | CSS handles everything, but complex |
| Native Windows look | wxPython DataViewCtrl | More setup, native appearance |

For your Story Tree Explorer displaying SQLite hierarchical data with **Status/ID/Title** columns requiring distinct per-cell colors, **PySide6 with QTreeWidget** is the recommended solution. It satisfies all must-have requirements (per-cell styling, hierarchy, proper chevrons, Python 3.11+, active maintenance) with the cleanest implementation path. The LGPL license permits commercial use without royalties, and the Qt ecosystem provides excellent documentation and community support for the inevitable edge cases you'll encounter.