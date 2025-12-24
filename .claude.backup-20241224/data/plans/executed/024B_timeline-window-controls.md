# 024B: Timeline Window Controls

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Story ID:** 4.6 | **Created:** 2025-12-22 | **Stage:** `planned`

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.
> **Sub-Plan:** Part B of 4 (Window Controls)

---

**Goal:** Create complete timeline window with zoom buttons, date selector, app filter, and detail panel.
**Approach:** Implement show_timeline_window function with ttk controls wrapping TimelineCanvas.
**Tech Stack:** tkinter (ttk widgets)
**Prerequisites:** Sub-plan 024A completed (TimelineCanvas exists)

---

## TDD Tasks

### Task 1: Create timeline window with controls (~8 min)

**Files:**
- Modify: `src/syncopaid/timeline_view.py`
- Test: Manual verification (UI component)

**Context:** Create a complete timeline window with zoom buttons, date selector, app filter, and detail panel.

**Step 1:** Implement show_timeline_window function

Add to `src/syncopaid/timeline_view.py`:

```python
from tkinter import ttk
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

**Step 2 - Verify:** Manual test (requires display and database)
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

```bash
# Verify imports work
python -c "
from syncopaid.timeline_view import show_timeline_window
print('show_timeline_window import successful')
"
```

## Notes

- This is a GUI component that requires manual testing with a display and database
- CI environments may not be able to run the visual test
- The window is ready for image export integration in sub-plan 024C
