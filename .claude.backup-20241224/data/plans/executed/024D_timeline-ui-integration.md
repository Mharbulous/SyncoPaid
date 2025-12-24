# 024D: Timeline UI Integration

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Story ID:** 4.6 | **Created:** 2025-12-22 | **Stage:** `planned`

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.
> **Sub-Plan:** Part D of 4 (UI Integration)

---

**Goal:** Integrate timeline view into main application menu.
**Approach:** Add "View Timeline" menu item to main window View menu.
**Tech Stack:** tkinter
**Prerequisites:** Sub-plans 024A, 024B, 024C completed (full timeline functionality exists)

---

## TDD Tasks

### Task 1: Integrate with main UI menu (~3 min)

**Files:**
- Modify: `src/syncopaid/main_ui_windows.py`

**Context:** Add "View Timeline" menu item to the main window View menu.

**Step 1:** Read current View menu implementation
```bash
grep -n "view_menu" src/syncopaid/main_ui_windows.py
```

**Step 2:** Add Timeline menu item

In `show_main_window`, find the View menu section and add the timeline command.

Look for existing View menu commands like "View Screenshots" and add after:

```python
def view_timeline():
    """Open timeline view window."""
    from syncopaid.timeline_view import show_timeline_window
    show_timeline_window(database)

view_menu.add_command(label="View Timeline", command=view_timeline)
```

**Step 3 - Verify:** Run application and check menu
```bash
python -m syncopaid
# Open main window, check View menu has "View Timeline" option
```

**Step 4 - COMMIT:**
```bash
git add src/syncopaid/main_ui_windows.py && git commit -m "feat: add View Timeline menu item to main window"
```

---

## Final Verification

Run after task complete:

```bash
# Run all timeline tests
python -m pytest tests/test_timeline_view.py -v

# Verify imports
python -c "
from syncopaid.timeline_view import (
    TimelineBlock, TimelineCanvas,
    get_timeline_blocks, show_timeline_window,
    export_timeline_image
)
print('All timeline imports successful')
"

# Manual UI test
python -m syncopaid
# 1. Open main window from system tray
# 2. View menu -> View Timeline
# 3. Verify timeline displays with zoom controls
# 4. Click blocks to see details
# 5. Use app filter dropdown
# 6. Export as image
```

## Rollback

If issues arise: `git log --oneline -5` to find commit, then `git revert <hash>`

## Notes

- This is the final sub-plan for story 4.6
- Completes all acceptance criteria:
  - [x] Horizontal timeline with color-coded activity blocks
  - [x] Zoom controls for day/hour/minute granularity
  - [x] Click to expand activity details
  - [x] Filter by application or matter
  - [x] Show idle periods distinctly
  - [x] Export timeline as image for records
