"""
Image export functionality for timeline view.

Provides functions to export timeline as PNG images.
"""

from datetime import datetime, timedelta
from typing import List
from PIL import Image, ImageDraw, ImageFont
from syncopaid.timeline_view_models import TimelineBlock
from syncopaid.timeline_view_geometry import calculate_block_rect, is_block_visible
from syncopaid.timeline_view_styling import ZOOM_LEVELS


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
    zoom_minutes = ZOOM_LEVELS.get(zoom_level, 24 * 60)

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
