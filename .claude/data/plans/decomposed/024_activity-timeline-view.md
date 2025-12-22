# 024: Activity Timeline View

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Story ID:** 4.6 | **Created:** 2025-12-21 | **Stage:** `planned`

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

---

**Goal:** Display a horizontal visual timeline of activity patterns with zoom controls, click-to-expand details, filtering, and image export.
**Approach:** Create new `timeline_view.py` module with tkinter Canvas-based timeline widget. Query events from database, render color-coded blocks, support zoom levels (day/hour/minute), and integrate with main UI.
**Tech Stack:** tkinter (Canvas widget), PIL/Pillow (image export), sqlite3

---

## Story Context

**Title:** Activity Timeline View

**Description:** As a lawyer reviewing my workday, I want a visual timeline showing my activity patterns, so that I can quickly understand how I spent my time.

**Acceptance Criteria:**
- [ ] Horizontal timeline with color-coded activity blocks
- [ ] Zoom controls for day/hour/minute granularity
- [ ] Click to expand activity details
- [ ] Filter by application or matter
- [ ] Show idle periods distinctly
- [ ] Export timeline as image for records

## Prerequisites

- [ ] venv activated: `venv\Scripts\activate`
- [ ] Baseline tests pass: `python -m pytest -v`
- [ ] Database module exists: `src/syncopaid/database.py`
- [ ] Main UI exists: `src/syncopaid/main_ui_windows.py`

## Files Affected

| File | Change | Purpose |
|------|--------|---------|
| `tests/test_timeline_view.py` | Create | Unit tests for timeline logic |
| `src/syncopaid/timeline_view.py` | Create | Timeline widget and rendering |
| `src/syncopaid/main_ui_windows.py:82-84` | Modify | Add Timeline menu item |

---

## TDD Tasks

### Task 1: Create timeline data model (~5 min)

**Files:**
- Create: `tests/test_timeline_view.py`
- Create: `src/syncopaid/timeline_view.py`

**Context:** The timeline needs a data structure to represent time blocks. Each block has start/end times, app name, title, duration, and whether it's idle.

**Step 1 - RED:** Write failing test
```python
# tests/test_timeline_view.py
import pytest
from datetime import datetime, timedelta


def test_timeline_block_creation():
    """Test creating a timeline block from event data."""
    from syncopaid.timeline_view import TimelineBlock

    block = TimelineBlock(
        start_time=datetime(2025, 12, 21, 9, 0, 0),
        end_time=datetime(2025, 12, 21, 9, 30, 0),
        app="WINWORD.EXE",
        title="Contract Draft - Word",
        is_idle=False
    )

    assert block.duration_seconds == 1800  # 30 minutes
    assert block.app == "WINWORD.EXE"
    assert block.is_idle == False


def test_timeline_block_from_event():
    """Test creating timeline block from database event dict."""
    from syncopaid.timeline_view import TimelineBlock

    event = {
        'timestamp': '2025-12-21T09:00:00',
        'end_time': '2025-12-21T09:30:00',
        'duration_seconds': 1800,
        'app': 'chrome.exe',
        'title': 'Legal Research - Chrome',
        'is_idle': False
    }

    block = TimelineBlock.from_event(event)

    assert block.app == 'chrome.exe'
    assert block.duration_seconds == 1800


def test_timeline_block_color_by_app():
    """Test that blocks get consistent colors by application."""
    from syncopaid.timeline_view import TimelineBlock, get_app_color

    # Same app should get same color
    color1 = get_app_color("WINWORD.EXE")
    color2 = get_app_color("WINWORD.EXE")
    assert color1 == color2

    # Idle should be distinct (gray)
    idle_color = get_app_color(None, is_idle=True)
    assert idle_color == "#D3D3D3"  # Light gray
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_timeline_view.py::test_timeline_block_creation -v
```
Expected: `FAILED` (module does not exist)

**Step 3 - GREEN:** Implement TimelineBlock
```python
# src/syncopaid/timeline_view.py
"""
Timeline view for visualizing activity patterns.

Provides a horizontal timeline with:
- Color-coded activity blocks by application
- Zoom controls (day/hour/minute granularity)
- Click-to-expand details
- Filter by application
- Export as image
"""

import hashlib
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict


# Color palette for applications (bright, distinct colors)
APP_COLORS = [
    "#4285F4",  # Blue (Google blue)
    "#34A853",  # Green
    "#EA4335",  # Red
    "#FBBC05",  # Yellow
    "#9C27B0",  # Purple
    "#FF5722",  # Deep orange
    "#00BCD4",  # Cyan
    "#795548",  # Brown
    "#607D8B",  # Blue gray
    "#E91E63",  # Pink
]

IDLE_COLOR = "#D3D3D3"  # Light gray for idle periods

# Cache app -> color mapping for consistency
_app_color_cache: Dict[str, str] = {}


def get_app_color(app: Optional[str], is_idle: bool = False) -> str:
    """
    Get consistent color for an application.

    Args:
        app: Application executable name (e.g., "WINWORD.EXE")
        is_idle: Whether this is an idle period

    Returns:
        Hex color string (e.g., "#4285F4")
    """
    if is_idle or app is None:
        return IDLE_COLOR

    if app not in _app_color_cache:
        # Hash app name to get consistent index
        hash_val = int(hashlib.md5(app.encode()).hexdigest(), 16)
        color_index = hash_val % len(APP_COLORS)
        _app_color_cache[app] = APP_COLORS[color_index]

    return _app_color_cache[app]


@dataclass
class TimelineBlock:
    """
    Represents a single activity block on the timeline.

    Attributes:
        start_time: Block start datetime
        end_time: Block end datetime
        app: Application executable name
        title: Window title
        is_idle: Whether this was an idle period
    """
    start_time: datetime
    end_time: datetime
    app: Optional[str]
    title: Optional[str]
    is_idle: bool = False

    @property
    def duration_seconds(self) -> float:
        """Calculate duration in seconds."""
        return (self.end_time - self.start_time).total_seconds()

    @property
    def color(self) -> str:
        """Get display color for this block."""
        return get_app_color(self.app, self.is_idle)

    @classmethod
    def from_event(cls, event: Dict) -> 'TimelineBlock':
        """
        Create TimelineBlock from database event dictionary.

        Args:
            event: Dict with timestamp, end_time, app, title, is_idle

        Returns:
            TimelineBlock instance
        """
        start = datetime.fromisoformat(event['timestamp'])

        # Use end_time if available, otherwise calculate from duration
        if event.get('end_time'):
            end = datetime.fromisoformat(event['end_time'])
        elif event.get('duration_seconds'):
            from datetime import timedelta
            end = start + timedelta(seconds=event['duration_seconds'])
        else:
            end = start

        return cls(
            start_time=start,
            end_time=end,
            app=event.get('app'),
            title=event.get('title'),
            is_idle=event.get('is_idle', False)
        )
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_timeline_view.py -v
```
Expected: `PASSED` for all 3 tests

**Step 5 - COMMIT:**
```bash
git add src/syncopaid/timeline_view.py tests/test_timeline_view.py && git commit -m "feat: add TimelineBlock data model for activity timeline"
```

---

### Task 2: Create timeline data aggregation (~5 min)

**Files:**
- Modify: `tests/test_timeline_view.py`
- Modify: `src/syncopaid/timeline_view.py`

**Context:** We need to convert database events into a list of TimelineBlocks for a given date range, with optional filtering by application.

**Step 1 - RED:** Write failing test
```python
# tests/test_timeline_view.py (ADD to file)
import tempfile
from pathlib import Path


def test_get_timeline_blocks_for_date():
    """Test fetching timeline blocks for a specific date."""
    from syncopaid.timeline_view import get_timeline_blocks
    from syncopaid.database import Database
    from syncopaid.tracker import ActivityEvent

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        # Insert test events
        events = [
            ActivityEvent(
                timestamp="2025-12-21T09:00:00",
                duration_seconds=1800,
                app="WINWORD.EXE",
                title="Contract.docx",
                is_idle=False
            ),
            ActivityEvent(
                timestamp="2025-12-21T09:30:00",
                duration_seconds=600,
                app=None,
                title=None,
                is_idle=True
            ),
            ActivityEvent(
                timestamp="2025-12-21T09:40:00",
                duration_seconds=1200,
                app="chrome.exe",
                title="CanLII Research",
                is_idle=False
            ),
        ]
        db.insert_events_batch(events)

        # Get blocks for the date
        blocks = get_timeline_blocks(db, "2025-12-21")

        assert len(blocks) == 3
        assert blocks[0].app == "WINWORD.EXE"
        assert blocks[1].is_idle == True
        assert blocks[2].app == "chrome.exe"


def test_get_timeline_blocks_filter_by_app():
    """Test filtering timeline blocks by application."""
    from syncopaid.timeline_view import get_timeline_blocks
    from syncopaid.database import Database
    from syncopaid.tracker import ActivityEvent

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        events = [
            ActivityEvent(
                timestamp="2025-12-21T09:00:00",
                duration_seconds=1800,
                app="WINWORD.EXE",
                title="Doc1",
                is_idle=False
            ),
            ActivityEvent(
                timestamp="2025-12-21T09:30:00",
                duration_seconds=1200,
                app="chrome.exe",
                title="Web",
                is_idle=False
            ),
        ]
        db.insert_events_batch(events)

        # Filter by Word only
        blocks = get_timeline_blocks(db, "2025-12-21", app_filter="WINWORD.EXE")

        assert len(blocks) == 1
        assert blocks[0].app == "WINWORD.EXE"
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_timeline_view.py::test_get_timeline_blocks_for_date -v
```
Expected: `FAILED` (function does not exist)

**Step 3 - GREEN:** Implement get_timeline_blocks
```python
# src/syncopaid/timeline_view.py (ADD to file)

def get_timeline_blocks(
    db,
    date: str,
    app_filter: Optional[str] = None,
    include_idle: bool = True
) -> List[TimelineBlock]:
    """
    Get timeline blocks for a specific date.

    Args:
        db: Database instance
        date: ISO date string (YYYY-MM-DD)
        app_filter: Optional app name to filter by
        include_idle: Whether to include idle periods

    Returns:
        List of TimelineBlock sorted by start time
    """
    events = db.get_events(
        start_date=date,
        end_date=date,
        include_idle=include_idle
    )

    blocks = []
    for event in events:
        # Apply app filter if specified
        if app_filter and event.get('app') != app_filter:
            continue

        block = TimelineBlock.from_event(event)
        blocks.append(block)

    # Sort by start time
    blocks.sort(key=lambda b: b.start_time)

    return blocks


def get_unique_apps(blocks: List[TimelineBlock]) -> List[str]:
    """
    Get list of unique application names from timeline blocks.

    Args:
        blocks: List of TimelineBlock instances

    Returns:
        Sorted list of unique app names (excluding None/idle)
    """
    apps = set()
    for block in blocks:
        if block.app and not block.is_idle:
            apps.add(block.app)
    return sorted(apps)
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_timeline_view.py::test_get_timeline_blocks_for_date tests/test_timeline_view.py::test_get_timeline_blocks_filter_by_app -v
```
Expected: `PASSED`

**Step 5 - COMMIT:**
```bash
git add src/syncopaid/timeline_view.py tests/test_timeline_view.py && git commit -m "feat: add timeline block aggregation with app filtering"
```

---

### Task 3: Create timeline rendering calculations (~5 min)

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
    from datetime import timedelta
    view_end = view_start + timedelta(minutes=zoom_minutes)

    # Block is visible if it overlaps the view window
    return block.start_time < view_end and block.end_time > view_start
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_timeline_view.py::test_calculate_block_position_day_view tests/test_timeline_view.py::test_calculate_block_position_hour_view -v
```
Expected: `PASSED`

**Step 5 - COMMIT:**
```bash
git add src/syncopaid/timeline_view.py tests/test_timeline_view.py && git commit -m "feat: add timeline block positioning calculations"
```

---

### Task 4: Create timeline canvas widget (~8 min)

**Files:**
- Modify: `src/syncopaid/timeline_view.py`
- Test: Manual verification (UI component)

**Context:** Now we create the actual tkinter Canvas-based timeline widget that renders blocks and handles interactions.

**Step 1:** Implement TimelineCanvas class
```python
# src/syncopaid/timeline_view.py (ADD to file)
import tkinter as tk
from tkinter import ttk
from datetime import timedelta


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

### Task 5: Create timeline window with controls (~8 min)

**Files:**
- Modify: `src/syncopaid/timeline_view.py`

**Context:** Create a complete timeline window with zoom buttons, date selector, app filter, and detail panel.

**Step 1:** Implement show_timeline_window function
```python
# src/syncopaid/timeline_view.py (ADD to file)
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

### Task 6: Add image export functionality (~5 min)

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

Update `show_timeline_window` to add export button:
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

### Task 7: Integrate with main UI menu (~3 min)

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

## Dependencies

- tkinter (standard library)
- PIL/Pillow (for image export)
- Database module with get_events() method
