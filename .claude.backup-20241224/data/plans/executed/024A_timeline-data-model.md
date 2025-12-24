# 024A: Timeline Data Model

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Story ID:** 4.6 | **Created:** 2025-12-22 | **Stage:** `planned`
**Parent Plan:** 024_activity-timeline-view.md (Sub-plan A of 4)

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

---

**Goal:** Create the TimelineBlock data model and color assignment for activity blocks.
**Approach:** Implement dataclass for timeline blocks with color-by-app functionality.
**Tech Stack:** Python dataclasses, hashlib for consistent color mapping

---

## Prerequisites

- [ ] venv activated: `venv\Scripts\activate`
- [ ] Baseline tests pass: `python -m pytest -v`
- [ ] Database module exists: `src/syncopaid/database.py`

## Files Affected

| File | Change | Purpose |
|------|--------|---------|
| `tests/test_timeline_view.py` | Create | Unit tests for timeline data model |
| `src/syncopaid/timeline_view.py` | Create | TimelineBlock dataclass and color functions |

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

## Final Verification

Run after all tasks complete:
```bash
# Run all timeline tests
python -m pytest tests/test_timeline_view.py -v

# Verify imports
python -c "
from syncopaid.timeline_view import (
    TimelineBlock,
    get_timeline_blocks,
    get_app_color,
    get_unique_apps
)
print('All timeline data model imports successful')
"
```

## Rollback

If issues arise: `git log --oneline -5` to find commit, then `git revert <hash>`

## Notes

- This sub-plan creates the foundational data model
- Next sub-plan (024B) will add rendering calculations
- Sub-plan 024C will implement the UI canvas widget
- Sub-plan 024D will integrate with main UI and add image export
