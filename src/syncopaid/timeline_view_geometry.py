"""
Geometry and positioning calculations for timeline view.

Provides functions for calculating block positions and visibility.
"""

from datetime import datetime, timedelta
from typing import Tuple
from syncopaid.timeline_view_models import TimelineBlock


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
