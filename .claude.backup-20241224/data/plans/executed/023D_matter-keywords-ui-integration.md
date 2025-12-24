# 023D: Matter Keywords - UI Integration

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Story ID:** 8.1.1 | **Created:** 2025-12-22 | **Stage:** `planned`

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

---

**Goal:** Display AI-extracted keywords in the matter list UI as read-only tags.
**Approach:** Extend MatterDialog to show keywords column with tooltip.
**Tech Stack:** tkinter (existing UI framework)

---

## Story Context

**Title:** Matter Keywords/Tags for AI Matching
**Description:** Keywords displayed in matter list UI (read-only, AI-managed). Users see the keywords but cannot edit them - AI has complete control.

**Acceptance Criteria (this sub-plan):**
- [ ] Keywords column added to matter list treeview
- [ ] Keywords are clearly labeled as AI-generated
- [ ] Tooltip shows full keyword list with confidence scores

## Prerequisites

- [ ] venv activated: `venv\Scripts\activate`
- [ ] Sub-plan 023C complete (formatting functions exist)
- [ ] Baseline tests pass: `python -m pytest tests/test_matter_keywords.py -v`

## TDD Tasks

### Task 1: Add Keywords column to MatterDialog treeview (~5 min)

**Files:**
- Modify: `src/syncopaid/matter_client_dialog.py`
- Test: Manual verification (UI component)

**Context:** MatterDialog uses tkinter Treeview to display matters. We need to add a "Keywords (AI)" column showing the formatted keywords. The column header indicates these are AI-managed.

**Step 1:** Locate MatterDialog class and its treeview setup

First, read the current structure:
```bash
grep -n "columns=" src/syncopaid/matter_client_dialog.py
grep -n "Treeview" src/syncopaid/matter_client_dialog.py
```

**Step 2:** Modify MatterDialog._create_treeview to add Keywords column

Find the section where treeview columns are defined and add the Keywords column. The exact line numbers depend on current file structure, but the pattern is:

```python
# In MatterDialog._create_treeview method, update columns tuple:
# Before:
# columns = ("matter_number", "client", "description", "status")
# After:
columns = ("matter_number", "client", "description", "keywords", "status")

# Add column heading:
self.tree.heading("keywords", text="Keywords (AI)")
self.tree.column("keywords", width=200, minwidth=100)
```

**Step 3:** Modify MatterDialog._refresh_list to populate keywords

Find the method that populates the treeview (usually _refresh_list or similar) and update it to include keywords:

```python
# In the method that populates treeview, use get_matters_with_keywords:
# Before:
# matters = self.db.get_matters()
# After:
matters = get_matters_with_keywords(self.db)

# When inserting into treeview, include keywords_display:
# Before:
# values=(m['matter_number'], client_name, m['description'], m['status'])
# After:
values=(m['matter_number'], client_name, m['description'], m['keywords_display'], m['status'])
```

**Step 4 - Verify:** Run the dialog manually
```bash
python -c "
from syncopaid.database import Database
from syncopaid.config import get_config
from syncopaid.matter_client_dialog import MatterDialog
import tkinter as tk

config = get_config()
db = Database(config.db_path)

root = tk.Tk()
root.withdraw()  # Hide main window
dialog = MatterDialog(root, db)
print('MatterDialog opened - check for Keywords (AI) column')
root.mainloop()
"
```

**Step 5 - COMMIT:**
```bash
git add src/syncopaid/matter_client_dialog.py && git commit -m "feat: add Keywords (AI) column to matter list dialog"
```

---

### Task 2: Add keyword tooltip for full list (~4 min)

**Files:**
- Modify: `src/syncopaid/matter_client_dialog.py`
- Test: Manual verification (UI component)

**Context:** The Keywords column may show truncated keywords with "...". Adding a tooltip on hover shows the full list with confidence scores.

**Step 1:** Add tooltip helper class (if not exists)

```python
# src/syncopaid/matter_client_dialog.py (ADD near top, after format functions)

class ToolTip:
    """Simple tooltip for tkinter widgets."""

    def __init__(self, widget, text_func):
        """
        Create tooltip that shows text from text_func on hover.

        Args:
            widget: Widget to attach tooltip to
            text_func: Callable that returns tooltip text (receives event)
        """
        self.widget = widget
        self.text_func = text_func
        self.tip_window = None

        widget.bind('<Enter>', self._show)
        widget.bind('<Leave>', self._hide)
        widget.bind('<Motion>', self._update_position)

    def _show(self, event):
        text = self.text_func(event)
        if not text:
            return

        x = event.x_root + 10
        y = event.y_root + 10

        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")

        label = tk.Label(
            tw,
            text=text,
            background="#ffffe0",
            relief=tk.SOLID,
            borderwidth=1,
            font=("TkDefaultFont", 9)
        )
        label.pack()

    def _hide(self, event):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None

    def _update_position(self, event):
        if self.tip_window:
            self._hide(event)
            self._show(event)
```

**Step 2:** Add tooltip to treeview for Keywords column

In MatterDialog.__init__ or _create_treeview, after creating the tree:

```python
# Store matters data for tooltip lookup
self._matters_data = {}

def get_keyword_tooltip(event):
    """Get full keyword list for hovered row."""
    item = self.tree.identify_row(event.y)
    if not item:
        return None

    matter_id = self.tree.item(item, 'values')[0]  # Assuming first col is ID
    matter_data = self._matters_data.get(matter_id)
    if not matter_data or not matter_data.get('keywords_raw'):
        return None

    keywords = matter_data['keywords_raw']
    lines = [f"AI Keywords for {matter_id}:"]
    for kw in keywords:
        conf = kw.get('confidence', 0)
        lines.append(f"  • {kw['keyword']} ({conf:.0%})")

    return "\n".join(lines)

# Only add tooltip if tree exists
if hasattr(self, 'tree'):
    ToolTip(self.tree, get_keyword_tooltip)
```

**Step 3:** Update _refresh_list to store matter data for tooltips

```python
# In _refresh_list, after getting matters:
matters = get_matters_with_keywords(self.db)

# Store for tooltip lookup
self._matters_data = {m['matter_number']: m for m in matters}
```

**Step 4 - COMMIT:**
```bash
git add src/syncopaid/matter_client_dialog.py && git commit -m "feat: add tooltip showing full keyword list with confidence scores"
```

---

## Final Verification

Manual UI verification:
```bash
# Run the application and open Matters dialog
python -m syncopaid
# Click on Matters in system tray menu
# Verify:
# 1. Keywords (AI) column appears
# 2. Keywords are displayed for matters that have them
# 3. Hovering shows tooltip with full keyword list
```

## Rollback

If issues arise: `git log --oneline -5` to find commit, then `git revert <hash>`

## Notes

- Keywords column is read-only - no edit functionality
- Column header "Keywords (AI)" clearly indicates AI management
- Tooltip shows confidence scores to help users understand AI certainty
- Truncation at 5 keywords keeps the list readable
- Future enhancement: add keyword search/filter in matter list

## Dependencies

- Sub-plan 023C must be complete (formatting functions)

## Next Task

This is the final sub-plan for story 8.1.1. After completion, the story can be marked as implemented.
