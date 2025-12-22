# 024C: Timeline Canvas Widget

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Story ID:** 4.6 | **Created:** 2025-12-22 | **Stage:** `planned`
**Parent Plan:** 024_activity-timeline-view.md (Sub-plan C of 4)

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

---

**Goal:** Implement the tkinter Canvas-based timeline widget with zoom, pan, and block selection.
**Approach:** Create TimelineCanvas class extending tk.Canvas with rendering and interaction handling.
**Tech Stack:** tkinter (Canvas widget), Python threading

---

## Prerequisites

- [ ] venv activated: `venv\Scripts\activate`
- [ ] Sub-plan 024B completed (calculate_block_rect exists)
- [ ] Tests pass: `python -m pytest tests/test_timeline_view.py -v`

## Files Affected

| File | Change | Purpose |
|------|--------|---------|
| `src/syncopaid/timeline_view.py` | Modify | Add TimelineCanvas class |

---

## TDD Tasks

### Task 1: Create timeline canvas widget (~8 min)

**Files:**
- Modify: `src/syncopaid/timeline_view.py`
- Test: Manual verification (UI component)

**Context:** Now we create the actual tkinter Canvas-based timeline widget that renders blocks and handles interactions.

**Step 1:** Implement TimelineCanvas class
```python
# src/syncopaid/timeline_view.py (ADD to file)
import tkinter as tk
from tkinter import ttk


class TimelineCanvas(tk.Canvas):
    """
    Canvas widget that displays activity timeline with zoom/pan.

    Features:
    - Color-coded activity blocks
    - Zoom levels: day (1440 min), hour (60 min), 15-min
    - Click to show activity details
    - Distinct styling for idle periods
    """

    ZOOM_LEVELS = {
        'day': 24 * 60,    # 1440 minutes
        'hour': 60,         # 60 minutes
        'minute': 15,       # 15 minutes
    }

    def __init__(self, parent, blocks: List[TimelineBlock], date: str, **kwargs):
        """
        Initialize timeline canvas.

        Args:
            parent: Parent widget
            blocks: List of TimelineBlock to display
            date: Date string (YYYY-MM-DD) being displayed
            **kwargs: Additional Canvas options
        """
        # Default dimensions
        kwargs.setdefault('width', 1200)
        kwargs.setdefault('height', 80)
        kwargs.setdefault('bg', 'white')

        super().__init__(parent, **kwargs)

        self.blocks = blocks
        self.date = date
        self.zoom_level = 'day'
        self.view_start = datetime.fromisoformat(f"{date}T00:00:00")
        self.selected_block: Optional[TimelineBlock] = None
        self.on_block_click = None  # Callback for block clicks

        # Bind events
        self.bind('<Button-1>', self._on_click)
        self.bind('<Configure>', self._on_resize)

        # Initial render
        self._render()

    def set_zoom(self, level: str):
        """
        Set zoom level.

        Args:
            level: One of 'day', 'hour', 'minute'
        """
        if level in self.ZOOM_LEVELS:
            self.zoom_level = level
            self._render()

    def pan_to(self, time: datetime):
        """
        Pan view to center on a specific time.

        Args:
            time: Datetime to center view on
        """
        zoom_minutes = self.ZOOM_LEVELS[self.zoom_level]
        # Center the view on the given time
        offset = timedelta(minutes=zoom_minutes / 2)
        self.view_start = time - offset

        # Clamp to date boundaries
        day_start = datetime.fromisoformat(f"{self.date}T00:00:00")
        day_end = datetime.fromisoformat(f"{self.date}T23:59:59")

        if self.view_start < day_start:
            self.view_start = day_start
        max_start = day_end - timedelta(minutes=zoom_minutes)
        if self.view_start > max_start:
            self.view_start = max_start

        self._render()

    def _render(self):
        """Render all visible blocks on the canvas."""
        self.delete('all')

        width = self.winfo_width() or int(self['width'])
        height = self.winfo_height() or int(self['height'])
        zoom_minutes = self.ZOOM_LEVELS[self.zoom_level]

        # Draw time axis
        self._draw_time_axis(width, height, zoom_minutes)

        # Draw blocks
        for block in self.blocks:
            if not is_block_visible(block, self.view_start, zoom_minutes):
                continue

            x1, y1, x2, y2 = calculate_block_rect(
                block, width, height - 20,  # Reserve space for axis
                self.view_start, zoom_minutes
            )

            # Offset for axis
            y1 += 20
            y2 += 20

            # Skip tiny blocks (less than 2 pixels)
            if x2 - x1 < 2:
                continue

            # Draw block rectangle
            fill = block.color
            outline = '#333333' if block == self.selected_block else '#666666'
            width_line = 2 if block == self.selected_block else 1

            self.create_rectangle(
                x1, y1, x2, y2,
                fill=fill,
                outline=outline,
                width=width_line,
                tags=('block', f'block_{id(block)}')
            )

            # Draw app name if block is wide enough
            if x2 - x1 > 50:
                text = block.app or "Idle"
                if len(text) > 15:
                    text = text[:12] + "..."
                self.create_text(
                    (x1 + x2) / 2, (y1 + y2) / 2,
                    text=text,
                    fill='white' if not block.is_idle else '#666666',
                    font=('Segoe UI', 8),
                    tags='block_text'
                )

    def _draw_time_axis(self, width: int, height: int, zoom_minutes: int):
        """Draw time axis with tick marks."""
        # Draw axis line
        self.create_line(0, 18, width, 18, fill='#999999')

        # Determine tick interval based on zoom
        if zoom_minutes >= 24 * 60:
            tick_interval = 60  # Every hour
        elif zoom_minutes >= 60:
            tick_interval = 15  # Every 15 minutes
        else:
            tick_interval = 5   # Every 5 minutes

        pixels_per_minute = width / zoom_minutes

        # Draw ticks
        current = self.view_start
        end_time = self.view_start + timedelta(minutes=zoom_minutes)

        while current <= end_time:
            minutes_from_start = (current - self.view_start).total_seconds() / 60
            x = int(minutes_from_start * pixels_per_minute)

            # Draw tick
            self.create_line(x, 14, x, 18, fill='#666666')

            # Draw time label
            time_str = current.strftime('%H:%M')
            self.create_text(x, 8, text=time_str, font=('Segoe UI', 7), fill='#666666')

            current += timedelta(minutes=tick_interval)

    def _on_click(self, event):
        """Handle click on canvas to select block."""
        # Find clicked block
        items = self.find_overlapping(event.x - 2, event.y - 2, event.x + 2, event.y + 2)

        clicked_block = None
        for item in items:
            tags = self.gettags(item)
            for tag in tags:
                if tag.startswith('block_'):
                    # Find matching block by tag
                    for block in self.blocks:
                        if f'block_{id(block)}' == tag:
                            clicked_block = block
                            break

        self.selected_block = clicked_block
        self._render()

        if clicked_block and self.on_block_click:
            self.on_block_click(clicked_block)

    def _on_resize(self, event):
        """Handle canvas resize."""
        self._render()
```

**Step 2 - Verify:** Manual test
```bash
python -c "
import tkinter as tk
from datetime import datetime, timedelta
from syncopaid.timeline_view import TimelineBlock, TimelineCanvas

root = tk.Tk()
root.title('Timeline Test')

# Create test blocks
blocks = [
    TimelineBlock(
        start_time=datetime(2025, 12, 21, 9, 0, 0),
        end_time=datetime(2025, 12, 21, 10, 30, 0),
        app='WINWORD.EXE',
        title='Contract',
        is_idle=False
    ),
    TimelineBlock(
        start_time=datetime(2025, 12, 21, 10, 30, 0),
        end_time=datetime(2025, 12, 21, 10, 45, 0),
        app=None,
        title=None,
        is_idle=True
    ),
    TimelineBlock(
        start_time=datetime(2025, 12, 21, 10, 45, 0),
        end_time=datetime(2025, 12, 21, 12, 0, 0),
        app='chrome.exe',
        title='Research',
        is_idle=False
    ),
]

canvas = TimelineCanvas(root, blocks, '2025-12-21')
canvas.pack(fill=tk.BOTH, expand=True)

root.mainloop()
"
```

**Step 3 - COMMIT:**
```bash
git add src/syncopaid/timeline_view.py && git commit -m "feat: add TimelineCanvas widget with zoom and selection"
```

---

### Task 2: Create timeline window with controls (~8 min)

**Files:**
- Modify: `src/syncopaid/timeline_view.py`

**Context:** Create a complete timeline window with zoom buttons, date selector, app filter, and detail panel.

**Step 1:** Implement show_timeline_window function
```python
# src/syncopaid/timeline_view.py (ADD to file)
from syncopaid.database import format_duration
from syncopaid.main_ui_utilities import set_window_icon


def show_timeline_window(database, date: Optional[str] = None):
    """
    Show the activity timeline window.

    Args:
        database: Database instance
        date: Optional date to display (defaults to today)
    """
    import threading

    def run_window():
        # Default to today
        if date is None:
            display_date = datetime.now().strftime('%Y-%m-%d')
        else:
            display_date = date

        # Fetch blocks
        blocks = get_timeline_blocks(database, display_date)

        # Create window
        root = tk.Toplevel()
        root.title(f"Activity Timeline - {display_date}")
        root.geometry("1200x400")
        root.attributes('-topmost', True)
        set_window_icon(root)

        # Current state
        current_date = display_date
        current_blocks = blocks
        current_app_filter = None

        # Control frame at top
        control_frame = ttk.Frame(root, padding=10)
        control_frame.pack(fill=tk.X)

        # Date selector
        ttk.Label(control_frame, text="Date:").pack(side=tk.LEFT, padx=(0, 5))
        date_var = tk.StringVar(value=display_date)
        date_entry = ttk.Entry(control_frame, textvariable=date_var, width=12)
        date_entry.pack(side=tk.LEFT, padx=(0, 10))

        # Zoom buttons
        ttk.Label(control_frame, text="Zoom:").pack(side=tk.LEFT, padx=(10, 5))

        zoom_var = tk.StringVar(value='day')

        def set_zoom(level):
            zoom_var.set(level)
            canvas.set_zoom(level)

        ttk.Radiobutton(
            control_frame, text="Day", variable=zoom_var,
            value='day', command=lambda: set_zoom('day')
        ).pack(side=tk.LEFT)

        ttk.Radiobutton(
            control_frame, text="Hour", variable=zoom_var,
            value='hour', command=lambda: set_zoom('hour')
        ).pack(side=tk.LEFT)

        ttk.Radiobutton(
            control_frame, text="15 min", variable=zoom_var,
            value='minute', command=lambda: set_zoom('minute')
        ).pack(side=tk.LEFT)

        # App filter dropdown
        ttk.Label(control_frame, text="Filter:").pack(side=tk.LEFT, padx=(20, 5))
        unique_apps = ['All'] + get_unique_apps(blocks)
        app_var = tk.StringVar(value='All')
        app_dropdown = ttk.Combobox(
            control_frame, textvariable=app_var,
            values=unique_apps, state='readonly', width=20
        )
        app_dropdown.pack(side=tk.LEFT)

        def refresh_timeline():
            nonlocal current_date, current_blocks, current_app_filter
            current_date = date_var.get()

            # Apply filter
            app_filter = None if app_var.get() == 'All' else app_var.get()
            current_app_filter = app_filter

            current_blocks = get_timeline_blocks(database, current_date, app_filter=app_filter)
            canvas.blocks = current_blocks
            canvas.date = current_date
            canvas.view_start = datetime.fromisoformat(f"{current_date}T00:00:00")
            canvas._render()

            # Update filter dropdown
            all_blocks = get_timeline_blocks(database, current_date)
            unique_apps = ['All'] + get_unique_apps(all_blocks)
            app_dropdown['values'] = unique_apps

            # Update summary
            update_summary()

        ttk.Button(control_frame, text="Refresh", command=refresh_timeline).pack(side=tk.LEFT, padx=(10, 0))

        # Summary label
        summary_label = ttk.Label(control_frame, text="")
        summary_label.pack(side=tk.RIGHT)

        def update_summary():
            total_seconds = sum(b.duration_seconds for b in current_blocks if not b.is_idle)
            idle_seconds = sum(b.duration_seconds for b in current_blocks if b.is_idle)
            summary_label.config(
                text=f"Active: {format_duration(total_seconds)} | Idle: {format_duration(idle_seconds)}"
            )

        update_summary()

        # Timeline canvas
        canvas_frame = ttk.Frame(root)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10)

        canvas = TimelineCanvas(canvas_frame, blocks, display_date, height=120)
        canvas.pack(fill=tk.BOTH, expand=True)

        # Horizontal scrollbar for panning
        h_scroll = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL)
        h_scroll.pack(fill=tk.X)

        # Detail panel at bottom
        detail_frame = ttk.LabelFrame(root, text="Activity Details", padding=10)
        detail_frame.pack(fill=tk.X, padx=10, pady=10)

        detail_text = tk.Text(detail_frame, height=4, wrap=tk.WORD, state=tk.DISABLED)
        detail_text.pack(fill=tk.X)

        def show_block_details(block: TimelineBlock):
            """Show details for selected block."""
            detail_text.config(state=tk.NORMAL)
            detail_text.delete('1.0', tk.END)

            if block.is_idle:
                text = f"Idle Period\n"
            else:
                text = f"Application: {block.app}\n"

            text += f"Title: {block.title or 'N/A'}\n"
            text += f"Time: {block.start_time.strftime('%H:%M:%S')} - {block.end_time.strftime('%H:%M:%S')}\n"
            text += f"Duration: {format_duration(block.duration_seconds)}"

            detail_text.insert('1.0', text)
            detail_text.config(state=tk.DISABLED)

        canvas.on_block_click = show_block_details

        # Bind app filter change
        app_dropdown.bind('<<ComboboxSelected>>', lambda e: refresh_timeline())

        # Bind date entry change
        date_entry.bind('<Return>', lambda e: refresh_timeline())

        root.mainloop()

    # Run in thread to avoid blocking
    window_thread = threading.Thread(target=run_window, daemon=True)
    window_thread.start()
```

**Step 2 - Verify:** Manual test
```bash
python -c "
from syncopaid.database import Database
from syncopaid.config import get_config
from syncopaid.timeline_view import show_timeline_window
import time

config = get_config()
db = Database(config.db_path)

show_timeline_window(db)

# Keep main thread alive for window
time.sleep(60)
"
```

**Step 3 - COMMIT:**
```bash
git add src/syncopaid/timeline_view.py && git commit -m "feat: add timeline window with controls, filtering, and details panel"
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
    get_timeline_blocks, show_timeline_window
)
print('All timeline canvas imports successful')
"
```

## Rollback

If issues arise: `git log --oneline -5` to find commit, then `git revert <hash>`

## Notes

- This sub-plan creates the UI components (requires GUI verification)
- Next sub-plan (024D) will add image export and main UI integration
- Manual testing required due to tkinter Canvas
