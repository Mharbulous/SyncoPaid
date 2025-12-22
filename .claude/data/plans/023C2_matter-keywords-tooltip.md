# 023C2: Matter Keywords Tooltip

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Story ID:** 8.1.1 | **Created:** 2025-12-22 | **Stage:** `planned`

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

---

**Goal:** Add tooltip showing full keyword list with confidence scores when hovering over Keywords column.
**Approach:** Implement ToolTip helper class and attach to MatterDialog treeview.
**Tech Stack:** tkinter (existing UI framework)

---

## Story Context

**Title:** Matter Keywords/Tags for AI Matching
**Description:** Keywords displayed in matter list UI (read-only, AI-managed). Users see the keywords but cannot edit them - AI has complete control.

**Acceptance Criteria:**
- [ ] Keywords displayed in matter list UI (read-only, AI-managed)
- [ ] Keywords are clearly labeled as AI-generated

## Prerequisites

- [ ] venv activated: `venv\Scripts\activate`
- [ ] Sub-plan 023C1 complete (Keywords column added to treeview)
- [ ] Baseline tests pass: `python -m pytest tests/test_matter_keywords.py -v`

## TDD Tasks

### Task 1: Add keyword tooltip for full list (~4 min)

**Files:**
- Modify: `src/syncopaid/matter_client_dialog_matters.py`
- Test: `tests/test_matter_keywords.py`

**Context:** The Keywords column may show truncated keywords with "...". Adding a tooltip on hover shows the full list with confidence scores. The _matters_data dict stores the raw keyword data for tooltip lookup.

**Step 1 - RED:** Write failing test
```python
# tests/test_matter_keywords.py (ADD to existing file)

def test_tooltip_class_exists():
    """Test that ToolTip helper class exists for keyword tooltips."""
    from syncopaid.matter_client_dialog_matters import ToolTip

    assert ToolTip is not None, "ToolTip class should exist"
    # Verify it has the expected methods
    assert hasattr(ToolTip, '_show'), "ToolTip should have _show method"
    assert hasattr(ToolTip, '_hide'), "ToolTip should have _hide method"
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_matter_keywords.py::test_tooltip_class_exists -v
```
Expected output: `FAILED` (ToolTip class does not exist)

**Step 3 - GREEN:** Add ToolTip helper class

```python
# src/syncopaid/matter_client_dialog_matters.py (ADD near top, after imports)
import tkinter as tk

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

**Step 4:** Attach tooltip to MatterDialog treeview

In MatterDialog class, add to __init__ or after _create_treeview:

```python
# Store matters data for tooltip lookup
self._matters_data = {}

def get_keyword_tooltip(event):
    """Get full keyword list for hovered row."""
    item = self.tree.identify_row(event.y)
    if not item:
        return None

    # Get matter number from the row
    values = self.tree.item(item, 'values')
    if not values:
        return None

    matter_number = values[0]  # First column is matter_number
    matter_data = self._matters_data.get(matter_number)
    if not matter_data or not matter_data.get('keywords_raw'):
        return None

    keywords = matter_data['keywords_raw']
    lines = [f"AI Keywords for {matter_number}:"]
    for kw in keywords:
        conf = kw.get('confidence', 0)
        lines.append(f"  • {kw['keyword']} ({conf:.0%})")

    return "\n".join(lines)

# Only add tooltip if tree exists
if hasattr(self, 'tree'):
    ToolTip(self.tree, get_keyword_tooltip)
```

**Step 5:** Update _refresh_list to store matter data for tooltips

```python
# In _refresh_list, after getting matters:
matters = get_matters_with_keywords(self.db)

# Store for tooltip lookup
self._matters_data = {m['matter_number']: m for m in matters}
```

**Step 6 - Verify GREEN:**
```bash
pytest tests/test_matter_keywords.py::test_tooltip_class_exists -v
```
Expected output: `PASSED`

**Step 7 - COMMIT:**
```bash
git add src/syncopaid/matter_client_dialog_matters.py tests/test_matter_keywords.py && git commit -m "feat: add tooltip showing full keyword list with confidence scores"
```

---

## Final Verification

Run after task completes:
```bash
python -m pytest tests/test_matter_keywords.py -v
```

## Rollback

If issues arise: `git log --oneline -5` to find commit, then `git revert <hash>`

## Notes

- Tooltip shows confidence scores to help users understand AI certainty
- Uses _matters_data dict to store raw keyword data for lookup
- Tooltip appears on hover over any treeview row

## Next Task

This is the final sub-plan for story 8.1.1. After completion, the story can be marked as implemented.
