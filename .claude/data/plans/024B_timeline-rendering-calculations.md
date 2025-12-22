# 024B: Timeline Rendering Calculations

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Story ID:** 4.6 | **Created:** 2025-12-22 | **Stage:** `planned`
**Parent Plan:** 024_activity-timeline-view.md (Sub-plan B of 4)

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

---

**Goal:** Implement pixel position calculations for rendering timeline blocks at different zoom levels.
**Approach:** Create pure functions for calculating block rectangles based on canvas dimensions and zoom.
**Tech Stack:** Python datetime arithmetic

---

## Prerequisites

- [ ] venv activated: `venv\Scripts\activate`
- [ ] Sub-plan 024A completed (TimelineBlock exists)
- [ ] Tests pass: `python -m pytest tests/test_timeline_view.py -v`

## Files Affected

| File | Change | Purpose |
|------|--------|---------|
| `tests/test_timeline_view.py` | Modify | Add tests for positioning calculations |
| `src/syncopaid/timeline_view.py` | Modify | Add calculate_block_rect and visibility functions |

---

## TDD Tasks

### Task 1: Create timeline rendering calculations (~5 min)

**Files:**
- Modify: `tests/test_timeline_view.py`
- Modify: `src/syncopaid/timeline_view.py`

**Context:** Before rendering, we need to calculate pixel positions for blocks based on canvas dimensions and zoom level.

**Step 1 - RED:** Write failing test
```python
# tests/test_timeline_view.py (ADD to file)

def test_calculate_block_position_day_view():
    """Test calculating pixel position for day view (24 hours)."""
    from syncopaid.timeline_view import TimelineBlock, calculate_block_rect
    from datetime import datetime

    block = TimelineBlock(
        start_time=datetime(2025, 12, 21, 12, 0, 0),  # Noon
        end_time=datetime(2025, 12, 21, 13, 0, 0),    # 1 PM
        app="test.exe",
        title="Test",
        is_idle=False
    )

    # Canvas 1440 pixels wide (1 pixel per minute for 24 hours)
    # At noon (720 minutes from midnight), block should start at x=720
    x1, y1, x2, y2 = calculate_block_rect(
        block,
        canvas_width=1440,
        canvas_height=60,
        day_start=datetime(2025, 12, 21, 0, 0, 0),
        zoom_minutes=24 * 60  # Full day view
    )

    assert x1 == 720  # Noon = 12 hours * 60 min = 720 pixels
    assert x2 == 780  # 1 PM = 13 hours * 60 min = 780 pixels
    assert y1 == 5    # Top padding
    assert y2 == 55   # Height minus padding


def test_calculate_block_position_hour_view():
    """Test calculating pixel position for 1-hour zoom."""
    from syncopaid.timeline_view import TimelineBlock, calculate_block_rect
    from datetime import datetime

    block = TimelineBlock(
        start_time=datetime(2025, 12, 21, 9, 15, 0),
        end_time=datetime(2025, 12, 21, 9, 30, 0),
        app="test.exe",
        title="Test",
        is_idle=False
    )

    # Canvas 600 pixels wide, showing 1 hour (60 minutes)
    # Start of view is 9:00, so 9:15 is 15 minutes in
    x1, y1, x2, y2 = calculate_block_rect(
        block,
        canvas_width=600,
        canvas_height=60,
        day_start=datetime(2025, 12, 21, 9, 0, 0),  # View starts at 9 AM
        zoom_minutes=60  # 1 hour view
    )

    # 15 minutes into 60-minute window on 600px canvas = 150px
    assert x1 == 150
    # 30 minutes into 60-minute window = 300px
    assert x2 == 300


def test_is_block_visible():
    """Test block visibility check."""
    from syncopaid.timeline_view import TimelineBlock, is_block_visible
    from datetime import datetime

    block = TimelineBlock(
        start_time=datetime(2025, 12, 21, 9, 0, 0),
        end_time=datetime(2025, 12, 21, 10, 0, 0),
        app="test.exe",
        title="Test",
        is_idle=False
    )

    # Block overlaps view window
    assert is_block_visible(block, datetime(2025, 12, 21, 8, 30, 0), 120) == True

    # Block before view window
    assert is_block_visible(block, datetime(2025, 12, 21, 10, 30, 0), 60) == False

    # Block after view window
    assert is_block_visible(block, datetime(2025, 12, 21, 7, 0, 0), 60) == False
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_timeline_view.py::test_calculate_block_position_day_view -v
```
Expected: `FAILED` (function does not exist)

**Step 3 - GREEN:** Implement calculation
```python
# src/syncopaid/timeline_view.py (ADD to file)
from typing import Tuple
from datetime import timedelta


def calculate_block_rect(
    block: TimelineBlock,
    canvas_width: int,
    canvas_height: int,
    day_start: datetime,
    zoom_minutes: int,
    padding: int = 5
) -> Tuple[int, int, int, int]:
    """
    Calculate rectangle coordinates for a timeline block.

    Args:
        block: TimelineBlock to position
        canvas_width: Width of canvas in pixels
        canvas_height: Height of canvas in pixels
        day_start: Start datetime of visible range
        zoom_minutes: Number of minutes visible in the canvas
        padding: Vertical padding for blocks

    Returns:
        Tuple of (x1, y1, x2, y2) for rectangle
    """
    # Calculate minutes from start of view
    block_start_minutes = (block.start_time - day_start).total_seconds() / 60
    block_end_minutes = (block.end_time - day_start).total_seconds() / 60

    # Clamp to visible range
    block_start_minutes = max(0, block_start_minutes)
    block_end_minutes = min(zoom_minutes, block_end_minutes)

    # Convert to pixels
    pixels_per_minute = canvas_width / zoom_minutes
    x1 = int(block_start_minutes * pixels_per_minute)
    x2 = int(block_end_minutes * pixels_per_minute)

    # Vertical position (full height minus padding)
    y1 = padding
    y2 = canvas_height - padding

    return (x1, y1, x2, y2)


def is_block_visible(
    block: TimelineBlock,
    view_start: datetime,
    zoom_minutes: int
) -> bool:
    """
    Check if a block is visible in the current view window.

    Args:
        block: TimelineBlock to check
        view_start: Start of visible time range
        zoom_minutes: Duration of visible range in minutes

    Returns:
        True if block overlaps with visible range
    """
    view_end = view_start + timedelta(minutes=zoom_minutes)

    # Block is visible if it overlaps the view window
    return block.start_time < view_end and block.end_time > view_start
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_timeline_view.py::test_calculate_block_position_day_view tests/test_timeline_view.py::test_calculate_block_position_hour_view tests/test_timeline_view.py::test_is_block_visible -v
```
Expected: `PASSED`

**Step 5 - COMMIT:**
```bash
git add src/syncopaid/timeline_view.py tests/test_timeline_view.py && git commit -m "feat: add timeline block positioning calculations"
```

---

## Final Verification

Run after all tasks complete:
```bash
# Run all timeline tests
python -m pytest tests/test_timeline_view.py -v

# Verify imports
python -c "
from syncopaid.timeline_view import (
    TimelineBlock,
    calculate_block_rect,
    is_block_visible,
    get_timeline_blocks
)
print('All timeline rendering imports successful')
"
```

## Rollback

If issues arise: `git log --oneline -5` to find commit, then `git revert <hash>`

## Notes

- This sub-plan adds pure calculation functions (no UI)
- Next sub-plan (024C) will implement the actual tkinter Canvas widget
- Sub-plan 024D will integrate with main UI and add image export
