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
