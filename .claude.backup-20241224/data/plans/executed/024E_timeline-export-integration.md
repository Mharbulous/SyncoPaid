# 024E: Timeline Export and Menu Integration

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Story ID:** 4.6 | **Created:** 2025-12-22 | **Stage:** `planned`
**Parent Plan:** 024_activity-timeline-view.md

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

---

**Goal:** Add image export functionality and integrate timeline with main UI menu.
**Approach:** Implement export_timeline_image using PIL/Pillow, add export button to timeline window, and add menu item to main UI.
**Tech Stack:** PIL/Pillow (image export), tkinter

---

## Prerequisites

- [x] Tasks 1-2 completed (TimelineBlock, get_timeline_blocks)
- [x] Task 3 completed (calculate_block_rect, is_block_visible) - from 024C
- [x] Tasks 4-5 completed (TimelineCanvas, show_timeline_window) - from 024D
- [ ] venv activated: `venv\Scripts\activate`
- [ ] Baseline tests pass: `python -m pytest tests/test_timeline_view.py -v`

## Files Affected

| File | Change | Purpose |
|------|--------|---------|
| `tests/test_timeline_view.py` | Modify | Add export tests |
| `src/syncopaid/timeline_view.py` | Modify | Add export_timeline_image |
| `src/syncopaid/main_ui_windows.py` | Modify | Add Timeline menu item |

---

## TDD Tasks

### Task 1: Add image export functionality (~5 min)

**Files:**
- Modify: `tests/test_timeline_view.py`
- Modify: `src/syncopaid/timeline_view.py`

**Context:** Users need to export the timeline as an image for records or sharing.

**Step 1 - RED:** Write failing test
```python
# tests/test_timeline_view.py (ADD to file)
import os


def test_export_timeline_image():
    """Test exporting timeline to image file."""
    from syncopaid.timeline_view import export_timeline_image, TimelineBlock
    from datetime import datetime

    with tempfile.TemporaryDirectory() as tmpdir:
        blocks = [
            TimelineBlock(
                start_time=datetime(2025, 12, 21, 9, 0, 0),
                end_time=datetime(2025, 12, 21, 10, 0, 0),
                app="test.exe",
                title="Test",
                is_idle=False
            ),
        ]

        output_path = os.path.join(tmpdir, "timeline.png")

        result = export_timeline_image(
            blocks,
            date="2025-12-21",
            output_path=output_path,
            width=1200,
            height=100
        )

        assert result == output_path
        assert os.path.exists(output_path)

        # Verify it's a valid PNG
        with open(output_path, 'rb') as f:
            header = f.read(8)
            assert header[:4] == b'\x89PNG'
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_timeline_view.py::test_export_timeline_image -v
```
Expected: `FAILED` (function does not exist)

**Step 3 - GREEN:** Implement export
```python
# src/syncopaid/timeline_view.py (ADD to file)
from PIL import Image, ImageDraw, ImageFont


def export_timeline_image(
    blocks: List[TimelineBlock],
    date: str,
    output_path: str,
    width: int = 1200,
    height: int = 100,
    zoom_level: str = 'day'
) -> str:
    """
    Export timeline as PNG image.

    Args:
        blocks: List of TimelineBlock to render
        date: Date string (YYYY-MM-DD)
        output_path: Path to save PNG file
        width: Image width in pixels
        height: Image height in pixels
        zoom_level: Zoom level ('day', 'hour', 'minute')

    Returns:
        Path to saved image file
    """
    # Create image
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)

    # Calculate view parameters
    view_start = datetime.fromisoformat(f"{date}T00:00:00")
    zoom_minutes = TimelineCanvas.ZOOM_LEVELS.get(zoom_level, 24 * 60)

    # Draw time axis
    axis_height = 20
    draw.line([(0, axis_height), (width, axis_height)], fill='#999999')

    # Draw axis ticks and labels
    if zoom_minutes >= 24 * 60:
        tick_interval = 60
    elif zoom_minutes >= 60:
        tick_interval = 15
    else:
        tick_interval = 5

    pixels_per_minute = width / zoom_minutes

    try:
        font = ImageFont.truetype("arial.ttf", 10)
    except:
        font = ImageFont.load_default()

    current = view_start
    end_time = view_start + timedelta(minutes=zoom_minutes)

    while current <= end_time:
        minutes_from_start = (current - view_start).total_seconds() / 60
        x = int(minutes_from_start * pixels_per_minute)

        draw.line([(x, axis_height - 4), (x, axis_height)], fill='#666666')
        draw.text((x, 2), current.strftime('%H:%M'), fill='#666666', font=font)

        current += timedelta(minutes=tick_interval)

    # Draw blocks
    block_top = axis_height + 5
    block_bottom = height - 5

    for block in blocks:
        if not is_block_visible(block, view_start, zoom_minutes):
            continue

        x1, _, x2, _ = calculate_block_rect(
            block, width, height - axis_height,
            view_start, zoom_minutes
        )

        if x2 - x1 < 2:
            continue

        draw.rectangle(
            [(x1, block_top), (x2, block_bottom)],
            fill=block.color,
            outline='#666666'
        )

        # Draw app name if space
        if x2 - x1 > 50:
            text = block.app or "Idle"
            if len(text) > 15:
                text = text[:12] + "..."
            text_color = 'white' if not block.is_idle else '#666666'
            text_x = (x1 + x2) / 2
            text_y = (block_top + block_bottom) / 2 - 5
            draw.text((text_x, text_y), text, fill=text_color, font=font, anchor='mm')

    # Save image
    img.save(output_path, 'PNG')

    return output_path
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_timeline_view.py::test_export_timeline_image -v
```
Expected: `PASSED`

**Step 5:** Add export button to timeline window

Update `show_timeline_window` to add export button (in control_frame):
```python
# In show_timeline_window, add to control_frame:

def export_image():
    from tkinter import filedialog
    filepath = filedialog.asksaveasfilename(
        defaultextension='.png',
        filetypes=[('PNG Image', '*.png')],
        initialfilename=f'timeline_{current_date}.png'
    )
    if filepath:
        export_timeline_image(
            current_blocks,
            current_date,
            filepath,
            width=1200,
            height=100,
            zoom_level=zoom_var.get()
        )
        from tkinter import messagebox
        messagebox.showinfo("Export Complete", f"Timeline saved to:\n{filepath}")

ttk.Button(control_frame, text="Export Image", command=export_image).pack(side=tk.LEFT, padx=(10, 0))
```

**Step 6 - COMMIT:**
```bash
git add src/syncopaid/timeline_view.py tests/test_timeline_view.py && git commit -m "feat: add timeline image export functionality"
```

---

### Task 2: Integrate with main UI menu (~3 min)

**Files:**
- Modify: `src/syncopaid/main_ui_windows.py`

**Context:** Add "View Timeline" menu item to the main window View menu.

**Step 1:** Read current View menu implementation
```bash
grep -n "view_menu" src/syncopaid/main_ui_windows.py
```

**Step 2:** Add Timeline menu item after View Screenshots

In `show_main_window`, find the View menu section (around line 82-99) and add:

```python
# After view_screenshots command definition, add:

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

Run after all tasks complete:
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

- **Performance:** For days with 1000+ events, consider aggregating small blocks into larger ones
- **Color accessibility:** Current palette may need adjustment for colorblind users
- **Edge cases:**
  - Days with no activity (show empty timeline with message)
  - Events spanning midnight (split at day boundary)
  - Very short events (<1 min) may be invisible at day zoom
- **Future enhancements:**
  - Matter/client color coding (when categorization is available)
  - Multiple day view
  - Print functionality
  - Keyboard navigation
