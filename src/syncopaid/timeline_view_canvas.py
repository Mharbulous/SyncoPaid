"""
Canvas widget for rendering interactive timeline view.

Provides TimelineCanvas class with zoom/pan functionality.
"""

import tkinter as tk
from datetime import datetime, timedelta
from typing import Optional, List
from syncopaid.timeline_view_models import TimelineBlock
from syncopaid.timeline_view_geometry import calculate_block_rect, is_block_visible
from syncopaid.timeline_view_styling import ZOOM_LEVELS


class TimelineCanvas(tk.Canvas):
    """
    Canvas widget that displays activity timeline with zoom/pan.

    Features:
    - Color-coded activity blocks
    - Zoom levels: day (1440 min), hour (60 min), 15-min
    - Click to show activity details
    - Distinct styling for idle periods
    """

    ZOOM_LEVELS = ZOOM_LEVELS

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
