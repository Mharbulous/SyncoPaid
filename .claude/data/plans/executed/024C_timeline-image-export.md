# 024C: Timeline Image Export

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Story ID:** 4.6 | **Created:** 2025-12-22 | **Stage:** `planned`

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.
> **Sub-Plan:** Part C of 4 (Image Export)

---

**Goal:** Add ability to export timeline as PNG image for records.
**Approach:** Use PIL/Pillow to render timeline blocks to image file.
**Tech Stack:** PIL/Pillow
**Prerequisites:** Sub-plans 024A and 024B completed (TimelineCanvas and window exist)

---

## TDD Tasks

### Task 1: Add image export functionality (~5 min)

**Files:**
- Modify: `tests/test_timeline_view.py`
- Modify: `src/syncopaid/timeline_view.py`

**Context:** Users need to export the timeline as an image for records or sharing.

**Step 1 - RED:** Write failing test

Add to `tests/test_timeline_view.py`:

```python
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

Add to `src/syncopaid/timeline_view.py`:

```python
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

**Step 5 - COMMIT:**
```bash
git add src/syncopaid/timeline_view.py tests/test_timeline_view.py && git commit -m "feat: add timeline image export functionality"
```

---

### Task 2: Add export button to timeline window (~3 min)

**Files:**
- Modify: `src/syncopaid/timeline_view.py`

**Context:** Add Export Image button to the timeline window controls.

**Step 1:** Update show_timeline_window

In `show_timeline_window`, after the Refresh button definition, add:

```python
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

**Step 2 - Verify:** Manual test (requires display)

**Step 3 - COMMIT:**
```bash
git add src/syncopaid/timeline_view.py && git commit -m "feat: add export button to timeline window"
```

---

## Final Verification

```bash
# Run export test
pytest tests/test_timeline_view.py::test_export_timeline_image -v

# Verify imports work
python -c "
from syncopaid.timeline_view import export_timeline_image
print('export_timeline_image import successful')
"
```

## Notes

- Image export uses PIL/Pillow which is already a project dependency
- The export function can be tested automatically (no display needed)
- Only the export button integration requires manual testing
